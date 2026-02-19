import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'incident_management.settings')
django.setup()

def verify_migration():
    print("Verifying migration...")
    
    # 1. Verify incidents.services.gemini_analyzer
    print("\n1. Checking incidents.services.gemini_analyzer...")
    try:
        from incidents.services.gemini_analyzer import GeminiAnalyzer
        analyzer = GeminiAnalyzer()
        print("  - Import successful")
        if hasattr(analyzer, 'client'):
            print("  - Has 'client' attribute (New SDK)")
        else:
            print("  - MISSING 'client' attribute")
            
        if hasattr(analyzer, 'model'):
            print("  - Has 'model' attribute (Old SDK?)")
        else:
            print("  - No 'model' attribute (Correct)")
            
    except Exception as e:
        print(f"  - Error: {e}")

    # 2. Verify incidents.services.similarity_detector
    print("\n2. Checking incidents.services.similarity_detector...")
    try:
        from incidents.services.similarity_detector import SimilarityDetector
        detector = SimilarityDetector()
        print("  - Import successful")
        if hasattr(detector, 'client'):
            print("  - Has 'client' attribute (New SDK)")
        else:
            print("  - MISSING 'client' attribute")
    except Exception as e:
        print(f"  - Error: {e}")

    # 3. Verify app.services.gemini_analyzer
    print("\n3. Checking app.services.gemini_analyzer...")
    try:
        from app.services.gemini_analyzer import GeminiAnalyzerService
        service = GeminiAnalyzerService()
        print("  - Import successful")
        if hasattr(service, 'client'):
            print("  - Has 'client' attribute (New SDK)")
        else:
            print("  - MISSING 'client' attribute")
    except Exception as e:
        print(f"  - Error: {e}")

    print("\nVerification complete.")

if __name__ == "__main__":
    verify_migration()
