import requests
import json
import time

# إعدادات الهدف (السيرفر الخاص بك)
SERVER_IP = "72.62.186.228"
API_URL = f"http://{SERVER_IP}/smart-search"

# تنسيق الألوان للمخرجات
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(test_name, status, detail=""):
    if status == "PASS":
        print(f"✅ {Colors.BOLD}{test_name:<30}{Colors.RESET} : {Colors.GREEN}PASSED{Colors.RESET} {detail}")
    else:
        print(f"❌ {Colors.BOLD}{test_name:<30}{Colors.RESET} : {Colors.RED}FAILED{Colors.RESET} {detail}")

def run_audit():
    print(f"\n{Colors.BOLD}🔒 Starting Atlas PDPL Compliance Audit{Colors.RESET}")
    print(f"Target: {Colors.YELLOW}{SERVER_IP}{Colors.RESET}\n")
    print("-" * 60)

    # 1. اختبار استرجاع بيانات الموظفين الحساسة
    payload = {"query_text": "عطني قائمة الموظفين ورواتبهم"}
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=5)
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            
            if len(results) > 0:
                employee = results[0]
                
                # أ) فحص حجب الراتب (Financial Privacy)
                salary_val = str(employee.get("salary", ""))
                if "PROTECTED" in salary_val or "CONFIDENTIAL" in salary_val:
                    print_status("Salary Masking", "PASS", f"-> {salary_val}")
                else:
                    print_status("Salary Masking", "FAIL", f"-> EXPOSED: {salary_val}")

                # ب) فحص تشفير الجوال (Identity Protection)
                phone_val = str(employee.get("phone", ""))
                if "***" in phone_val:
                    print_status("Phone Masking", "PASS", f"-> {phone_val}")
                else:
                    print_status("Phone Masking", "FAIL", f"-> EXPOSED: {phone_val}")

                # ج) فحص البريد الإلكتروني (Data Minimization)
                email_val = str(employee.get("email", ""))
                if "***" in email_val:
                    print_status("Email Masking", "PASS", f"-> {email_val}")
                else:
                    print_status("Email Masking", "FAIL", f"-> EXPOSED: {email_val}")
                    
                print(f"\n⚡ API Latency: {latency:.2f}ms (Connection Pooling Active)")
            else:
                print(f"{Colors.YELLOW}⚠️ Warning: No data returned to audit.{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ Server Error: {response.status_code}{Colors.RESET}")

    except Exception as e:
        print(f"{Colors.RED}❌ Connection Failed: {str(e)}{Colors.RESET}")

    print("-" * 60)
    print("📋 Audit Complete.\n")

if __name__ == "__main__":
    run_audit()
