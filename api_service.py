import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
import uvicorn

HF_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER_PATH = "/workspace/atlas_erp/models/atlas-qwen-full/final"

app = FastAPI(title="Atlas ERP Saudi Advisor API")

print("جاري تحميل التوكنايزر...")
tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_ID, trust_remote_code=True)

print("جاري تحميل النموذج الأساسي من HuggingFace...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)

base_model = AutoModelForCausalLM.from_pretrained(
    HF_MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

print("جاري تحميل محول LoRA المدرب...")
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
model.eval()
print("✅ النموذج جاهز!")

class Query(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7

@app.post("/ask")
async def ask_atlas(query: Query):
    try:
        prompt = f"""<|im_start|>system
أنت خبير استشاري في أنظمة أوراكل السعودية.<|im_end|>
<|im_start|>user
{query.prompt}<|im_end|>
<|im_start|>assistant
"""
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=query.max_tokens,
                temperature=query.temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return {"status": "success", "response": response.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "Atlas-Qwen-7B-Saudi"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
