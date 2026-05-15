# incidents/services/local_inference.py
import torch
import json
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from django.conf import settings

# 🔑 HF_TOKEN ko .env ya settings se fetch karna
HF_TOKEN = getattr(settings, 'HF_TOKEN', os.environ.get('HF_TOKEN'))


class LocalPhi3Fallback:
    _instance = None
    _model = None
    _tokenizer = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            model_path = "unsloth/Phi-3-mini-4k-instruct"  # Base model
            adapter_path = os.path.join(settings.BASE_DIR, 'incidents', 'ai_models', 'custom_model')

            print(f"🚀 Loading Local Fallback Model from {adapter_path}...")

            if HF_TOKEN:
                print("✅ HF_TOKEN detected! Using authenticated fast download...")
            else:
                print("⚠️ Warning: No HF_TOKEN found. Download might fail or be slow.")

            # Base model load karna (WITH TOKEN)
            base_model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                token=HF_TOKEN  # <--- YAHAN TOKEN ADD KIYA HAI
            )

            # Aapka trained adapter (zip wali files) connect karna
            cls._model = PeftModel.from_pretrained(base_model, adapter_path)

            # Tokenizer load karna (WITH TOKEN)
            cls._tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                token=HF_TOKEN  # <--- YAHAN BHI TOKEN ADD KIYA HAI
            )

        return cls._model, cls._tokenizer

    @classmethod
    def analyze(cls, log_text):
        try:
            model, tokenizer = cls.get_model()

            prompt = f"Analyze the following system logs and provide a complete, production-grade incident analysis. Return ONLY valid JSON.\n\nLog: {log_text}"

            inputs = tokenizer(prompt, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
            outputs = model.generate(**inputs, max_new_tokens=512)
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # JSON part nikalna
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            return json.loads(response[json_start:json_end])
        except Exception as e:
            print(f"❌ Local Fallback also failed: {e}")
            return None