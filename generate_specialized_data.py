import json
import random

# 1. إعداد البيانات المتخصصة
sectors_data = {
    "الموارد البشرية": {
        "ops": ["مسير الرواتب", "نهاية الخدمة", "الإجازات"],
        "scenarios": ["احتساب خاطئ للمستحقات", "تعليق في الـ Workflow", "تحديث بيانات تابعين"]
    },
    "المالية": {
        "ops": ["الإقفال الشهري", "التسويات البنكية", "أوامر الصرف"],
        "scenarios": ["عدم تطابق الأرصدة", "تجاوز الميزانية (Funds Check)", "فشل الترحيل لـ GL"]
    },
    "سلاسل الإمداد": {
        "ops": ["أوامر الشراء PO", "الاستلام المخزني", "الجرد"],
        "scenarios": ["إلغاء سطر معلق", "اختلاف الكمية المستلمة", "فشل حجز الكميات"]
    }
}
common_errors = ["FRM-40735: Trigger Exception", "ORA-01403: No Data Found", "APP-SQLAP-10000", "Account Generator Failed"]
output_file = "Oracle_Saudi_Specialized_10k.jsonl"

data = []
print("جاري توليد 10,000 سجل تدريبي متخصص...")

for i in range(10000):
    sector = random.choice(list(sectors_data.keys()))
    op = random.choice(sectors_data[sector]["ops"])
    scenario = random.choice(sectors_data[sector]["scenarios"])
    
    # 60% سيناريوهات أخطاء (لزيادة الذكاء في حل المشاكل)
    if random.random() < 0.6:
        err = random.choice(common_errors)
        user_msg = f"واجهت الخطأ {err} أثناء تنفيذ {op} في نظام {sector}. الحالة: {scenario}."
        assist_msg = f"الخطأ {err} في سياق {sector} وتحديداً عند {op} يشير غالباً لتعارض في البيانات. لحل مشكلة {scenario}، تحقق أولاً من المدخلات الإلزامية وصلاحية الفترة المالية."
    else:
        user_msg = f"ما هو الإجراء الصحيح لعمل {op} في {sector}؟"
        assist_msg = f"لإتمام {op} بنجاح، انتقل للشاشة المخصصة، أدخل البيانات المطلوبة، وتأكد من اكتمال الاعتمادات. النظام سيقوم بمعالجة {scenario} آلياً."

    # صيغة ShareGPT
    entry = {
        "conversations": [
            {"from": "system", "value": "أنت خبير تقني في أنظمة Oracle ERP الموطنة للسعودية."},
            {"from": "human", "value": user_msg},
            {"from": "gpt", "value": assist_msg}
        ]
    }
    data.append(entry)

with open(output_file, 'w', encoding='utf-8') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"تم بنجاح! الملف {output_file} جاهز للتدريب.")
