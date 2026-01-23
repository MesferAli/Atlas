import paramiko
import sys
import os
import time

# إعدادات السيرفر
SERVER_IP = "72.62.186.228"
USERNAME = "root"


def deploy(ssh_pass, db_name, db_user, db_pass):
    print(f"🚀 Connecting to {SERVER_IP}...")

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SERVER_IP, username=USERNAME, password=ssh_pass, timeout=30)

        def run_cmd(cmd, timeout=300, show=True):
            if show:
                print(f"⚙️  Running command...")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode()
            err = stderr.read().decode()
            if show and out:
                for line in out.strip().split("\n")[:10]:
                    print(f"   {line}")
            return out, err

        print("1️⃣ Updating Docker Configuration...")
        run_cmd(
            """cat > /root/atlas_erp/docker-compose.yml << 'EOF'
version: '3.8'
services:
  atlas-app:
    build: .
    container_name: atlas_erp
    network_mode: "host"
    volumes:
      - ./logs:/app/logs
    restart: always
EOF"""
        )

        print("2️⃣ Updating Requirements (adding PostgreSQL)...")
        run_cmd(
            """cat > /root/atlas_erp/requirements.txt << 'EOF'
fastapi
uvicorn
requests
psycopg2-binary
pydantic
jinja2
python-multipart
EOF"""
        )

        print("3️⃣ Injecting PDPL Logic with PostgreSQL Connector...")
        connector_code = f'''cat > /root/atlas_erp/db_guardrails/safe_db_connector.py << 'EOFCONNECTOR'
import psycopg2
import psycopg2.extras

# بيانات الاتصال (Localhost لأننا استخدمنا network_mode="host")
DB_CONFIG = {{
    "dbname": "{db_name}",
    "user": "{db_user}",
    "password": "{db_pass}",
    "host": "127.0.0.1",
    "port": "5432"
}}


def mask_pdpl_data(row):
    """تطبيق نظام حماية البيانات الشخصية (PDPL)"""
    masked = row.copy()

    # 1. السرية المالية (Financial Privacy)
    if "salary" in masked:
        masked["salary"] = "🔒 CONFIDENTIAL"

    # 2. تقليل البيانات (Data Minimization)
    if "email" in masked and masked["email"] and "@" in str(masked["email"]):
        try:
            u, d = str(masked["email"]).split("@")
            masked["email"] = f"{{u[:2]}}***@{{d}}"
        except Exception:
            pass

    # 3. حجب الهوية (Anonymization) - الجوال
    if "phone" in masked and masked["phone"]:
        p = str(masked["phone"])
        if len(p) >= 4:
            masked["phone"] = f"******{{p[-4:]}}"

    return masked


def init_tables():
    """إنشاء الجداول تلقائياً إذا لم تكن موجودة"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # التأكد من وجود الجداول
        cur.execute(
            """CREATE TABLE IF NOT EXISTS atlas_invoices
                       (id SERIAL PRIMARY KEY, supplier VARCHAR(100), amount DECIMAL,
                        status VARCHAR(20), risk_score DECIMAL)"""
        )

        cur.execute(
            """CREATE TABLE IF NOT EXISTS atlas_employees
                       (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100),
                        phone VARCHAR(20), salary DECIMAL, leave_balance INT, risk VARCHAR(20))"""
        )

        # إضافة بيانات تجريبية فقط إذا كان الجدول فارغاً
        cur.execute("SELECT count(*) FROM atlas_invoices")
        if cur.fetchone()[0] == 0:
            print("Seeding Initial Data...")
            cur.execute(
                "INSERT INTO atlas_invoices (supplier, amount, status, risk_score) VALUES "
                "('Saudi Electric', 120000, 'DUE', 10.0), ('Tech Solutions', 45000, 'PAID', 5.0)"
            )
            cur.execute(
                "INSERT INTO atlas_employees (name, email, phone, salary, leave_balance, risk) VALUES "
                "('Ali Al-Ghamdi', 'ali.ghamdi@company.sa', '0551234567', 18000, 45, 'Low')"
            )

        conn.commit()
        conn.close()
        print("Database tables initialized successfully!")
    except Exception as e:
        print(f"Database Init Warning: {{e}}")


# تشغيل التهيئة عند البدء
init_tables()


def execute_protected_query(sql_query: str):
    # الحماية من التدمير
    if any(k in sql_query.upper() for k in ["DROP", "DELETE", "TRUNCATE"]):
        return {{"status": "error", "error": "⛔ Security Alert: Action Blocked"}}

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql_query)
        rows = cur.fetchall()

        # تطبيق القناع (Masking) قبل الإرجاع
        cleaned_data = [mask_pdpl_data(dict(row)) for row in rows]
        conn.close()
        return {{"status": "success", "data": cleaned_data}}

    except Exception as e:
        return {{"status": "error", "error": f"DB Error: {{str(e)}}"}}
EOFCONNECTOR'''
        run_cmd(connector_code)

        print("4️⃣ Updating API Brain...")
        run_cmd(
            """cat > /root/atlas_erp/api/main.py << 'EOFAPI'
import os
import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_guardrails.safe_db_connector import execute_protected_query

app = FastAPI(title="Atlas ERP PDPL")


class SearchRequest(BaseModel):
    query_text: str


class SmartSearchEngine:
    def text_to_sql(self, text: str):
        q = text.lower()
        if "فواتير" in q:
            return "SELECT supplier, amount, status, risk_score FROM atlas_invoices ORDER BY risk_score DESC LIMIT 5"
        elif "موظفين" in q:
            return "SELECT name, email, phone, salary, leave_balance, risk FROM atlas_employees ORDER BY leave_balance DESC LIMIT 5"
        return "SELECT count(*) FROM atlas_invoices"


brain = SmartSearchEngine()


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("templates/dashboard.html", "r") as f:
        return f.read()


@app.post("/smart-search")
def intelligent_search(request: SearchRequest):
    sql = brain.text_to_sql(request.query_text)
    result = execute_protected_query(sql)
    if result["status"] == "success":
        return {
            "status": "success",
            "interpretation": "بيانات مشفرة (PDPL Compliant) ✅",
            "sql_generated": sql,
            "results": result.get("data", []),
        }
    else:
        return {"status": "error", "error": result.get("error", "Unknown error")}
EOFAPI"""
        )

        print("5️⃣ Rebuilding Docker Container (This takes ~60 seconds)...")
        run_cmd("cd /root/atlas_erp && docker compose down", show=False)
        out, err = run_cmd(
            "cd /root/atlas_erp && docker compose up -d --build", timeout=180
        )

        time.sleep(5)

        print("6️⃣ Checking Container Status...")
        out, _ = run_cmd("docker ps | grep atlas_erp")

        if "atlas_erp" in out:
            print("\n✅ SUCCESS! Atlas is now linked to your Server's PostgreSQL.")
            print("🛡️ PDPL Masking is ACTIVE.")
            print(f"👉 Check: http://{SERVER_IP}:8000/dashboard")
            print(
                "\n⚠️  Note: Since we use network_mode='host', the app runs on port 8000"
            )
        else:
            print("⚠️ Container may have issues. Checking logs...")
            run_cmd("docker logs atlas_erp 2>&1 | tail -20")

        client.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    # Get credentials from environment or command line
    ssh_pass = os.environ.get("SSH_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "postgres")
    db_user = os.environ.get("DB_USER", "postgres")
    db_pass = os.environ.get("DB_PASSWORD", "")

    if len(sys.argv) >= 5:
        ssh_pass = sys.argv[1]
        db_name = sys.argv[2]
        db_user = sys.argv[3]
        db_pass = sys.argv[4]

    if not ssh_pass or not db_pass:
        print("Usage: python deploy_postgres.py <ssh_password> <db_name> <db_user> <db_password>")
        print("   or: SSH_PASSWORD=x DB_NAME=x DB_USER=x DB_PASSWORD=x python deploy_postgres.py")
        sys.exit(1)

    deploy(ssh_pass, db_name, db_user, db_pass)
