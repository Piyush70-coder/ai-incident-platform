from collections import defaultdict
from django.utils.timezone import localtime
import re


def _get_event_time(event):
    return (
        getattr(event, "timestamp", None)
        or getattr(event, "logged_at", None)
        or getattr(event, "uploaded_at", None)
        or getattr(event, "created_at", None)
    )


def _extract_lines(log):
    """
    Extract individual log lines from IncidentLog
    """
    if getattr(log, "processed_content", None):
        return log.processed_content.splitlines()
    return []


def _guess_level(line: str) -> str:
    if "ERROR" in line.upper():
        return "ERROR"
    if "WARN" in line.upper():
        return "WARN"
    if "INFO" in line.upper():
        return "INFO"
    return ""


def _guess_service(line: str) -> str:
    """
    Guess service name from log line [service-name]
    """
    match = re.search(r"\[(.*?)\]", line)
    return match.group(1) if match else "unknown"


def build_timeline(logs):
    """
    Build timeline from file-based logs
    """
    timeline = []

    for log in logs:
        event_time = _get_event_time(log)
        lines = _extract_lines(log)

        for line in lines:
            level = _guess_level(line)
            if not level:
                continue  # skip noise

            timeline.append({
                "time": localtime(event_time).isoformat() if event_time else "unknown",
                "service": _guess_service(line),
                "level": level,
                "message": line[:300]
            })

    return timeline[:50]


def detect_first_failure(logs):
    for log in logs:
        event_time = _get_event_time(log)
        for line in _extract_lines(log):
            if "ERROR" in line.upper():
                return {
                    "time": localtime(event_time).isoformat() if event_time else "unknown",
                    "service": _guess_service(line),
                    "message": line[:300]
                }
    return None


def detect_error_spikes(logs, threshold=3):
    error_count = defaultdict(int)

    for log in logs:
        for line in _extract_lines(log):
            if "ERROR" in line.upper():
                service = _guess_service(line)
                error_count[service] += 1

    return [
        {"service": svc, "error_count": cnt}
        for svc, cnt in error_count.items()
        if cnt >= threshold
    ]
