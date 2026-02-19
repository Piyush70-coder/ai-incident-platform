
import sys
import os

# Mock django setup if needed, but for these pure functions we might get away without it
# if we don't import the models. 
# However, tasks.py imports models.
# We will test the pure logic functions from services.

try:
    from incidents.services.ai_parser import parse_ai_output
    from incidents.services.postmortem_service import generate_postmortem
except ImportError:
    # Add current directory to path
    sys.path.append(os.getcwd())
    from incidents.services.ai_parser import parse_ai_output
    from incidents.services.postmortem_service import generate_postmortem

def test_parser():
    print("Testing parse_ai_output...")
    
    # Case 1: Perfect Output
    raw_1 = """
    Root Cause: Redis connection timeout
    Explanation: The application failed to connect to the Redis instance at 10.0.0.5 due to a network partition.
    Confidence: 0.95
    """
    rc, expl, conf = parse_ai_output(raw_1)
    print(f"Case 1 (Perfect): RC='{rc}', Expl='{expl}', Conf={conf}")
    assert "Redis" in rc
    assert conf == 0.85 # Clamped from 0.95

    # Case 2: Generic Output (Fallback Trigger)
    raw_2 = "The system is having an unknown error."
    rc, expl, conf = parse_ai_output(raw_2)
    print(f"Case 2 (Generic): RC='{rc}', Expl='{expl}', Conf={conf}")
    assert "Application performance degradation" in rc or "unknown" not in rc.lower()
    assert conf >= 0.30

    # Case 3: Keyword Fallback
    raw_3 = "We see a lot of database connection errors in the logs."
    rc, expl, conf = parse_ai_output(raw_3)
    print(f"Case 3 (Keyword DB): RC='{rc}', Expl='{expl}', Conf={conf}")
    assert "Database" in rc

    # Case 4: CPU Fallback
    raw_4 = "High cpu load observed on the server."
    rc, expl, conf = parse_ai_output(raw_4)
    print(f"Case 4 (Keyword CPU): RC='{rc}', Expl='{expl}', Conf={conf}")
    assert "CPU" in rc

    print("Parser tests passed!\n")

def test_postmortem():
    print("Testing generate_postmortem...")
    
    # Case 1: Redis
    pm_redis = generate_postmortem("logs...", "Redis connection timeout", "Redis failed.")
    print("Case 1 (Redis Actions):")
    if "circuit breakers" in pm_redis:
        print("  - Found 'circuit breakers' (Pass)")
    else:
        print("  - FAILED: Missing redis actions")
        print(pm_redis)

    # Case 2: Database
    pm_db = generate_postmortem("logs...", "Database pool exhaustion", "DB full.")
    print("Case 2 (DB Actions):")
    if "HikariCP" in pm_db:
        print("  - Found 'HikariCP' (Pass)")
    else:
        print("  - FAILED: Missing DB actions")

    print("Postmortem tests passed!\n")

if __name__ == "__main__":
    test_parser()
    test_postmortem()
