"""
Output validation and cleaning service for AI-generated text
"""
import re
import string


def is_garbage_text(text: str) -> bool:
    """
    Check if text appears to be garbage/nonsensical output from AI model
    """
    if not text or len(text.strip()) < 10:
        return True
    
    text_lower = text.lower()
    
    # Check for excessive special characters (more than 30% of text)
    special_chars = sum(1 for c in text if c not in string.ascii_letters + string.digits + ' .,!?;:-()[]')
    if len(text) > 0 and (special_chars / len(text)) > 0.3:
        return True
    
    # Check for patterns that indicate garbage
    garbage_patterns = [
        r'[*]{3,}',  # Multiple asterisks
        r'[#]{3,}',  # Multiple hashes
        r'[%]{2,}',  # Multiple percent signs
        r'[/]{3,}',  # Multiple slashes
        r'[\\]{2,}',  # Multiple backslashes
        r'[&]{2,}',  # Multiple ampersands
        r'[>]{2,}',  # Multiple greater than
        r'[<]{2,}',  # Multiple less than
        r'ROID ALG',  # Specific garbage pattern seen
        r'catifer-cain',  # Specific garbage pattern
        r'STARLS',  # Specific garbage pattern
        r'FALLAGE',  # Specific garbage pattern
        r'\[.*?\[.*?\[',  # Nested brackets (likely parsing error)
        r'[a-zA-Z]{20,}',  # Very long words (likely tokenization error)
    ]
    
    for pattern in garbage_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check if text has too many random characters
    # If more than 50% are non-alphanumeric (excluding spaces and common punctuation)
    alphanumeric = sum(1 for c in text if c.isalnum() or c.isspace())
    if len(text) > 0 and (alphanumeric / len(text)) < 0.5:
        return True
    
    # Check for repeated patterns (indicates model stuck in loop)
    words = text.split()
    if len(words) > 5:
        # Check if same word appears more than 30% of the time
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        max_count = max(word_counts.values()) if word_counts else 0
        if max_count / len(words) > 0.3:
            return True
    
    return False


def clean_text(text: str) -> str:
    """
    Clean and sanitize text output
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive special characters at start/end
    text = text.strip('*#%&<>[]()/\\')
    
    # Remove patterns that look like garbage
    text = re.sub(r'\[.*?mistake.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'ROID ALG.*?MySQL', 'MySQL', text, flags=re.IGNORECASE)
    text = re.sub(r'catifer-cain.*?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'STARLS.*?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'FALLAGE.*?', '', text, flags=re.IGNORECASE)
    
    # Remove excessive special characters in middle
    text = re.sub(r'[*#%]{3,}', '', text)
    text = re.sub(r'[/\\]{3,}', '', text)
    
    # Clean up quotes and special characters
    text = re.sub(r'["\']{2,}', '"', text)
    text = re.sub(r'[&]{2,}', '&', text)
    
    return text.strip()


def validate_and_clean_root_cause(text: str) -> str:
    """
    Validate and clean root cause text
    Returns cleaned text or empty string if garbage
    """
    if not text:
        return ""
    
    # Clean first
    cleaned = clean_text(text)
    
    # Check if still garbage after cleaning
    if is_garbage_text(cleaned):
        return ""
    
    # Additional validation: should be readable
    # Check if it has at least some normal words
    words = cleaned.split()
    normal_words = [w for w in words if any(c.isalpha() for c in w) and len(w) < 30]
    
    if len(normal_words) < 3:
        return ""
    
    # Limit length (root cause shouldn't be too long)
    if len(cleaned) > 500:
        cleaned = cleaned[:500] + "..."
    
    return cleaned


def extract_meaningful_content(text: str, incident_description: str = "") -> str:
    """
    Try to extract meaningful content from potentially garbled text
    Falls back to incident description if text is garbage
    """
    cleaned = clean_text(text)
    
    if is_garbage_text(cleaned):
        # Try to extract any meaningful parts
        # Look for common technical terms
        technical_terms = [
            'database', 'timeout', 'connection', 'pool', 'error', 'exception',
            'mysql', 'postgresql', 'redis', 'api', 'service', 'request',
            'failed', 'failure', 'crash', 'memory', 'cpu', 'disk'
        ]
        
        found_terms = []
        text_lower = text.lower()
        for term in technical_terms:
            if term in text_lower:
                found_terms.append(term)
        
        if found_terms:
            # Construct a simple root cause from found terms
            if 'database' in found_terms or 'mysql' in found_terms or 'postgresql' in found_terms:
                if 'timeout' in found_terms or 'connection' in found_terms:
                    return "Database connection timeout or pool exhaustion"
                return "Database-related issue"
            elif 'timeout' in found_terms:
                return "Service timeout or connection issue"
            elif 'error' in found_terms or 'exception' in found_terms:
                return "Application error or exception"
        
        # If nothing found, use incident description
        if incident_description:
            # Extract key phrases from description
            desc_lower = incident_description.lower()
            if 'database' in desc_lower:
                return "Database connectivity or performance issue"
            elif 'timeout' in desc_lower:
                return "Service timeout or unavailability"
            elif 'connection pool' in desc_lower or 'pool' in desc_lower:
                return "Connection pool exhaustion"
            elif 'error' in desc_lower:
                return "Application error or system failure"
        
        return "Root cause analysis in progress"
    
    return cleaned

