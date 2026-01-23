"""
Saudi AI Middleware (Pro MLOps + NLP) v2.3
Central intelligence layer with intent classification and routing.
"""
import re
import uuid

import psycopg2
from fastapi import Body, FastAPI

app = FastAPI(title="Saudi AI Middleware (Pro MLOps + NLP)")


def get_db():
    """Get PostgreSQL database connection."""
    return psycopg2.connect(
        host="atlas-db",
        database="atlas_production",
        user="atlas_admin",
        password="Atlas_Secure_2026"
    )


# --- Intent Classification Engine ---
class IntentEngine:
    """Saudi Arabic intent classification with rule-based fallback."""

    def clean_text(self, text: str) -> str:
        text = str(text).lower()
        text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
        return text.strip()

    def classify(self, text: str) -> str:
        text_lower = self.clean_text(text)

        # Pricing
        if any(kw in text_lower for kw in [
            'سعر', 'كم', 'تكلفة', 'اشتراك', 'باقة', 'خصم', 'price'
        ]):
            return 'pricing_question'

        # Support
        if any(kw in text_lower for kw in [
            'مشكلة', 'خطأ', 'مو راضي', 'ما يشتغل', 'معلق', 'help', 'error'
        ]):
            return 'support_request'

        # Greeting
        if any(kw in text_lower for kw in [
            'السلام', 'مرحبا', 'صباح', 'مساء', 'هلا', 'أهلا', 'hello'
        ]):
            return 'greeting'

        # Complaint
        if any(kw in text_lower for kw in [
            'شكوى', 'زعلان', 'مستاء', 'سيء', 'complaint'
        ]):
            return 'complaint'

        # Order
        if any(kw in text_lower for kw in ['طلب', 'اشتري', 'شراء', 'order', 'buy']):
            return 'order_inquiry'

        return 'general_inquiry'

    def route(self, message: str) -> dict:
        intent = self.classify(message)

        routing = {
            'pricing_question': (
                'Generate Quote', 'Sales Team', 'medium',
                'شكراً لاستفسارك! سيتواصل معك فريق المبيعات.'
            ),
            'support_request': (
                'Create Ticket', 'Tech Support', 'high',
                'تم استلام طلبك! فريق الدعم سيساعدك قريباً.'
            ),
            'greeting': (
                'Auto Reply', 'AI Agent', 'low',
                'أهلاً وسهلاً! كيف يمكنني مساعدتك؟'
            ),
            'complaint': (
                'Escalate', 'Customer Relations', 'urgent',
                'نأسف لذلك. سيتواصل معك المدير شخصياً.'
            ),
            'order_inquiry': (
                'Check Status', 'Operations', 'medium',
                'جاري التحقق من طلبك...'
            ),
            'general_inquiry': (
                'Log', 'General Inbox', 'low',
                'شكراً لتواصلك! سنرد قريباً.'
            )
        }

        action, dept, priority, reply = routing.get(
            intent, routing['general_inquiry']
        )

        return {
            'original_message': message,
            'detected_intent': intent,
            'action': action,
            'department': dept,
            'priority': priority,
            'auto_reply': reply
        }


# --- Compliance Engine (PDPL) ---
class ComplianceEngine:
    """PDPL compliance layer for PII detection and masking."""

    def check_pii(self, text: str):
        patterns = {
            "SAUDI_ID": r"\b[12]\d{9}\b",
            "PHONE_SA": r"\b05\d{8}\b",
            "EMAIL": r"[^@]+@[^@]+\.[^@]+"
        }
        detected = []
        masked_text = text

        for p_type, regex in patterns.items():
            matches = re.findall(regex, text)
            if matches:
                detected.append(p_type)
                for m in matches:
                    if p_type == "PHONE_SA":
                        masked_text = masked_text.replace(m, "******" + m[-4:])
                    elif p_type == "SAUDI_ID":
                        masked_text = masked_text.replace(m, "##########")
                    elif p_type == "EMAIL":
                        parts = m.split("@")
                        masked_text = masked_text.replace(
                            m, parts[0][:2] + "***@" + parts[1]
                        )

        return {
            "has_pii": len(detected) > 0,
            "detected_types": detected,
            "masked_content": masked_text
        }


# --- Context Layer ---
class ContextLayer:
    """Domain classification for intelligent routing."""

    def analyze_domain(self, text: str):
        text_lower = text.lower()
        if any(w in text_lower for w in ["zakat", "tax", "invoice"]):
            return "Taxation & ZATCA"
        elif any(w in text_lower for w in ["salary", "hire", "leave"]):
            return "HR & Labor Law"
        elif any(w in text_lower for w in ["purchase", "vendor"]):
            return "Procurement"
        return "General"


# --- Decision Engine with PostgreSQL Logging ---
class DecisionEngine:
    """Central policy enforcement with DB-backed MLOps logging."""

    def __init__(self):
        self.current_version = "v1.0.0"

    def evaluate(self, context, risk_score, amount):
        allowed = True
        reason = "Approved by AI Middleware"

        if risk_score > 60:
            allowed = False
            reason = "High Risk Vendor (Central Policy)"
        elif amount > 100000:
            allowed = False
            reason = "Amount exceeds auto-approval limit"

        # MLOps: Log prediction to PostgreSQL
        pred_id = str(uuid.uuid4())
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO ai_predictions
                   (id, model_version, input_context, risk_score, decision)
                   VALUES (%s, %s, %s, %s, %s)""",
                (pred_id, self.current_version, str(context), risk_score,
                 "ALLOWED" if allowed else "BLOCKED")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"MLOps DB Log Error: {e}")

        return {"allowed": allowed, "reason": reason, "prediction_id": pred_id}


intent_engine = IntentEngine()
compliance = ComplianceEngine()
context_layer = ContextLayer()
engine = DecisionEngine()


@app.post("/v1/intent/classify")
def classify_intent(payload: dict = Body(...)):
    """Classify message intent and return routing recommendation."""
    message = payload.get("message", "")
    return intent_engine.route(message)


@app.post("/v1/compliance/scan")
def scan_text(payload: dict = Body(...)):
    """Scan text for PII and return masked version."""
    return compliance.check_pii(payload.get("text", ""))


@app.post("/v1/context/analyze")
def analyze_context(payload: dict = Body(...)):
    """Classify the domain of a text query."""
    return {"domain": context_layer.analyze_domain(payload.get("text", ""))}


@app.post("/v1/decision/evaluate")
def evaluate(payload: dict = Body(...)):
    """Evaluate a business transaction and log to PostgreSQL."""
    return engine.evaluate(
        payload.get("context", ""),
        payload.get("risk_score", 0),
        payload.get("amount", 0)
    )


@app.post("/v1/mlops/feedback")
def feedback(payload: dict = Body(...)):
    """Store user feedback in PostgreSQL for model improvement."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ai_feedback
               (prediction_id, actual_feedback, correction_note)
               VALUES (%s, %s, %s)""",
            (payload.get("prediction_id"),
             payload.get("feedback"),
             payload.get("correction"))
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Feedback recorded in database"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/v1/mlops/stats")
def get_stats():
    """Get MLOps statistics from PostgreSQL."""
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM ai_predictions")
        total_predictions = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM ai_feedback WHERE actual_feedback = 'positive'"
        )
        positive = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM ai_feedback WHERE actual_feedback = 'negative'"
        )
        negative = cur.fetchone()[0]

        cur.execute(
            "SELECT version, status FROM ai_models WHERE status = 'ACTIVE' LIMIT 1"
        )
        model_info = cur.fetchone()

        conn.close()

        total_fb = positive + negative
        accuracy = (positive / total_fb * 100) if total_fb > 0 else 100

        return {
            "model_version": model_info[0] if model_info else "unknown",
            "model_status": model_info[1] if model_info else "unknown",
            "total_predictions": total_predictions,
            "feedback": {"positive": positive, "negative": negative},
            "accuracy": round(accuracy, 1)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
def root():
    return {"status": "Operational", "version": "2.3 NLP"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Saudi AI Middleware",
        "version": "2.3",
        "capabilities": [
            "PDPL Compliance",
            "Intent Classification",
            "Decision Engine",
            "MLOps"
        ]
    }
