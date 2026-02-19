"""
Log processing service to extract and process log file contents
"""
import os
import zipfile
import tarfile
import gzip
from typing import Optional


def extract_log_content(log_file) -> str:
    """
    Extract text content from log file.
    Supports: .txt, .log, .zip, .tar.gz, .gz
    """
    content = ""
    file_path = log_file.path if hasattr(log_file, 'path') else None
    
    # If it's a file path, read from disk
    if file_path and os.path.exists(file_path):
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext in ['.zip']:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Extract first file from zip
                    file_list = zip_ref.namelist()
                    if file_list:
                        content = zip_ref.read(file_list[0]).decode('utf-8', errors='ignore')
            
            elif file_ext in ['.gz', '.tar.gz']:
                if file_path.endswith('.tar.gz'):
                    with tarfile.open(file_path, 'r:gz') as tar:
                        # Extract first file from tar
                        members = tar.getmembers()
                        if members:
                            file_obj = tar.extractfile(members[0])
                            if file_obj:
                                content = file_obj.read().decode('utf-8', errors='ignore')
                else:
                    with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
            
            else:
                # Plain text file (.txt, .log, etc.)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
        
        except Exception as e:
            # Fallback: try reading as binary then decode
            try:
                with open(file_path, 'rb') as f:
                    raw = f.read()
                    content = raw.decode('utf-8', errors='ignore')
            except:
                content = f"Error reading log file: {str(e)}"
    
    # If it's a file object (Django FileField), read directly
    elif hasattr(log_file, 'read'):
        try:
            log_file.seek(0)
            content = log_file.read().decode('utf-8', errors='ignore')
        except:
            try:
                log_file.seek(0)
                content = str(log_file.read())
            except Exception as e:
                content = f"Error reading log: {str(e)}"
    
    return content


def process_log_file(incident_log) -> str:
    """
    Process an IncidentLog instance and return extracted content.
    Also extracts key information like errors, timestamps, etc.
    """
    content = extract_log_content(incident_log.file)
    
    if not content:
        return ""
    
    # Extract key information
    lines = content.split('\n')
    error_lines = []
    warning_lines = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'failure', 'fatal']):
            error_lines.append(line[:200])  # Truncate long lines
        elif any(keyword in line_lower for keyword in ['warn', 'warning', 'critical']):
            warning_lines.append(line[:200])
    
    # Build processed content with key information
    processed = content[:5000]  # Keep first 5000 chars
    
    if error_lines:
        processed += "\n\n=== KEY ERRORS ===\n" + "\n".join(error_lines[:20])
    
    if warning_lines:
        processed += "\n\n=== KEY WARNINGS ===\n" + "\n".join(warning_lines[:10])
    
    return processed


def extract_key_errors(log_content: str, max_errors: int = 10) -> list:
    """
    Extract key error messages from log content
    """
    errors = []
    lines = log_content.split('\n')
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in ['error', 'exception', 'failed', 'failure', 'fatal', 'timeout']):
            # Clean up the line
            clean_line = line.strip()[:300]  # Max 300 chars per error
            if clean_line and clean_line not in errors:
                errors.append(clean_line)
                if len(errors) >= max_errors:
                    break
    
    return errors

