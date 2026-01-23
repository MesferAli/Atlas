import datetime

LOG_FILE_PATH = "logs/atlas_db.log"


def log_violation(query_hash, violation_type, details):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"{timestamp} - CRITICAL - Guardrail triggered: "
        f'{{"query_hash": "{query_hash}", "violation": "{violation_type}", '
        f'"details": "{details}"}}\n'
    )
    try:
        with open(LOG_FILE_PATH, "a") as f:
            f.write(log_entry)
    except Exception:
        pass


def execute_protected_query(sql_query: str):
    # 1. الحماية من التدمير
    forbidden = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
    if any(k in sql_query.upper() for k in forbidden):
        log_violation("auth_fail_001", "FORBIDDEN_KEYWORD", f"Blocked: {sql_query}")
        return {
            "status": "error",
            "error": "⛔ Security Alert: Destructive command detected!",
        }

    # 2. محاكاة البيانات الذكية (Smart Mock Data)
    # إذا كان الاستعلام يطلب الفواتير
    if "invoices" in sql_query.lower():
        return {
            "status": "success",
            "data": [
                {
                    "supplier": "TechSolutions Ltd",
                    "amount": 150000,
                    "status": "DUE",
                    "priority_score": 98.5,
                },
                {
                    "supplier": "Global Logistics",
                    "amount": 230000,
                    "status": "OVERDUE",
                    "priority_score": 95.0,
                },
                {
                    "supplier": "Office Supplies Co",
                    "amount": 105000,
                    "status": "DUE",
                    "priority_score": 88.2,
                },
            ],
        }

    # إذا كان الاستعلام يطلب الموظفين
    if "employees" in sql_query.lower():
        return {
            "status": "success",
            "data": [
                {
                    "name": "Ahmed Al-Farsi",
                    "role": "Senior Engineer",
                    "leave_balance": 75,
                    "risk": "High Burnout",
                },
                {
                    "name": "Sarah Miller",
                    "role": "Project Manager",
                    "leave_balance": 62,
                    "risk": "Moderate",
                },
            ],
        }

    # البيانات الافتراضية
    return {"status": "success", "data": [{"id": 1, "msg": "Safe Data Retrieved"}]}
