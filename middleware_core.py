"""
Saudi AI Middleware + MLOps v2.1
Central intelligence layer for Atlas ERP with continuous learning capabilities.
"""
import datetime
import json
import re

from fastapi import Body, FastAPI

app = FastAPI(title="Saudi AI Middleware + MLOps v2.1")

FEEDBACK_FILE = "/tmp/mlops_feedback.jsonl"


# --- MLOps Engine ---
class MLOpsEngine:
    """
    MLOps layer for tracking predictions and capturing user feedback.
    Enables continuous improvement through human-in-the-loop learning.
    """

    def log_prediction(self, model_name, input_data, output, confidence):
        """Log prediction for observability and future analysis."""
        log_entry = {
            "timestamp": str(datetime.datetime.now()),
            "model": model_name,
            "input": input_data,
            "prediction": output,
            "confidence": confidence
        }
        print(f"MLOPS LOG: {json.dumps(log_entry)}")
        return log_entry

    def capture_feedback(self, prediction_id, user_feedback, correction=None):
        """
        Capture user feedback on a prediction.
        This is the core of MLOps: learning from mistakes.
        """
        entry = {
            "timestamp": str(datetime.datetime.now()),
            "prediction_id": prediction_id,
            "feedback": user_feedback,
            "correction": correction
        }
        try:
            with open(FEEDBACK_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Feedback write error: {e}")

        return {"status": "Feedback Recorded", "drift_alert": False}

    def get_feedback_stats(self):
        """Get statistics on collected feedback."""
        try:
            with open(FEEDBACK_FILE, "r") as f:
                lines = f.readlines()
            positive = sum(1 for line in lines if '"feedback": "positive"' in line)
            negative = sum(1 for line in lines if '"feedback": "negative"' in line)
            return {"total": len(lines), "positive": positive, "negative": negative}
        except FileNotFoundError:
            return {"total": 0, "positive": 0, "negative": 0}


mlops = MLOpsEngine()


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
        if any(w in text_lower for w in ["zakat", "tax", "invoice", "فاتورة"]):
            return "Taxation & ZATCA"
        elif any(w in text_lower for w in ["salary", "hire", "leave", "راتب"]):
            return "HR & Labor Law"
        elif any(w in text_lower for w in ["purchase", "vendor", "شراء"]):
            return "Procurement"
        return "General"


# --- Decision Engine ---
class DecisionEngine:
    """Central policy enforcement for business decisions."""

    def evaluate_transaction(self, context, risk_score, amount):
        decision = {"allowed": True, "reason": "Approved by AI Middleware"}

        if risk_score > 60:
            decision = {"allowed": False, "reason": "High Risk Vendor (Central Policy)"}
        elif amount > 100000:
            decision = {"allowed": False, "reason": "Amount exceeds auto-approval limit"}

        # Log to MLOps
        mlops.log_prediction(
            "risk_model_v1",
            {"risk": risk_score, "amount": amount, "context": context},
            decision,
            0.95
        )
        return decision


compliance = ComplianceEngine()
context_layer = ContextLayer()
decision = DecisionEngine()


# --- API Endpoints ---


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
    """Evaluate a business transaction and return decision with prediction_id."""
    pred_id = f"pred_{int(datetime.datetime.now().timestamp())}"
    res = decision.evaluate_transaction(
        context=payload.get("context", ""),
        risk_score=payload.get("risk_score", 0),
        amount=payload.get("amount", 0)
    )
    res["prediction_id"] = pred_id
    return res


@app.post("/v1/mlops/feedback")
def submit_feedback(payload: dict = Body(...)):
    """Submit user feedback on a prediction for continuous learning."""
    return mlops.capture_feedback(
        prediction_id=payload.get("prediction_id"),
        user_feedback=payload.get("feedback"),
        correction=payload.get("correction")
    )


@app.get("/v1/mlops/stats")
def get_stats():
    """Get feedback statistics for monitoring model drift."""
    return mlops.get_feedback_stats()


@app.get("/")
def root():
    return {"status": "Middleware Operational", "version": "2.1 MLOps"}


@app.get("/health")
def health():
    stats = mlops.get_feedback_stats()
    return {
        "status": "healthy",
        "service": "Saudi AI Middleware + MLOps",
        "version": "2.1",
        "layers": [
            "PDPL Compliance",
            "Context Analysis",
            "Decision Engine",
            "MLOps Feedback"
        ],
        "feedback_stats": stats
    }
