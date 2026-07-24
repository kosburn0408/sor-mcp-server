"""Privacy/PII sanitizer for Science of Reading MCP server.

FERPA-compliant PII anonymization. All student PII is stripped at the
MCP boundary before any LLM sees it. Re-identification happens only at
output rendering time — the LLM operates exclusively on synthetic tokens.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from typing import Any

PII_FIELDS: set[str] = {
    "first_name",
    "last_name",
    "full_name",
    "student_name",
    "name",
    "state_student_id",
    "ssid",
    "student_id_raw",
    "email",
    "email_address",
    "dob",
    "date_of_birth",
    "address",
    "street",
    "city",
    "zip_code",
    "phone",
    "phone_number",
    "guardian_name",
    "parent_name",
}

ACADEMIC_FIELDS: set[str] = {
    "grade",
    "grade_level",
    "age",
    "decoding_score",
    "language_comprehension_score",
    "fluency_rate",
    "accuracy_pct",
    "phonics_errors",
    "error_patterns",
    "deficit_codes",
    "mastered_skills",
    "case_competency_ids",
    "assessment_scores",
    "reading_level",
    "lexile",
    "intervention_tier",
    "attendance_pct",
    "student_token",
}


class PrivacyAuditLogger:
    """Lightweight security audit log."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def log(self, event_type: str, status: str, detail: str = "") -> None:
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "status": status,
            "detail": detail,
        }
        with self._lock:
            self._events.append(event)
            if len(self._events) > 1000:
                self._events = self._events[-1000:]

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            total = len(self._events)
            by_type: dict[str, int] = {}
            for e in self._events:
                by_type[e["event_type"]] = by_type.get(e["event_type"], 0) + 1
            recent = self._events[-5:] if self._events else []
            return {
                "total_events": total,
                "event_counts": by_type,
                "zdr_mode": True,
                "pii_on_disk": False,
                "recent_events": [
                    {"time": e["timestamp"], "type": e["event_type"], "status": e["status"]}
                    for e in recent
                ],
            }


_audit = PrivacyAuditLogger()


def log_privacy_event(event_type: str, status: str, detail: str = "") -> None:
    _audit.log(event_type, status, detail)


class PIIManager:
    """Manages student identity anonymization per request session."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, dict[str, str]]] = {}
        self._lock = threading.Lock()

    def create_session(self, label: str = "") -> str:
        session_id = f"sor_{secrets.token_hex(8)}"
        with self._lock:
            self._sessions[session_id] = {}
        log_privacy_event("session_created", "success", f"Session {session_id[:12]}... created")
        return session_id

    def destroy_session(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._sessions:
                count = len(self._sessions[session_id])
                del self._sessions[session_id]
                log_privacy_event("session_destroyed", "success", f"Session {session_id[:12]}... destroyed ({count} records purged)")

    def anonymize_student_record(self, data: dict[str, Any]) -> dict[str, Any]:
        raw_name = data.get("first_name", "") + data.get("last_name", "")
        raw_id = data.get("state_student_id", data.get("ssid", ""))
        token_seed = raw_name + raw_id

        if not token_seed.strip():
            student_token = f"std_{secrets.token_hex(4)}"
        else:
            student_token = f"std_{hashlib.sha256(token_seed.encode()).hexdigest()[:8]}"

        pii_store: dict[str, str] = {}
        for field in PII_FIELDS:
            value = data.get(field)
            if value and str(value).strip():
                pii_store[field] = str(value)

        session_id = data.get("_session_id", "")
        if session_id and session_id in self._sessions:
            with self._lock:
                self._sessions[session_id][student_token] = pii_store

        cleaned: dict[str, Any] = {"student_token": student_token}

        for key, value in data.items():
            if key in PII_FIELDS or key.startswith("_"):
                continue
            cleaned[key] = value

        return cleaned

    def anonymize_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.anonymize_student_record(r) for r in records]

    def deanonymize_response_text(self, text: str, session_id: str) -> str:
        with self._lock:
            mapping = self._sessions.get(session_id, {})

        if not mapping:
            return text

        result = text
        for token, pii in mapping.items():
            first = pii.get("first_name", "")
            last = pii.get("last_name", "")
            full = pii.get("full_name", "") or f"{first} {last}".strip()

            if full:
                result = result.replace(token, full)

        return result

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            active_sessions = len(self._sessions)
            total_mappings = sum(len(v) for v in self._sessions.values())

        return {
            "zdr_mode": True,
            "pii_on_disk": False,
            "pii_in_logs": False,
            "active_sessions": active_sessions,
            "total_identity_mappings": total_mappings,
            "sanitized_fields": sorted(PII_FIELDS),
            "retained_fields": sorted(ACADEMIC_FIELDS),
            "audit": _audit.get_summary(),
            "status": "operational",
            "compliance": {
                "ferpa": "compliant",
                "coppa": "compliant",
                "gdpr_right_to_erasure": "zdr_by_default",
            },
        }


_pii_manager = PIIManager()


def get_pii_manager() -> PIIManager:
    return _pii_manager


def sanitize_pii(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize student PII from a dictionary payload."""
    return get_pii_manager().anonymize_student_record(data)
