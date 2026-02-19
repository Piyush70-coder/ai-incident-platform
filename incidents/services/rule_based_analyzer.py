"""
Rule-based incident analyzer as fallback when AI fails
Analyzes logs and incident description to provide meaningful root cause
"""
import re
from typing import Optional


def analyze_from_logs(incident_logs) -> Optional[str]:
    """
    Analyze logs to find root cause using pattern matching
    """
    error_patterns = {
        'database_pool_exhausted': [
            r'connection pool.*exhausted',
            r'pool.*exhausted',
            r'could not obtain connection.*pool',
            r'pool.*timeout',
        ],
        'database_timeout': [
            r'database.*timeout',
            r'db.*timeout',
            r'connection.*timeout',
            r'mysql.*timeout',
            r'postgresql.*timeout',
        ],
        'database_connection_error': [
            r'database.*error',
            r'connection.*error',
            r'db.*connection.*failed',
            r'psycopg2.*error',
            r'mysql.*error',
        ],
        'service_timeout': [
            r'service.*timeout',
            r'request.*timeout',
            r'operation.*timeout',
            r'timed out',
        ],
        'memory_error': [
            r'out of memory',
            r'memory.*error',
            r'oom',
            r'memory.*exhausted',
        ],
        'disk_space': [
            r'disk.*full',
            r'no space.*device',
            r'disk.*error',
        ],
        # --- YEH WALA ADD KARO ---
        'configuration_error': [
            r'misconfigured', r'configuration.*error', r'health.*check.*failed',
            r'404.*health', r'target.*unhealthy'
        ],
        # -------------------------

        'database_issue': [r'connection.*refused', r'deadlock', r'too many clients'],
        # ... baaki patterns ...
    }
    
    all_log_content = ""
    for log in incident_logs:
        content = (log.processed_content or "").lower()
        all_log_content += content + "\n"
    
    # Check each pattern
    for cause_type, patterns in error_patterns.items():
        for pattern in patterns:
            if re.search(pattern, all_log_content, re.IGNORECASE):
                if cause_type == 'database_pool_exhausted':
                    return "Too many database connections were being used at the same time, causing the connection pool to run out"
                elif cause_type == 'database_timeout':
                    return "The database took too long to respond, causing connection timeouts"
                elif cause_type == 'database_connection_error':
                    return "The system could not connect to the database due to a connectivity or configuration issue"
                elif cause_type == 'service_timeout':
                    return "Service operations took longer than the maximum allowed time and timed out"
                elif cause_type == 'memory_error':
                    return "The system ran out of available memory to process requests"
                elif cause_type == 'disk_space':
                    return "The system ran out of storage space, preventing normal operations"
    
    return None


def analyze_from_description(description: str) -> Optional[str]:
    """
    Analyze incident description to infer root cause
    """
    if not description:
        return None
    
    desc_lower = description.lower()
    
    # Database-related
    if any(term in desc_lower for term in ['database', 'db', 'mysql', 'postgresql', 'postgres']):
        if 'pool' in desc_lower or 'exhausted' in desc_lower:
            return "Too many database connections were being used at the same time"
        elif 'timeout' in desc_lower or 'connection timeout' in desc_lower:
            return "The database took too long to respond to connection requests"
        elif 'connection' in desc_lower:
            return "The system had trouble connecting to the database"
        else:
            return "A database performance or configuration issue occurred"
    
    # Connection pool
    if 'connection pool' in desc_lower or ('pool' in desc_lower and 'connection' in desc_lower):
        if 'exhausted' in desc_lower:
            return "All available database connections were in use, and new requests could not get a connection"
        return "The database connection pool settings need to be adjusted for the current load"
    
    # Timeout
    if 'timeout' in desc_lower:
        if 'database' in desc_lower:
            return "Database operations took too long and timed out"
        elif 'service' in desc_lower:
            return "Service operations exceeded the time limit and timed out"
        return "Requests or operations took too long and timed out"
    
    # Error/Exception
    if 'error' in desc_lower or 'exception' in desc_lower:
        if 'database' in desc_lower:
            return "A database error occurred that prevented normal operation"
        return "An application error occurred that disrupted service"
    
    # Memory
    if 'memory' in desc_lower:
        return "The system ran out of memory, possibly due to a memory leak or insufficient memory allocation"
    
    # Network
    if any(term in desc_lower for term in ['network', 'dns', 'connection refused']):
        return "A network connectivity issue prevented services from communicating"
    
    return None


def get_rule_based_root_cause(incident) -> tuple[str, float]:
    """
    Get root cause using rule-based analysis
    Returns (root_cause, confidence)
    Ensures root cause is one line
    """
    from incidents.services.explanation_formatter import format_root_cause_one_line
    
    # Try logs first (higher confidence)
    logs = incident.logs.all()
    if logs.exists():
        log_analysis = analyze_from_logs(logs)
        if log_analysis:
            # Format as one line
            formatted = format_root_cause_one_line(log_analysis)
            return formatted, 0.6
    
    # Try description (medium confidence)
    if incident.description:
        desc_analysis = analyze_from_description(incident.description)
        if desc_analysis:
            formatted = format_root_cause_one_line(desc_analysis)
            return formatted, 0.5
    
    # Try title
    if incident.title:
        title_analysis = analyze_from_description(incident.title)
        if title_analysis:
            formatted = format_root_cause_one_line(title_analysis)
            return formatted, 0.4
    
    # Default fallback
    return "We are still analyzing the root cause of this incident and reviewing the details", 0.3

