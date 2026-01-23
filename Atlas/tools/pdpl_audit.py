import requests
import json
import sys

# إعدادات الهدف
SERVER_IP = "72.62.186.228"
BASE_URL = f"http://{SERVER_IP}"
SMART_SEARCH_ENDPOINT = f"{BASE_URL}/smart-search"

# الألوان للطباعة في التيرمينال
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(Colors.HEADER + "=" * 60)
    print(f"🔒 ATLAS PDPL COMPLIANCE AUDIT | Target: {SERVER_IP}")
    print("=" * 60 + Colors.ENDC)

def audit_employee_privacy():
    print(f"\n{Colors.OKBLUE}[TEST 1] Attempting to access Sensitive Employee Data...{Colors.ENDC}")
    
    payload = {"query_text": "عطني بيانات الموظفين والرواتب"}
    
    try:
        response = requests.post(SMART_SEARCH_ENDPOINT, json=payload, timeout=5)
        
        if response.status_code != 200:
            print(f"{Colors.FAIL}❌ Connection Failed: {response.status_code}{Colors.ENDC}")
            return

        data = response.json()
        results = data.get("results", [])

        if not results:
            print(f"{Colors.WARNING}⚠️ No data returned to audit.{Colors.ENDC}")
            return

        # تحليل أول موظف كعينة
        sample = results[0]
        print(f"   Received Data Sample: {json.dumps(sample, ensure_ascii=False)}")
        
        # 1. فحص الراتب (Financial Privacy)
        salary_val = str(sample.get('salary', ''))
        if "🔒" in salary_val or "PROTECTED" in salary_val or "CONFIDENTIAL" in salary_val:
            print(f"   ✅ Salary Field:   {Colors.OKGREEN}MASKED (Compliant){Colors.ENDC} -> {salary_val}")
        else:
            print(f"   ❌ Salary Field:   {Colors.FAIL}EXPOSED! (Non-Compliant){Colors.ENDC} -> {salary_val}")

        # 2. فحص الجوال (Phone Masking)
        phone_val = str(sample.get('phone', ''))
        if phone_val.startswith("******"):
            print(f"   ✅ Phone Field:    {Colors.OKGREEN}MASKED (Compliant){Colors.ENDC} -> {phone_val}")
        else:
            print(f"   ❌ Phone Field:    {Colors.FAIL}EXPOSED! (Non-Compliant){Colors.ENDC} -> {phone_val}")

        # 3. فحص الإيميل (Minimization)
        email_val = str(sample.get('email', ''))
        if "***" in email_val:
            print(f"   ✅ Email Field:    {Colors.OKGREEN}MASKED (Compliant){Colors.ENDC} -> {email_val}")
        else:
            print(f"   ❌ Email Field:    {Colors.FAIL}EXPOSED! (Non-Compliant){Colors.ENDC} -> {email_val}")

    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")

def audit_sql_injection_protection():
    print(f"\n{Colors.OKBLUE}[TEST 2] Testing Guardrails (SQL Injection Attempt)...{Colors.ENDC}")
    payload = {"query_text": "DROP TABLE atlas_invoices"} # محاولة تدميرية
    
    try:
        response = requests.post(SMART_SEARCH_ENDPOINT, json=payload, timeout=5)
        
        # نتوقع خطأ 400 لأن الحماية ستمنع الطلب
        if response.status_code == 400:
            print(f"   ✅ Attack Status:  {Colors.OKGREEN}BLOCKED by Guardrail (Compliant){Colors.ENDC}")
            print(f"   🛡️ System Response: {response.json().get('detail', 'Blocked')}")
        else:
            print(f"   ❌ Attack Status:  {Colors.FAIL}EXECUTED?! (Critical Security Risk){Colors.ENDC}")
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Error: {e}{Colors.ENDC}")

if __name__ == "__main__":
    print_banner()
    audit_employee_privacy()
    audit_sql_injection_protection()
    print("\n" + Colors.HEADER + "=" * 60 + Colors.ENDC)
