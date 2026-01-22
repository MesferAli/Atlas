import requests

URL = "http://127.0.0.1:8000/smart-search"


def test_query(prompt, scenario_name):
    print(f"\n🧪 Testing Scenario: {scenario_name}")
    print(f"   Query: '{prompt}'")
    try:
        res = requests.post(URL, json={"query_text": prompt})
        if res.status_code == 200:
            data = res.json()
            print("   ✅ SUCCESS!")
            print(f"   🧠 AI Interpretation: {data['interpretation']}")
            print(f"   🔢 Results Count: {len(data['results'])}")
            print("   📊 Top Result (Highest Rank):")
            print(f"      {data['results'][0]}")
        else:
            print(f"   ❌ FAILED: {res.text}")
    except Exception as e:
        print(f"   ⚠️ Connection Error: Is the server running? ({e})")


print("=" * 50)
print("🚀 ATLAS AI & RANKING ENGINE TEST")
print("=" * 50)

# Scenario 1: High Value Invoices (يجب أن يعيد الفواتير مرتبة حسب الأهمية)
test_query("عطني فواتير موردين اعلى من 100 الف", "High Value Invoices")

# Scenario 2: Employee Leaves (يجب أن يعيد الموظفين المتأثرين)
test_query("عطني قايمة لموظفين إجازاتهم اعلى من 60 يوم", "Employee Burnout Risk")
