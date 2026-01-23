import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model

# ========================================================
# ⚙️ إعدادات المشروع
# ========================================================
MODEL_NAME = "Qwen/Qwen2.5-32B-Instruct"
DATA_PATH = "/workspace/atlas_erp/data/qwen_train.jsonl"
OUTPUT_DIR = "/workspace/atlas_erp/models/atlas-qwen-full"

print(f"🚀 جاري تجهيز أطلس للتدريب المكثف على موديل: {MODEL_NAME}")

# ========================================================
# 1️⃣ تحميل الموديل بضغط عالي (4-bit)
# ========================================================
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    use_cache=False
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
tokenizer.pad_token = tokenizer.eos_token

# ========================================================
# 2️⃣ إعدادات المحول (LoRA Adapter)
# ========================================================
peft_config = LoraConfig(
    lora_alpha=16,
    lora_dropout=0.05,
    r=64,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
)

# ========================================================
# 3️⃣ تحميل البيانات السعودية
# ========================================================
try:
    dataset = load_dataset("json", data_files=DATA_PATH, split="train")
    print(f"✅ تم تحميل {len(dataset)} سجل سعودي جاهز للحقن!")
except Exception as e:
    print(f"❌ خطأ في تحميل الملف: {e}")
    exit()

# ========================================================
# 4️⃣ إعدادات التدريب (1000 خطوة)
# ========================================================
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    optim="paged_adamw_32bit",
    save_steps=200,
    logging_steps=25,
    learning_rate=1e-4,
    fp16=True,
    max_grad_norm=0.3,
    max_steps=1000,     # 🔥 التدريب الطويل
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="cosine",
    report_to="tensorboard"
)

# ========================================================
# 5️⃣ بدء المعركة
# ========================================================
print("🔥 الفرن جاهز.. جاري بدء التدريب (هذا قد يستغرق ساعة أو ساعتين)...")

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=1024,
    processing_class=tokenizer,
    args=training_args,
)

trainer.train()

# ========================================================
# 6️⃣ الحفظ النهائي
# ========================================================
print("🎉 تم الانتهاء بنجاح! جاري حفظ النسخة النهائية...")
trainer.model.save_pretrained(f"{OUTPUT_DIR}/final")
tokenizer.save_pretrained(f"{OUTPUT_DIR}/final")
print(f"✅ أطلس (النسخة الكاملة) محفوظ في: {OUTPUT_DIR}/final")
