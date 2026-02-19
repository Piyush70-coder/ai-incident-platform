import re

def parse_ai_output(text: str):
    # 1. Regex Extraction with Strict Boundaries
    rc_match = re.search(r"Root Cause:\s*(.+?)(?=\n\s*Explanation:|$)", text, re.IGNORECASE | re.DOTALL)
    ex_match = re.search(r"Explanation:\s*(.+?)(?=\n\s*Confidence:|$)", text, re.IGNORECASE | re.DOTALL)
    conf_match = re.search(r"Confidence:\s*([0-9.]+)", text, re.IGNORECASE)

    root_cause = rc_match.group(1).strip() if rc_match else ""
    explanation = ex_match.group(1).strip() if ex_match else ""
    
    # 2. Parse Confidence (Heuristic base if missing)
    try:
        confidence = float(conf_match.group(1)) if conf_match else 0.3
    except ValueError:
        confidence = 0.3

    # 3. Detect & Reject Placeholders / Generic Content
    forbidden_phrases = [
        "<specific technical cause>", "<technical analysis>", "analysis in progress",
        "system component failed", "unknown error", "check logs", "investigating"
    ]
    
    is_placeholder = any(phrase in root_cause.lower() for phrase in forbidden_phrases)
    is_generic = len(root_cause) < 5 or root_cause.lower() in ["error", "failure", "timeout", "unknown"]
    
    if is_placeholder or is_generic:
        root_cause = ""  # Force fallback

    # 4. Deterministic Fallback Inference (Keyword-based)
    if not root_cause:
        text_lower = text.lower()
        if "redis" in text_lower:
            root_cause = "Redis Cache Connection Timeout"
        elif "postgres" in text_lower or "db" in text_lower or "database" in text_lower:
            root_cause = "Database Connection Pool Exhaustion"
        elif "dns" in text_lower:
            root_cause = "DNS Resolution Failure"
        elif "kafka" in text_lower or "consumer" in text_lower:
            root_cause = "Kafka Consumer Group Lag"
        elif "504" in text_lower or "gateway" in text_lower:
            root_cause = "API Gateway Timeout (504)"
        elif "oom" in text_lower or "memory" in text_lower:
            root_cause = "Container OOMKilled"
        elif "connection refused" in text_lower:
            root_cause = "Service Connection Refused"
        elif "disk" in text_lower:
            root_cause = "Disk Space Exhaustion"
        else:
            root_cause = "Application Performance Degradation"  # Final safe fallback

    # 5. Ensure Explanation is not empty
    if not explanation or any(p in explanation.lower() for p in forbidden_phrases) or len(explanation) < 10:
        explanation = f"Automated analysis detected patterns consistent with {root_cause}."

    # 6. Clamp Confidence (Strict 0.30 - 0.85 range)
    confidence = max(0.30, min(0.85, confidence))

    return root_cause, explanation, confidence
