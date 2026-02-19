"""
Real confidence score calculator based on actual file data and incident information
Calculates confidence based on:
- Number and quality of log files
- Error patterns found in logs
- Completeness of incident information
- Similarity to past incidents
- Data quality indicators
"""
import re
from typing import Tuple


def calculate_log_quality_score(incident_logs) -> float:
    """
    Calculate confidence based on log file quality
    Returns score between 0.0 and 1.0
    """
    if not incident_logs.exists():
        return 0.0
    
    total_score = 0.0
    log_count = incident_logs.count()
    
    # Base score for having logs (0.3 max)
    if log_count > 0:
        total_score += min(0.3, log_count * 0.1)
    
    # Check processed logs
    processed_logs = incident_logs.filter(processed=True)
    processed_count = processed_logs.count()
    
    if processed_count > 0:
        # Quality score for processed logs (0.2 max)
        total_score += min(0.2, (processed_count / log_count) * 0.2)
    
    # Check for error patterns in logs (0.3 max)
    error_patterns = [
        r'error', r'exception', r'failed', r'failure', r'timeout',
        r'connection.*pool', r'database.*error', r'connection.*timeout'
    ]
    
    error_count = 0
    for log in processed_logs:
        content = (log.processed_content or "").lower()
        for pattern in error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                error_count += 1
                break  # Count each log only once
    
    if error_count > 0:
        total_score += min(0.3, (error_count / log_count) * 0.3)
    
    # Check log content size (0.2 max)
    total_content_size = sum(
        len(log.processed_content or "") 
        for log in processed_logs
    )
    
    if total_content_size > 1000:  # At least 1KB of content
        total_score += min(0.2, (total_content_size / 10000) * 0.2)
    
    return min(1.0, total_score)


def calculate_incident_completeness_score(incident) -> float:
    """
    Calculate confidence based on incident information completeness
    """
    score = 0.0
    
    # Title (0.1)
    if incident.title and len(incident.title.strip()) > 10:
        score += 0.1
    
    # Description (0.2)
    if incident.description:
        desc_len = len(incident.description.strip())
        if desc_len > 50:
            score += 0.2
        elif desc_len > 20:
            score += 0.1
    
    # Severity (0.1)
    if incident.severity:
        score += 0.1
    
    # Category (0.1)
    if incident.category:
        score += 0.1
    
    # Affected services (0.1)
    if incident.affected_services and len(incident.affected_services) > 0:
        score += 0.1
    
    # Assigned user (0.05)
    if incident.assigned_to:
        score += 0.05
    
    # Status (0.05)
    if incident.status:
        score += 0.05
    
    return min(1.0, score)


def calculate_similarity_confidence(incident) -> float:
    """
    Calculate confidence boost from similar past incidents
    """
    try:
        from incidents.services.similarity_service import find_similar_incidents_db
        
        similar = find_similar_incidents_db(incident.title, top_k=3)
        
        if not similar:
            return 0.0
        
        # Get highest similarity score
        max_similarity = max(score for _, score in similar)
        
        # Boost confidence if similar incidents found
        # High similarity (>0.7) = +0.15
        # Medium similarity (>0.5) = +0.10
        # Low similarity (>0.3) = +0.05
        
        if max_similarity > 0.7:
            return 0.15
        elif max_similarity > 0.5:
            return 0.10
        elif max_similarity > 0.3:
            return 0.05
        
        return 0.0
    except:
        return 0.0


def calculate_rule_based_confidence(incident) -> float:
    """
    Calculate confidence based on rule-based analysis success
    """
    try:
        from incidents.services.rule_based_analyzer import analyze_from_logs, analyze_from_description
        
        # Check if we can find root cause from logs
        logs = incident.logs.all()
        if logs.exists():
            log_analysis = analyze_from_logs(logs)
            if log_analysis:
                return 0.6  # High confidence when found in logs
        
        # Check if we can find from description
        if incident.description:
            desc_analysis = analyze_from_description(incident.description)
            if desc_analysis:
                return 0.5  # Medium confidence from description
        
        # Check title
        if incident.title:
            title_analysis = analyze_from_description(incident.title)
            if title_analysis:
                return 0.4  # Lower confidence from title only
        
        return 0.3  # Default low confidence
    except:
        return 0.3


def calculate_real_confidence(incident, root_cause_found_in_logs: bool = False) -> float:
    """
    Calculate real confidence score based on actual data quality
    
    Factors:
    1. Log file quality (40% weight)
    2. Incident completeness (20% weight)
    3. Similarity to past incidents (15% weight)
    4. Rule-based analysis success (15% weight)
    5. Root cause found in logs (10% weight)
    """
    logs = incident.logs.all()
    
    # 1. Log quality score (40% weight)
    log_score = calculate_log_quality_score(logs)
    weighted_log_score = log_score * 0.4
    
    # 2. Incident completeness (20% weight)
    completeness_score = calculate_incident_completeness_score(incident)
    weighted_completeness = completeness_score * 0.2
    
    # 3. Similarity confidence (15% weight)
    similarity_boost = calculate_similarity_confidence(incident)
    weighted_similarity = similarity_boost * 0.15
    
    # 4. Rule-based confidence (15% weight)
    rule_confidence = calculate_rule_based_confidence(incident)
    weighted_rule = rule_confidence * 0.15
    
    # 5. Root cause found in logs (10% weight)
    log_found_boost = 0.1 if root_cause_found_in_logs else 0.0
    
    # Total confidence
    total_confidence = (
        weighted_log_score +
        weighted_completeness +
        weighted_similarity +
        weighted_rule +
        log_found_boost
    )
    
    # Ensure between 0.0 and 1.0
    return max(0.0, min(1.0, total_confidence))


def get_confidence_explanation(incident) -> str:
    """
    Get human-readable explanation of confidence score
    """
    logs = incident.logs.all()
    log_count = logs.count()
    processed_count = logs.filter(processed=True).count()
    
    factors = []
    
    if log_count > 0:
        factors.append(f"{log_count} log file(s) uploaded")
        if processed_count > 0:
            factors.append(f"{processed_count} log(s) processed")
    
    if incident.description and len(incident.description) > 50:
        factors.append("Detailed incident description")
    
    if incident.category:
        factors.append("Category specified")
    
    if incident.affected_services:
        factors.append(f"{len(incident.affected_services)} affected service(s)")
    
    try:
        from incidents.services.similarity_service import find_similar_incidents_db
        similar = find_similar_incidents_db(incident.title, top_k=1)
        if similar:
            factors.append(f"Similar past incidents found (similarity: {similar[0][1]:.2f})")
    except:
        pass
    
    if factors:
        return "Confidence based on: " + ", ".join(factors)
    else:
        return "Confidence based on basic incident information"

