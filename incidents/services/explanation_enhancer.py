"""
SRE-quality explanation enhancer
Ensures explanations are tightly coupled to root cause and explain:
- which component failed
- why it failed
- how the failure propagated
- why users were impacted
"""
import re
from typing import Optional


def enhance_explanation(incident, root_cause: str, raw_explanation: str = "") -> str:
    """
    Enhance explanation to be SRE-quality, tightly coupled to root cause
    """
    if not root_cause:
        return "Explanation will be provided once root cause analysis is complete."
    
    root_lower = root_cause.lower()
    description = (incident.description or "").lower()
    logs = incident.logs.filter(processed=True)
    
    # Build explanation parts
    parts = []
    
    # 1. Which component failed
    component = None
    if 'database' in root_lower or 'db' in root_lower:
        component = 'database'
    elif 'redis' in root_lower or 'cache' in root_lower:
        component = 'redis/cache system'
    elif 'kafka' in root_lower or 'queue' in root_lower:
        component = 'Kafka message queue'
    elif 'api' in root_lower or 'service' in root_lower:
        component = 'API service'
    elif 'connection' in root_lower:
        component = 'connection layer'
    elif 'timeout' in root_lower:
        component = 'service operation'
    elif 'memory' in root_lower:
        component = 'memory subsystem'
    
    if component:
        parts.append(f"The {component} failed.")
    else:
        parts.append("A system component failed.")
    
    # 2. Why it failed
    why_failed = None
    
    # Check logs for why
    all_log_content = ""
    for log in logs:
        all_log_content += (log.processed_content or "").lower()
    
    if 'pool' in root_lower and 'exhausted' in root_lower:
        why_failed = "The connection pool was exhausted because too many concurrent requests tried to use connections simultaneously, exceeding the configured pool size."
    elif 'timeout' in root_lower:
        if 'database' in root_lower:
            why_failed = "Database operations took longer than the configured timeout threshold, likely due to slow queries, high load, or resource contention."
        else:
            why_failed = "Operations exceeded the maximum allowed time limit, causing requests to timeout."
    elif 'connection' in root_lower and 'error' in root_lower:
        why_failed = "The system could not establish or maintain connections, possibly due to network issues, configuration problems, or the target service being unavailable."
    elif 'redis' in root_lower or 'cache' in root_lower:
        why_failed = "The cache system became unavailable or unresponsive, possibly due to memory pressure, network issues, or service restart."
    elif 'kafka' in root_lower:
        why_failed = "The message queue system failed to process messages, possibly due to broker unavailability, consumer lag, or partition issues."
    elif 'memory' in root_lower:
        why_failed = "The system ran out of available memory, possibly due to a memory leak, insufficient allocation, or excessive memory usage by processes."
    else:
        # Try to infer from description or logs
        if 'concurrent' in description or 'high load' in description:
            why_failed = "The system was unable to handle the concurrent request volume or load."
        elif 'configuration' in description:
            why_failed = "A configuration issue prevented the system from operating correctly."
        else:
            why_failed = "The component encountered an error condition that prevented normal operation."
    
    if why_failed:
        parts.append(why_failed)
    
    # 3. How the failure propagated
    if component:
        if component == 'database':
            parts.append("This caused all database-dependent services to fail or degrade, as they could not retrieve or store data.")
        elif component == 'redis/cache system':
            parts.append("This forced services to fall back to slower database queries, causing increased latency and potential database overload.")
        elif component == 'Kafka message queue':
            parts.append("This caused message processing to stall, leading to data processing delays and potential data loss.")
        elif component == 'API service':
            parts.append("This caused API endpoints to become unavailable or slow, directly impacting user requests.")
        else:
            parts.append("This failure propagated to dependent services, causing cascading issues.")
    
    # 4. Why users were impacted
    severity = incident.get_severity_display().lower()
    affected_services = incident.affected_services or []
    
    if affected_services:
        services_str = ', '.join(affected_services[:3])
        parts.append(f"Users were impacted because {services_str} became unavailable or degraded, affecting their ability to use the system.")
    elif severity == 'critical':
        parts.append("Users were severely impacted as critical services became unavailable, preventing core functionality.")
    elif severity == 'high':
        parts.append("Users experienced significant service degradation, with many requests failing or timing out.")
    else:
        parts.append("Users experienced service issues that affected their experience, though the impact was limited.")
    
    return " ".join(parts)


def is_generic_explanation(explanation: str) -> bool:
    """
    Check if explanation is too generic
    """
    if not explanation:
        return True
    
    explanation_lower = explanation.lower()
    
    generic_phrases = [
        'system was slow',
        'took longer than expected',
        'something went wrong',
        'an error occurred',
        'issue happened',
        'problem occurred'
    ]
    
    return any(phrase in explanation_lower for phrase in generic_phrases)

