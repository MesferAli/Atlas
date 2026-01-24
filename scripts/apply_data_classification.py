import json
import os

SCHEMA_PATH = "/home/user/Atlas/data/oracle_fusion_schema.json"

def get_classification(table_name, columns):
    """
    تحديد تصنيف الجدول بناءً على السياسة الوطنية لتصنيف البيانات
    """
    table_str = table_name.upper()
    col_str = " ".join(columns).upper()

    # 1. المستوى السري (SECRET) - أضرار مالية أو اقتصادية
    # يشمل: الرواتب، الحسابات البنكية، أرقام الهويات (NID)
    if any(x in table_str for x in ['SALARY', 'PAY_', 'BANK', 'ELEMENT_ENTRY']) or \
       any(x in col_str for x in ['IBAN', 'NATIONAL_ID', 'AMOUNT', 'NET_PAY']):
        return "SECRET"

    # 2. المستوى المقيد (RESTRICTED) - بيانات شخصية (PDPL)
    # يشمل: معلومات الموظفين، العناوين، العقود، المشتريات التفصيلية
    if any(x in table_str for x in ['PERSON', 'EMPLOYEE', 'ASSIGNMENT', 'PO_HEADERS', 'CONTACT']) or \
       any(x in col_str for x in ['PHONE', 'EMAIL', 'ADDRESS', 'DOB', 'MARITAL_STATUS']):
        return "RESTRICTED"

    # 3. المستوى العام/الداخلي (INTERNAL/PUBLIC)
    # يشمل: الهياكل التنظيمية، الوظائف، المواقع
    return "INTERNAL"

def apply_classification():
    print("🔄 جاري تطبيق معايير 'سياسة تصنيف البيانات' الوطنية...")

    if not os.path.exists(SCHEMA_PATH):
        print("❌ الملف غير موجود!")
        return

    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)

    updated_count = 0
    stats = {"SECRET": 0, "RESTRICTED": 0, "INTERNAL": 0}

    for item in schema:
        # تحديد التصنيف بناءً على القواعد
        cls = get_classification(item.get('name', ''), item.get('columns', []))

        # إضافة التصنيف للميتاداتا
        if 'security_metadata' not in item:
            item['security_metadata'] = {}

        item['security_metadata']['classification'] = cls
        item['security_metadata']['compliance_standard'] = "NDMO_DATA_CLASS_POLICY_V1"

        stats[cls] += 1
        updated_count += 1

    # حفظ الملف المحدث
    with open(SCHEMA_PATH, 'w') as f:
        json.dump(schema, f, indent=2)

    print(f"✅ تم تحديث {updated_count} جدول.")
    print("📊 إحصائيات التصنيف:")
    print(f"   🔴 سري (SECRET): {stats['SECRET']} جدول (رواتب، بنوك)")
    print(f"   🟠 مقيد (RESTRICTED): {stats['RESTRICTED']} جدول (بيانات شخصية)")
    print(f"   🟢 عام/داخلي (INTERNAL): {stats['INTERNAL']} جدول (هياكل، وظائف)")

    # إعادة الحقن في Qdrant لتفعيل التغييرات
    print("\n🚀 ملاحظة: يجب تشغيل inject_moat.py لتنعكس التغييرات في قاعدة البيانات.")

if __name__ == "__main__":
    apply_classification()
