"""
Deterministic confidence scoring - NO AI hallucination
Based on actual data signals, not model output
"""
import re
from typing import Tuple


def calculate_deterministic_confidence(incident, similarity_score: float = 0.0) -> float:
    """
    Calculate confidence score deterministically based on:
    - similarity score from MiniLM (0-1)
    - number of matching error patterns in logs
    - presence of recovery signals
    - clarity of incident description
    - number of infrastructure components involved
    
    Returns float between 0 and 1
    """
    confidence = 0.0
    
    # 1. Similarity score (30% weight)
    # Higher similarity = higher confidence
    similarity_weight = min(0.30, similarity_score * 0.30)
    confidence += similarity_weight
    
    # 2. Error patterns in logs (25% weight)
    logs = incident.logs.filter(processed=True)
    error_patterns = [
        r'error', r'exception', r'failed', r'failure', r'timeout',
        r'connection.*error', r'pool.*exhausted', r'connection.*refused'
    ]
    
    pattern_matches = 0
    for log in logs:
        content = (log.processed_content or "").lower()
        for pattern in error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                pattern_matches += 1
                break  # Count each log once
    
    if logs.exists():
        pattern_ratio = min(1.0, pattern_matches / logs.count())
        pattern_weight = pattern_ratio * 0.25
        confidence += pattern_weight
    
    # 3. Recovery signals (15% weight)
    # If recovery signal exists, we have more context
    description = (incident.description or "").lower()
    all_text = description
    
    for log in logs:
        all_text += " " + (log.processed_content or "").lower()
    
    recovery_signals = ['restart', 'recovered', 'fixed', 'resolved', 'auto.*recover']
    has_recovery = any(re.search(signal, all_text, re.IGNORECASE) for signal in recovery_signals)
    
    if has_recovery:
        confidence += 0.15
    
    # 4. Description clarity (15% weight)
    if incident.description:
        desc_len = len(incident.description.strip())
        if desc_len > 100:
            confidence += 0.15  # Detailed description
        elif desc_len > 50:
            confidence += 0.10  # Moderate description
        elif desc_len > 20:
            confidence += 0.05  # Basic description
    
    # 5. Infrastructure components detected (15% weight)
    # More specific components = higher confidence
    components = []
    all_text_lower = all_text.lower()
    
    if re.search(r'database|db|mysql|postgresql|postgres', all_text_lower):
        components.append('database')
    if re.search(r'redis|cache|redisson', all_text_lower):
        components.append('redis')
    if re.search(r'kafka|queue|broker', all_text_lower):
        components.append('kafka')
    if re.search(r'api|endpoint|service', all_text_lower):
        components.append('api')
    
    if components:
        # More components = more context = higher confidence
        component_weight = min(0.15, len(components) * 0.05)
        confidence += component_weight
    
    # Ensure 0.0-1.0 range
    return max(0.0, min(1.0, confidence))


def get_confidence_with_similarity(incident) -> Tuple[float, float]:
    """
    Get confidence score with similarity score
    Returns (confidence, similarity_score)
    """
    try:
        from incidents.services.similarity_service import find_similar_incidents_db
        
        similar = find_similar_incidents_db(incident.title, top_k=1)
        similarity_score = similar[0][1] if similar else 0.0
    except:
        similarity_score = 0.0
    
    confidence = calculate_deterministic_confidence(incident, similarity_score)
    
    return confidence, similarity_score

