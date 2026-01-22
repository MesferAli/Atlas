import paramiko
import time
import getpass

# إعدادات السيرفر
SERVER_IP = "72.62.186.228"
USERNAME = "root"

# الأوامر التي سيتم تنفيذها في السيرفر
DEPLOYMENT_SCRIPT = """
# 1. إعداد البيئة
apt-get update
if ! command -v docker &> /dev/null; then
    apt-get install -y docker.io docker-compose
fi

mkdir -p ~/atlas_erp/{api,templates,db_guardrails,logs,tools}
cd ~/atlas_erp

# 2. إنشاء الملفات
echo "creating requirements.txt..."
cat <<EOF > requirements.txt
fastapi
uvicorn
requests
cx_Oracle
pydantic
jinja2
python-multipart
EOF

echo "creating Dockerfile..."
cat <<EOF > Dockerfile
FROM python:3.9-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y libaio1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p logs
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "creating docker-compose.yml..."
cat <<EOF > docker-compose.yml
version: '3.8'
services:
  atlas-app:
    build: .
    container_name: atlas_erp
    ports:
      - "80:8000"
    volumes:
      - ./logs:/app/logs
    restart: always
EOF

# (سنقوم بنسخ ملفات البايثون والـ HTML لاحقاً عبر SFTP لضمان الدقة)

# 3. التشغيل
echo "🚀 Starting Docker..."
docker-compose down
docker-compose up -d --build
"""


def deploy():
    print(f"🚀 Connecting to {SERVER_IP}...")
    password = getpass.getpass(f"Enter password for {USERNAME}@{SERVER_IP}: ")

    try:
        # 1. إنشاء الاتصال
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(SERVER_IP, username=USERNAME, password=password)

        print("✅ Connected! Uploading project files...")

        # 2. رفع الملفات الحالية من جهازك إلى السيرفر (SFTP)
        sftp = client.open_sftp()

        # دالة مساعدة لرفع الملفات
        def upload_file(local_path, remote_path):
            try:
                sftp.put(local_path, remote_path)
                print(f"   📄 Uploaded: {local_path}")
            except Exception as e:
                print(f"   ⚠️ Skipping {local_path} (Not found)")

        # التأكد من وجود المجلدات هناك
        client.exec_command(
            "mkdir -p ~/atlas_erp/api ~/atlas_erp/templates ~/atlas_erp/db_guardrails"
        )
        time.sleep(1)

        # رفع الملفات المهمة
        upload_file("api/main.py", "/root/atlas_erp/api/main.py")
        upload_file(
            "db_guardrails/safe_db_connector.py",
            "/root/atlas_erp/db_guardrails/safe_db_connector.py",
        )
        upload_file("templates/dashboard.html", "/root/atlas_erp/templates/dashboard.html")
        upload_file("templates/index.html", "/root/atlas_erp/templates/index.html")
        upload_file("templates/onboarding.html", "/root/atlas_erp/templates/onboarding.html")

        sftp.close()

        # 3. تنفيذ أوامر Docker
        print("⚙️  Running deployment script on server (this takes ~2 mins)...")
        stdin, stdout, stderr = client.exec_command(DEPLOYMENT_SCRIPT)

        # عرض المخرجات مباشرة
        for line in stdout:
            print("   [Server] " + line.strip())

        print("\n✅ Deployment Finished Successfully!")
        print(f"🌍 Your App is Live: http://{SERVER_IP}")

        client.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    deploy()
