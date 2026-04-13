"""
Audit Logger Service
Collects timestamped log entries for the full execution trail.
"""

from datetime import datetime, timezone


class AuditLogger:
    def __init__(self):
        self._entries: list[dict] = []

    def log(self, service: str, message: str, level: str = "INFO", data: dict | None = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": level,
            "service": service,
            "message": message,
        }
        if data:
            entry["data"] = data
        self._entries.append(entry)

    def info(self, service: str, message: str, data: dict | None = None):
        self.log(service, message, "INFO", data)

    def debug(self, service: str, message: str, data: dict | None = None):
        self.log(service, message, "DEBUG", data)

    def warning(self, service: str, message: str, data: dict | None = None):
        self.log(service, message, "WARNING", data)

    def error(self, service: str, message: str, data: dict | None = None):
        self.log(service, message, "ERROR", data)

    def entries(self) -> list[dict]:
        return list(self._entries)
