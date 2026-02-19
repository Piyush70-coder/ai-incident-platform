import os
from django.conf import settings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import torch

# =========================================================
# 1. SETUP: LOAD CUSTOM MODEL
# =========================================================
BASE_MODEL = "google/flan-t5-base"
CUSTOM_MODEL_PATH = os.path.join(settings.BASE_DIR, "incidents", "ai_models", "custom_model")

print(f"🔄 AI System initializing...")

try:
    # Google Base Model
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)

    # Custom Brain (Agar hai toh)
    if os.path.exists(CUSTOM_MODEL_PATH):
        print(f"🛠️ Custom Brain Found: {CUSTOM_MODEL_PATH}")
        model = PeftModel.from_pretrained(base_model, CUSTOM_MODEL_PATH)
        print("✅ SUCCESS: Custom AI (5-Point Mode) Active!")
    else:
        print("⚠️ Custom model missing. Using Base Model.")
        model = base_model

except Exception as e:
    print(f"❌ Error loading model: {e}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)


# =========================================================
# 2. GENERATION FUNCTION (5 POINTS ENFORCED)
# =========================================================
def generate_root_cause(context: str) -> dict:
    # 🔥 PROMPT: STRICT 5-POINT RULE
    prompt = (
        "Role: Senior SRE. Task: Analyze incident logs and provide a detailed Technical Explanation.\n"
        "Strictly Forbidden: 'Automated analysis detected', 'Patterns consistent with', 'Generic errors'.\n"
        "Strictly Forbidden: One-line summaries. You MUST provide details.\n\n"
        "Instructions:\n"
        "1. Identify the specific infrastructure failure (e.g. 'Postgres Connection Exhaustion').\n"
        "2. Break down the analysis into EXACTLY 5 numbered technical points.\n"
        "3. Cite specific log lines/errors in the points.\n\n"
        "Incident Context:\n"
        f"{context}\n\n"
        "Output Format:\n"
        "Root Cause: [Specific Technical Issue]\n"
        "Explanation:\n"
        "1. [Technical Point 1 - What failed]\n"
        "2. [Technical Point 2 - Evidence from logs]\n"
        "3. [Technical Point 3 - Why it happened]\n"
        "4. [Technical Point 4 - Impact breakdown]\n"
        "5. [Technical Point 5 - Resolution/Action]"
    )

    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

        # Max Tokens badha diye (350) taaki wo 5 points likh sake
        outputs = model.generate(
            **inputs,
            max_new_tokens=350,
            temperature=0.3,  # Thoda creative hone do
            do_sample=False
        )

        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return {"raw": text}

    except Exception as e:
        print(f"Error generating text: {e}")
        return {"raw": "Analysis failed."}