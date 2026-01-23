import json
import random

# --- 1. قاعدة البيانات العربية المتخصصة ---
sectors_data = {
    "الموارد البشرية (HR)": {
        "ops": ["مسير الرواتب", "احتساب نهاية الخدمة", "الإجازات", "الانتادابات"],
        "scenarios": ["عدم نزول الراتب", "خطأ في رصيد الإجازات", "فشل اعتماد القرار", "تحديث بيانات التابعين"],
        "solutions": ["مراجعة شاشة التعريفات", "التحقق من التعيين", "تحديث المؤهل العلمي"]
    },
    "الإدارة المالية (Finance)": {
        "ops": ["إقفال الفترة المحاسبية", "التسويات البنكية", "أوامر الصرف", "ضريبة القيمة المضافة"],
        "scenarios": ["عدم تطابق الأرصدة", "تجاوز الميزانية (Funds Check)", "فشل الترحيل للأستاذ العام", "رفض الفاتورة من هيئة الزكاة"],
        "solutions": ["عمل مناقلة للميزانية", "مراجعة القيود المعلقة", "التأكد من رقم السجل الضريبي"]
    },
    "سلاسل الإمداد (SCM)": {
        "ops": ["أوامر الشراء (PO)", "الاستلام المخزني", "المنافسات", "الجرد السنوي"],
        "scenarios": ["إلغاء تعميد معلق", "فرق في الكميات المستلمة", "مشكلة في ربط منصة اعتماد", "الصنف غير معرف"],
        "solutions": ["تعديل الكمية في الطلب", "التواصل مع المورد", "فتح تذكرة دعم فني"]
    }
}

# أخطاء شائعة (تبقى بالانجليزي لأنها تظهر كذا في النظام، لكن الشرح عربي)
common_errors = [
    "FRM-40735: Trigger raised unhandled exception",
    "ORA-01403: No data found",
    "APP-SQLAP-10000: User holds no responsibility",
    "Budget Exceeded: Funds check failed",
    "IBAN Validation Failed"
]

data = []
print("جاري توليد 10,000 سجل متخصص باللغة العربية...")

# --- 2. محرك التوليد ---
for i in range(10000):
    sector_key = random.choice(list(sectors_data.keys()))
    details = sectors_data[sector_key]
    
    op = random.choice(details["ops"])
    scenario = random.choice(details["scenarios"])
    solution = random.choice(details["solutions"])
    error_code = random.choice(common_errors)
    
    # تنويع الأسلوب (رسمي vs استفسار مباشر)
    style = random.choice(["issue", "question", "error_report"])

    if style == "issue":
        # سيناريو مشكلة عامة
        user_msg = f"تواجهني مشكلة في {sector_key}، تحديداً عند {op}. النظام يقول {scenario}."
        assist_msg = f"في حالات {scenario} داخل {sector_key}، يجب عليك أولاً {solution}. تأكد أيضاً أن الفترة مفتوحة وأن الصلاحيات محدثة."
    
    elif style == "error_report":
        # سيناريو خطأ تقني محدد
        user_msg = f"ظهر لي الخطأ {error_code} وأنا أحاول أعمل {op}. وش الحل؟"
        assist_msg = f"الخطأ {error_code} يعني وجود خلل في البيانات المدخلة أو الصلاحيات. لحل مشكلة {op}، جرب {solution} وتحقق من الحقول الإلزامية."
        
    else:
        # سيناريو استفسار إجرائي
        user_msg = f"ما هي الطريقة الصحيحة لعمل {op} في نظام أوراكل السعودي؟"
        assist_msg = f"لإتمام {op} بنجاح: 1. ادخل النظام. 2. تأكد من {scenario}. 3. قم بـ {solution}. لا تنسَ التحقق من توافق العملية مع أنظمة الهيئة/الوزارة."

    # --- 3. الهيكلة النهائية (ShareGPT) ---
    entry = {
        "conversations": [
            {"from": "system", "value": "أنت خبير استشاري متخصص في حل مشاكل أنظمة Oracle ERP في المملكة العربية السعودية."},
            {"from": "human", "value": user_msg},
            {"from": "gpt", "value": assist_msg}
        ]
    }
    data.append(entry)

# --- 4. الحفظ (مع ضمان ظهور العربي بشكل صحيح) ---
with open("Oracle_Saudi_Specialized_10k.jsonl", "w", encoding='utf-8') as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("تم! الملف Oracle_Saudi_Specialized_10k.jsonl جاهز وتام التعريب.")
