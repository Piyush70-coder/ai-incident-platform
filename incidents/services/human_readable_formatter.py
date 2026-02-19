"""
Human-readable text formatter
Converts technical jargon into plain, understandable language
"""
import re
from typing import Dict


# Technical term to human-readable translations
TECHNICAL_TO_SIMPLE = {
    # Database terms
    'connection pool exhausted': 'too many database connections were being used at the same time',
    'connection pool': 'database connection limit',
    'pool exhausted': 'all available connections were in use',
    'database timeout': 'database took too long to respond',
    'connection timeout': 'connection attempt took too long',
    'database connection error': 'could not connect to the database',
    'psycopg2': 'database driver',
    'mysql': 'database',
    'postgresql': 'database',
    'postgres': 'database',
    
    # Cache/Redis terms
    'redis': 'cache system',
    'cache failure': 'cache system stopped working',
    'cache miss': 'requested data not found in cache',
    'cache timeout': 'cache took too long to respond',
    
    # Kafka terms
    'kafka': 'message queue system',
    'kafka consumer': 'message processor',
    'kafka producer': 'message sender',
    'broker': 'message queue server',
    
    # General terms
    'concurrent requests': 'multiple requests happening at the same time',
    'request volume': 'number of requests',
    'service degradation': 'service became slow or unreliable',
    'service unavailable': 'service stopped working',
    'latency': 'response time',
    'throughput': 'number of requests processed',
    'memory exhaustion': 'ran out of available memory',
    'oom': 'out of memory',
    'heap': 'memory space',
    'disk space': 'storage space',
    'no space': 'storage is full',
    
    # Error terms
    'exception': 'error',
    'fatal error': 'critical error that stopped the service',
    'error pattern': 'repeated errors',
}


def simplify_technical_terms(text: str) -> str:
    """
    Replace technical jargon with simple, human-readable terms
    """
    if not text:
        return text
    
    text_lower = text.lower()
    simplified = text
    
    # Replace technical terms (longer phrases first)
    for technical, simple in sorted(TECHNICAL_TO_SIMPLE.items(), key=len, reverse=True):
        pattern = re.compile(re.escape(technical), re.IGNORECASE)
        simplified = pattern.sub(simple, simplified)
    
    return simplified


def make_sentence_natural(sentence: str) -> str:
    """
    Make a sentence more natural and conversational
    """
    if not sentence:
        return sentence
    
    # Remove redundant phrases
    sentence = re.sub(r'\b(due to the fact that|because of the fact that)\b', 'because', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\b(in order to)\b', 'to', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\b(utilize|utilization)\b', 'use', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\b(commence)\b', 'start', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\b(terminate)\b', 'stop', sentence, flags=re.IGNORECASE)
    sentence = re.sub(r'\b(encounter)\b', 'face', sentence, flags=re.IGNORECASE)
    
    # Fix common issues
    sentence = re.sub(r'\s+', ' ', sentence)  # Multiple spaces
    sentence = sentence.strip()
    
    # Ensure sentence starts with capital and ends with period
    if sentence:
        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
        if not sentence.endswith(('.', '!', '?')):
            sentence += '.'
    
    return sentence


def format_root_cause_human_readable(root_cause: str) -> str:
    """
    Format root cause in human-readable, simple language
    """
    if not root_cause:
        return "We are still analyzing the root cause of this incident."
    
    # Simplify technical terms
    simplified = simplify_technical_terms(root_cause)
    
    # Make it natural
    simplified = make_sentence_natural(simplified)
    
    # Ensure it's one clear sentence
    sentences = simplified.split('.')
    if len(sentences) > 1:
        # Take the first complete sentence
        simplified = sentences[0].strip()
        if simplified:
            simplified += '.'
        else:
            simplified = sentences[1].strip() + '.' if len(sentences) > 1 else simplified
    
    # Limit length
    if len(simplified) > 200:
        simplified = simplified[:197] + "..."
    
    # Final cleanup
    simplified = re.sub(r'\s+', ' ', simplified).strip()
    
    return simplified if simplified else "We are still analyzing the root cause of this incident."


def format_explanation_human_readable(incident, root_cause: str) -> str:
    """
    Format explanation in human-readable bullet points
    """
    bullets = []
    logs = incident.logs.filter(processed=True)
    description = incident.description or ""
    
    # Bullet 1: What happened (simple, clear)
    if root_cause:
        # Simplify root cause for first bullet
        simple_cause = simplify_technical_terms(root_cause)
        simple_cause = make_sentence_natural(simple_cause)
        # Remove period for bullet point
        simple_cause = simple_cause.rstrip('.')
        bullets.append(f"• {simple_cause}")
    elif description:
        first_sentence = description.split('.')[0].strip()
        if len(first_sentence) > 10:
            simple_desc = simplify_technical_terms(first_sentence)
            simple_desc = make_sentence_natural(simple_desc)
            simple_desc = simple_desc.rstrip('.')
            bullets.append(f"• {simple_desc}")
        else:
            severity = incident.get_severity_display().lower()
            bullets.append(f"• A {severity} severity incident occurred that affected our services")
    else:
        bullets.append(f"• An incident occurred: {incident.title}")
    
    # Bullet 2: Why it happened (explain in simple terms)
    if logs.exists():
        all_log_content = ""
        for log in logs:
            all_log_content += (log.processed_content or "").lower()
        
        if 'pool' in all_log_content and 'exhausted' in all_log_content:
            bullets.append("• Too many requests tried to use the database at the same time, and we ran out of available connections")
        elif 'timeout' in all_log_content:
            bullets.append("• The system took longer than expected to respond, causing requests to time out")
        elif 'connection' in all_log_content and 'error' in all_log_content:
            bullets.append("• The system could not establish or maintain connections to required services")
        elif 'memory' in all_log_content or 'oom' in all_log_content:
            bullets.append("• The system ran out of available memory to process requests")
        elif 'redis' in all_log_content or 'cache' in all_log_content:
            bullets.append("• The cache system (Redis) failed or became unavailable, causing slower responses")
        elif 'kafka' in all_log_content:
            bullets.append("• The message queue system (Kafka) had issues processing messages")
        else:
            bullets.append("• Error patterns were found in the system logs indicating a service problem")
    elif description:
        desc_lower = description.lower()
        if 'pool' in desc_lower and 'exhausted' in desc_lower:
            bullets.append("• Too many database connections were being used simultaneously")
        elif 'timeout' in desc_lower:
            bullets.append("• Operations took longer than the allowed time limit")
        elif 'error' in desc_lower or 'exception' in desc_lower:
            bullets.append("• Application errors occurred during normal operation")
        elif 'redis' in desc_lower or 'cache' in desc_lower:
            bullets.append("• The cache system stopped working properly")
        else:
            bullets.append("• The system encountered an unexpected failure")
    else:
        bullets.append("• The root cause analysis indicates a system-level issue occurred")
    
    # Bullet 3: Impact (what was affected)
    if incident.affected_services:
        services = ', '.join(incident.affected_services[:3])
        bullets.append(f"• This incident affected the following services: {services}")
    elif description:
        desc_lower = description.lower()
        if 'degradation' in desc_lower or 'degraded' in desc_lower:
            bullets.append("• Service performance became slower and less reliable")
        elif 'down' in desc_lower or 'unavailable' in desc_lower:
            bullets.append("• Services became unavailable and users could not access them")
        elif 'slow' in desc_lower or 'latency' in desc_lower:
            bullets.append("• Services responded much slower than usual")
        else:
            severity = incident.get_severity_display()
            bullets.append(f"• Impact level: {severity} - This affected service availability")
    else:
        severity = incident.get_severity_display()
        bullets.append(f"• Impact level: {severity}")
    
    # Bullet 4: How we detected it
    if logs.exists():
        log_count = logs.count()
        if log_count == 1:
            bullets.append(f"• We detected this issue by analyzing {log_count} log file that contained error messages")
        else:
            bullets.append(f"• We detected this issue by analyzing {log_count} log files that contained error patterns")
    elif description:
        bullets.append("• This incident was detected through our monitoring systems or user reports")
    else:
        bullets.append("• This incident was reported and logged for investigation")
    
    # Bullet 5: What we're doing about it
    if incident.status in ['resolved', 'closed']:
        bullets.append("• This incident has been resolved and all services are back to normal")
    elif incident.status == 'mitigating':
        bullets.append("• We are currently applying fixes to resolve this issue")
    else:
        # Suggest action in simple terms
        root_lower = root_cause.lower() if root_cause else ""
        if 'pool' in root_lower or 'connection' in root_lower:
            bullets.append("• Recommended action: Increase the number of available database connections and optimize how connections are managed")
        elif 'timeout' in root_lower:
            bullets.append("• Recommended action: Review timeout settings and optimize slow database queries or operations")
        elif 'memory' in root_lower:
            bullets.append("• Recommended action: Increase memory allocation and investigate potential memory leaks")
        elif 'redis' in root_lower or 'cache' in root_lower:
            bullets.append("• Recommended action: Check Redis/cache configuration and ensure proper failover mechanisms are in place")
        elif 'kafka' in root_lower:
            bullets.append("• Recommended action: Review Kafka broker configuration and check message processing rates")
        else:
            bullets.append("• Recommended action: Review system configuration and implement preventive measures to avoid similar issues")
    
    # Ensure exactly 5 bullets
    while len(bullets) < 5:
        bullets.append("• Additional analysis is in progress")
    
    bullets = bullets[:5]
    
    return "\n".join(bullets)

