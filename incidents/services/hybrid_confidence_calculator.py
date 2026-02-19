"""
Hybrid Confidence Calculator
Combines FLAN-T5 model confidence with data-driven factors:
- Log presence and quality
- Keyword detection (redis, kafka, timeout, db)
- Similar incident matching
- Data completeness
"""
import re
from typing import Tuple, List


# Critical keywords that indicate clear root causes
CRITICAL_KEYWORDS = {
    'redis': ['redis', 'cache', 'redisson'],
    'kafka': ['kafka', 'kafka consumer', 'kafka producer', 'broker'],
    'timeout': ['timeout', 'timed out', 'connection timeout', 'request timeout'],
    'db': ['database', 'db', 'mysql', 'postgresql', 'postgres', 'mongodb', 'connection pool'],
    'network': ['network', 'dns', 'connection refused', 'connection error'],
    'memory': ['memory', 'oom', 'out of memory', 'heap'],
    'disk': ['disk', 'disk space', 'no space', 'storage']
}


def detect_keywords_in_text(text: str) -> dict:
    """
    Detect critical keywords in text
    Returns dict with keyword categories found
    """
    if not text:
        return {}
    
    text_lower = text.lower()
    found_keywords = {}
    
    for category, keywords in CRITICAL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords[category] = found_keywords.get(category, 0) + 1
    
    return found_keywords


def calculate_keyword_confidence(incident) -> Tuple[float, List[str]]:
    """
    Calculate confidence based on keyword detection
    Returns (score, detected_keywords_list)
    """
    score = 0.0
    detected_keywords = []
    
    # Check logs first (highest weight)
    logs = incident.logs.filter(processed=True)
    log_keywords = {}
    
    for log in logs:
        content = (log.processed_content or "").lower()
        keywords = detect_keywords_in_text(content)
        for category, count in keywords.items():
            log_keywords[category] = log_keywords.get(category, 0) + count
    
    # Log keywords are worth more (0.15 max)
    if log_keywords:
        unique_categories = len(log_keywords)
        total_matches = sum(log_keywords.values())
        # More categories and matches = higher confidence
        log_score = min(0.15, (unique_categories * 0.05) + (min(total_matches, 5) * 0.02))
        score += log_score
        detected_keywords.extend([f"{cat} (in logs)" for cat in log_keywords.keys()])
    
    # Check description (medium weight - 0.07 max)
    if incident.description:
        desc_keywords = detect_keywords_in_text(incident.description)
        if desc_keywords:
            unique_categories = len(desc_keywords)
            desc_score = min(0.07, unique_categories * 0.035)
            score += desc_score
            detected_keywords.extend([f"{cat} (in description)" for cat in desc_keywords.keys()])
    
    # Check title (low weight - 0.03 max)
    if incident.title:
        title_keywords = detect_keywords_in_text(incident.title)
        if title_keywords:
            score += min(0.03, len(title_keywords) * 0.015)
            detected_keywords.extend([f"{cat} (in title)" for cat in title_keywords.keys()])
    
    return min(0.25, score), list(set(detected_keywords))


def calculate_log_presence_score(incident) -> Tuple[float, dict]:
    """
    Calculate confidence based on log file presence and quality
    Returns (score, metadata_dict)
    """
    logs = incident.logs.all()
    
    if not logs.exists():
        return 0.0, {"log_count": 0, "processed_count": 0, "error_count": 0}
    
    log_count = logs.count()
    processed_logs = logs.filter(processed=True)
    processed_count = processed_logs.count()
    
    score = 0.0
    
    # Base score for having logs (0.10 max)
    if log_count > 0:
        score += min(0.10, log_count * 0.033)  # 3 logs = 0.10
    
    # Processed logs score (0.08 max)
    if processed_count > 0:
        processing_ratio = processed_count / log_count
        score += min(0.08, processing_ratio * 0.08)
    
    # Error patterns in logs (0.07 max)
    error_patterns = [
        r'error', r'exception', r'failed', r'failure', r'fatal',
        r'timeout', r'connection.*error', r'pool.*exhausted'
    ]
    
    error_count = 0
    for log in processed_logs:
        content = (log.processed_content or "").lower()
        for pattern in error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                error_count += 1
                break
    
    if error_count > 0:
        score += min(0.07, (error_count / log_count) * 0.07)
    
    metadata = {
        "log_count": log_count,
        "processed_count": processed_count,
        "error_count": error_count
    }
    
    return min(0.25, score), metadata


def calculate_similarity_confidence(incident) -> Tuple[float, float]:
    """
    Calculate confidence boost from similar past incidents
    Returns (score, max_similarity)
    """
    try:
        from incidents.services.similarity_service import find_similar_incidents_db
        
        similar = find_similar_incidents_db(incident.title, top_k=3)
        
        if not similar:
            return 0.0, 0.0
        
        max_similarity = max(score for _, score in similar)
        
        # Scale similarity to confidence boost
        if max_similarity > 0.8:
            return 0.15, max_similarity
        elif max_similarity > 0.6:
            return 0.12, max_similarity
        elif max_similarity > 0.4:
            return 0.08, max_similarity
        elif max_similarity > 0.3:
            return 0.05, max_similarity
        
        return 0.0, max_similarity
    except:
        return 0.0, 0.0


def calculate_data_completeness_score(incident) -> float:
    """
    Calculate confidence based on incident information completeness
    """
    score = 0.0
    
    # Title (0.03)
    if incident.title and len(incident.title.strip()) > 10:
        score += 0.03
    
    # Description (0.05)
    if incident.description:
        desc_len = len(incident.description.strip())
        if desc_len > 100:
            score += 0.05
        elif desc_len > 50:
            score += 0.03
        elif desc_len > 20:
            score += 0.02
    
    # Severity (0.02)
    if incident.severity:
        score += 0.02
    
    # Category (0.02)
    if incident.category:
        score += 0.02
    
    # Affected services (0.03)
    if incident.affected_services and len(incident.affected_services) > 0:
        score += 0.03
    
    return min(0.15, score)


def calculate_hybrid_confidence(
    incident,
    model_confidence: float = 0.5,
    root_cause_found_in_logs: bool = False
) -> Tuple[float, dict]:
    """
    Calculate hybrid confidence score combining multiple factors
    
    Args:
        incident: Incident instance
        model_confidence: FLAN-T5 model confidence (0.0-1.0)
        root_cause_found_in_logs: Whether root cause was found in logs
    
    Returns:
        (final_confidence, breakdown_dict)
    """
    # 1. Log Presence Score (25% weight)
    log_score, log_metadata = calculate_log_presence_score(incident)
    weighted_log = log_score * 0.25
    
    # 2. Keyword Detection Score (25% weight)
    keyword_score, detected_keywords = calculate_keyword_confidence(incident)
    weighted_keyword = keyword_score * 0.25
    
    # 3. Similar Incident Score (15% weight)
    similarity_score, max_similarity = calculate_similarity_confidence(incident)
    weighted_similarity = similarity_score * 0.15
    
    # 4. Data Completeness Score (15% weight)
    completeness_score = calculate_data_completeness_score(incident)
    weighted_completeness = completeness_score * 0.15
    
    # 5. Model Confidence (20% weight) - Only if reasonable
    if 0.3 <= model_confidence <= 0.8:
        weighted_model = model_confidence * 0.20
    else:
        # Ignore unreasonable model confidence
        weighted_model = 0.5 * 0.20  # Use neutral 0.5 instead
    
    # 6. Root Cause Found in Logs Bonus (+0.05)
    log_bonus = 0.05 if root_cause_found_in_logs else 0.0
    
    # Calculate final confidence
    final_confidence = (
        weighted_log +
        weighted_keyword +
        weighted_similarity +
        weighted_completeness +
        weighted_model +
        log_bonus
    )
    
    # Ensure 0.0-1.0 range
    final_confidence = max(0.0, min(1.0, final_confidence))
    
    # Build breakdown for transparency
    breakdown = {
        "final_confidence": final_confidence,
        "components": {
            "log_presence": {
                "score": log_score,
                "weighted": weighted_log,
                "metadata": log_metadata
            },
            "keyword_detection": {
                "score": keyword_score,
                "weighted": weighted_keyword,
                "keywords_found": detected_keywords
            },
            "similar_incidents": {
                "score": similarity_score,
                "weighted": weighted_similarity,
                "max_similarity": max_similarity
            },
            "data_completeness": {
                "score": completeness_score,
                "weighted": weighted_completeness
            },
            "model_confidence": {
                "raw": model_confidence,
                "weighted": weighted_model,
                "used": 0.3 <= model_confidence <= 0.8
            },
            "log_bonus": log_bonus
        }
    }
    
    return final_confidence, breakdown

