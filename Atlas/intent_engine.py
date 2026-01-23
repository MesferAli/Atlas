"""
Saudi Arabic Intent Classification Engine
Integrates with Atlas for intelligent message routing.
"""
import os
import pickle
import re

# Model path
MODEL_PATH = "/app/models/intent_classifier_50k.pkl"
model = None


def load_model():
    """Load the trained intent classifier."""
    global model
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            print("✅ Saudi AI Intent Model loaded successfully!")
            return True
        except Exception as e:
            print(f"⚠️ Model load error: {e}")
    else:
        print(f"ℹ️ Model not found at {MODEL_PATH}, using rule-based fallback")
    return False


def clean_text(text: str) -> str:
    """Clean and normalize Arabic text."""
    text = str(text).lower()
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)  # Keep Arabic chars
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def rule_based_classify(text: str) -> str:
    """Fallback rule-based classification for Arabic intents."""
    text_lower = text.lower()

    # Pricing intent
    pricing_keywords = [
        'سعر', 'كم', 'تكلفة', 'اشتراك', 'باقة', 'عرض', 'خصم', 'price', 'cost'
    ]
    if any(kw in text_lower for kw in pricing_keywords):
        return 'pricing_question'

    # Support intent
    support_keywords = [
        'مشكلة', 'خطأ', 'مو راضي', 'ما يشتغل', 'معلق', 'بطيء', 'help', 'error'
    ]
    if any(kw in text_lower for kw in support_keywords):
        return 'support_request'

    # Greeting intent
    greeting_keywords = [
        'السلام', 'مرحبا', 'صباح', 'مساء', 'هلا', 'أهلا', 'hello', 'hi'
    ]
    if any(kw in text_lower for kw in greeting_keywords):
        return 'greeting'

    # Complaint intent
    complaint_keywords = ['شكوى', 'زعلان', 'مستاء', 'سيء', 'complaint']
    if any(kw in text_lower for kw in complaint_keywords):
        return 'complaint'

    # Order/Purchase intent
    order_keywords = ['طلب', 'اشتري', 'شراء', 'order', 'buy']
    if any(kw in text_lower for kw in order_keywords):
        return 'order_inquiry'

    return 'general_inquiry'


def classify_intent(text: str) -> str:
    """Classify the intent of a message."""
    cleaned = clean_text(text)

    if model is not None:
        try:
            return model.predict([cleaned])[0]
        except Exception as e:
            print(f"Model prediction error: {e}")

    return rule_based_classify(cleaned)


def route_message(message: str) -> dict:
    """Classify intent and determine routing action."""
    intent = classify_intent(message)

    # Business logic routing
    routing_rules = {
        'pricing_question': {
            'action': 'Generate Quote',
            'department': 'Sales Team',
            'priority': 'medium',
            'auto_reply': 'شكراً لاستفسارك! سيتواصل معك فريق المبيعات قريباً.'
        },
        'support_request': {
            'action': 'Create Support Ticket',
            'department': 'Tech Support',
            'priority': 'high',
            'auto_reply': 'تم استلام طلبك! فريق الدعم الفني سيساعدك في أقرب وقت.'
        },
        'greeting': {
            'action': 'Auto Reply',
            'department': 'AI Agent',
            'priority': 'low',
            'auto_reply': 'أهلاً وسهلاً! كيف يمكنني مساعدتك اليوم؟'
        },
        'complaint': {
            'action': 'Escalate to Manager',
            'department': 'Customer Relations',
            'priority': 'urgent',
            'auto_reply': 'نأسف لسماع ذلك. سيتواصل معك مدير خدمة العملاء شخصياً.'
        },
        'order_inquiry': {
            'action': 'Check Order Status',
            'department': 'Operations',
            'priority': 'medium',
            'auto_reply': 'جاري التحقق من حالة طلبك...'
        },
        'general_inquiry': {
            'action': 'Log for Review',
            'department': 'General Inbox',
            'priority': 'low',
            'auto_reply': 'شكراً لتواصلك! سنرد عليك قريباً.'
        }
    }

    route_info = routing_rules.get(intent, routing_rules['general_inquiry'])

    return {
        'original_message': message,
        'cleaned_text': clean_text(message),
        'detected_intent': intent,
        'recommended_action': route_info['action'],
        'routed_to': route_info['department'],
        'priority': route_info['priority'],
        'auto_reply': route_info['auto_reply'],
        'model_used': 'ml_model' if model else 'rule_based'
    }


# Try to load model on import
load_model()
