"""
Format explanation as bullet points based on incident data
"""
import re
from typing import List


def format_explanation_as_bullets(incident, root_cause: str, raw_explanation: str = "") -> str:
    """
    Format explanation as 5 bullet points based on incident data
    """
    bullets = []
    
    # Get incident data
    logs = incident.logs.filter(processed=True)
    description = incident.description or ""
    
    # Bullet 1: What happened (from root cause or description)
    if root_cause:
        bullets.append(f"• {root_cause}")
    elif description:
        # Extract first sentence from description
        first_sentence = description.split('.')[0].strip()
        if len(first_sentence) > 10:
            bullets.append(f"• {first_sentence}")
        else:
            bullets.append(f"• Incident occurred affecting {incident.get_severity_display().lower()} severity services")
    else:
        bullets.append(f"• {incident.title}")
    
    # Bullet 2: Why it happened (from logs or description)
    if logs.exists():
        # Check for specific error patterns
        all_log_content = ""
        for log in logs:
            all_log_content += (log.processed_content or "").lower()
        
        if 'pool' in all_log_content and 'exhausted' in all_log_content:
            bullets.append("• Connection pool was exhausted due to high concurrent request volume")
        elif 'timeout' in all_log_content:
            bullets.append("• Operations exceeded maximum timeout thresholds")
        elif 'connection' in all_log_content and 'error' in all_log_content:
            bullets.append("• Database/service connections failed or were unavailable")
        elif 'memory' in all_log_content:
            bullets.append("• System memory resources were insufficient for the workload")
        else:
            bullets.append("• Error patterns detected in system logs indicate service degradation")
    elif description:
        desc_lower = description.lower()
        if 'pool' in desc_lower:
            bullets.append("• Connection pool resources were insufficient for concurrent load")
        elif 'timeout' in desc_lower:
            bullets.append("• Service operations exceeded configured timeout limits")
        elif 'error' in desc_lower or 'exception' in desc_lower:
            bullets.append("• Application errors or exceptions occurred during operation")
        else:
            bullets.append("• System encountered an unexpected failure condition")
    else:
        bullets.append("• Root cause analysis indicates system-level issue")
    
    # Bullet 3: Impact (from incident data)
    if incident.affected_services:
        services = ', '.join(incident.affected_services[:3])
        bullets.append(f"• Affected services: {services}")
    elif description:
        # Try to extract impact from description
        desc_lower = description.lower()
        if 'degradation' in desc_lower or 'degraded' in desc_lower:
            bullets.append("• Service performance degradation observed")
        elif 'down' in desc_lower or 'unavailable' in desc_lower:
            bullets.append("• Services became unavailable or unresponsive")
        elif 'slow' in desc_lower or 'latency' in desc_lower:
            bullets.append("• Increased latency and slow response times")
        else:
            bullets.append(f"• Impact severity: {incident.get_severity_display()}")
    else:
        bullets.append(f"• Impact severity: {incident.get_severity_display()}")
    
    # Bullet 4: Detection/Evidence (from logs)
    if logs.exists():
        log_count = logs.count()
        bullets.append(f"• Detected through analysis of {log_count} log file(s) with error patterns")
    elif description:
        bullets.append("• Incident detected through monitoring or user reports")
    else:
        bullets.append("• Incident reported and logged for investigation")
    
    # Bullet 5: Resolution/Mitigation (generic or from status)
    if incident.status in ['resolved', 'closed']:
        bullets.append("• Incident has been resolved and services restored")
    elif incident.status == 'mitigating':
        bullets.append("• Mitigation steps are currently being applied")
    else:
        # Suggest mitigation based on root cause
        root_lower = root_cause.lower() if root_cause else ""
        if 'pool' in root_lower or 'connection' in root_lower:
            bullets.append("• Recommended: Increase connection pool size and optimize connection management")
        elif 'timeout' in root_lower:
            bullets.append("• Recommended: Review timeout configurations and optimize slow queries")
        elif 'memory' in root_lower:
            bullets.append("• Recommended: Increase memory allocation and investigate memory leaks")
        else:
            bullets.append("• Recommended: Review system configuration and implement preventive measures")
    
    # Ensure exactly 5 bullets
    while len(bullets) < 5:
        bullets.append("• Additional analysis in progress")
    
    # Limit to 5 bullets
    bullets = bullets[:5]
    
    return "\n".join(bullets)


def format_root_cause_one_line(root_cause: str) -> str:
    """
    Ensure root cause is one concise line
    """
    if not root_cause:
        return "Root cause analysis in progress"
    
    # Remove newlines and extra spaces
    root_cause = re.sub(r'\s+', ' ', root_cause.strip())
    
    # Take first sentence if multiple sentences
    sentences = root_cause.split('.')
    if len(sentences) > 1:
        root_cause = sentences[0].strip()
        if not root_cause.endswith('.'):
            root_cause += '.'
    
    # Limit length to reasonable one-line size
    if len(root_cause) > 150:
        root_cause = root_cause[:147] + "..."
    
    return root_cause

