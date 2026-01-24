import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_guardrails.safe_db_connector import execute_protected_query

app = FastAPI(title="Atlas DB Guardrails API")


class QueryRequest(BaseModel):
    sql_query: str


class SearchRequest(BaseModel):
    query_text: str


# === الذكاء الاصطناعي (Atlas Brain) ===
class SmartSearchEngine:
    def text_to_sql(self, natural_query: str):
        q = natural_query.lower()
        # محاكاة فهم اللغة (NLP Mocking)
        if "فواتير" in q and "100" in q:
            # تطبيق منطق الترتيب (Ranking Logic) المشابه لمنصة X
            return """
            SELECT supplier, amount, status,
                   (amount * 0.001 + risk_score * 10) as priority_score
            FROM invoices
            WHERE amount > 100000
            ORDER BY priority_score DESC
            """
        elif "موظفين" in q or "إجازات" in q:
            return (
                "SELECT name, role, leave_balance FROM employees "
                "WHERE leave_balance > 60 ORDER BY leave_balance DESC"
            )
        else:
            return "SELECT * FROM general_logs FETCH FIRST 5 ROWS ONLY"


brain = SmartSearchEngine()


# --- Endpoints ---


@app.get("/", response_class=HTMLResponse)
def home():
    with open("templates/index.html", "r") as f:
        return f.read()


@app.get("/onboarding", response_class=HTMLResponse)
def onboarding():
    with open("templates/onboarding.html", "r") as f:
        return f.read()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("templates/dashboard.html", "r") as f:
        return f.read()


@app.post("/execute")
def run_query(request: QueryRequest):
    result = execute_protected_query(request.sql_query)
    if result["status"] == "success":
        return {"status": "success", "data": result["data"]}
    else:
        raise HTTPException(status_code=400, detail=result["error"])


@app.post("/smart-search")
def intelligent_search(request: SearchRequest):
    # 1. تحويل النص إلى SQL مع خوارزمية الترتيب
    generated_sql = brain.text_to_sql(request.query_text)

    # 2. التنفيذ الآمن
    result = execute_protected_query(generated_sql)

    if result["status"] == "success":
        return {
            "status": "success",
            "interpretation": (
                "تم تحليل الطلب وترتيب النتائج حسب (الأهمية القصوى) باستخدام خوارزمية Atlas Ranker"
            ),
            "sql_generated": generated_sql.strip(),
            "results": result["data"],
        }
    else:
        raise HTTPException(status_code=400, detail=result["error"])
