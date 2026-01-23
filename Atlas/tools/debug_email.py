import smtplib
from email.message import EmailMessage
import sys

# --- البيانات مدمجة مباشرة لتجاوز مشاكل البيئة ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "Mesfer@xcyrcle.co"
SENDER_PASSWORD = "ennb ivmp liuf ktpy"  # كلمة مرور التطبيق من الصورة السابقة
RECEIVER_EMAIL = "info@xcyrcle.co"

print(f"(1/4) Connecting to server {SMTP_SERVER}...")

try:
    # 1. إعداد الرسالة
    msg = EmailMessage()
    msg.set_content("نجح الاتصال! هذا بريد اختبار من نظام Atlas للتحقق من العمليات.")
    msg['Subject'] = "✅ Atlas Project: Live Connection Test"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # 2. بدء الاتصال
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    
    # 3. تشفير الاتصال
    if server.starttls()[0] != 220:
        print("ERROR: Failed to enable TLS.")
        sys.exit(1)
    print("(2/4) TLS secured.")

    # 4. تسجيل الدخول
    print(f"(3/4) Logging in as {SENDER_EMAIL}...")
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    print("Password accepted.")

    # 5. الإرسال
    print(f"(4/4) Sending message to {RECEIVER_EMAIL}...")
    server.send_message(msg)
    server.quit()
    
    print("\nOperation completed successfully. Check the inbox now.")

except smtplib.SMTPAuthenticationError:
    print("\nAuthentication error. Ensure the App Password is valid.")
except Exception as e:
    print(f"\nUnexpected error: {e}")