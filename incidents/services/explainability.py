def build_explainability(context: str, ai_result: dict) -> dict:
    """
    Explain WHY AI suggested a root cause
    """
    explanations = []

    for rc in ai_result.get("root_causes", []):
        explanations.append({
            "cause": rc.get("cause"),
            "reason": "Based on repeated error patterns and timeline correlation.",
            "evidence": rc.get("evidence", []),
            "confidence": rc.get("probability", 0.0)
        })

    return {
        "summary": "Root causes were inferred from log frequency, error spikes, and event order.",
        "details": explanations
    }
