import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()

from incidents.services.gemini_analyzer import GeminiAnalyzer
from incidents.services.similarity_detector import SimilarityDetector
from app.services.gemini_analyzer import GeminiAnalyzerService

def verify_model_names():
    print("Verifying model names in source code (static check)...")
    
    files = [
        'incidents/services/gemini_analyzer.py',
        'incidents/services/similarity_detector.py',
        'app/services/gemini_analyzer.py'
    ]
    
    for fpath in files:
        with open(fpath, 'r') as f:
            content = f.read()
            if 'gemini-2.0-flash-exp' in content:
                print(f"✅ {fpath}: Updated to gemini-2.0-flash-exp")
            elif 'gemini-1.5-flash' in content:
                print(f"❌ {fpath}: Still using gemini-1.5-flash")
            else:
                print(f"⚠️ {fpath}: Model name not found")

    print("\nAttempting to initialize services...")
    try:
        analyzer = GeminiAnalyzer()
        print("✅ GeminiAnalyzer initialized")
    except Exception as e:
        print(f"❌ GeminiAnalyzer failed: {e}")

    try:
        detector = SimilarityDetector()
        print("✅ SimilarityDetector initialized")
    except Exception as e:
        print(f"❌ SimilarityDetector failed: {e}")

if __name__ == "__main__":
    verify_model_names()
