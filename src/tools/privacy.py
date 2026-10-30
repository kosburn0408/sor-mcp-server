"""Privacy/PII sanitizer for Science of Reading MCP server.

Data-minimization helper: removes known student identifiers before data is
passed to a language model.

- Named PII fields (names, IDs, contact details) are dropped and replaced by a
  pseudonymous token derived with a per-process secret key, so tokens cannot be
  recomputed from a class roster.
- Free-text fields are scrubbed of the student's name parts and of patterns
  that look like identifiers (long digit runs such as GTIDs, emails, phone
  numbers, dates).

Pattern-based scrubbing cannot catch every identifier (for example a
classmate's name typed into a note). It reduces risk; it does not make a
system FERPA-compliant on its own. Districts remain responsible for their own
privacy review and data agreements.
"""

from __future__ import annotations

import hashlib
import hmac
import re
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


_TOKEN_KEY = secrets.token_bytes(32)

_ID_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"), "[DATE_REDACTED]"),
    (re.compile(r"\b[A-Z]{2,3}-?\d{4,}\b"), "[ID_REDACTED]"),
    (re.compile(r"\b\d{6,}\b"), "[ID_REDACTED]"),
]


def scrub_text(text: str, names: list[str] | tuple[str, ...] = ()) -> tuple[str, list[str]]:
    """Remove a student's name parts and identifier-like patterns from text.

    Returns (scrubbed_text, list of redaction kinds applied).
    """
    applied: list[str] = []
    out = text
    parts = sorted({p for n in names for p in re.split(r"[\s,]+", str(n)) if len(p) >= 2}, key=len, reverse=True)
    for rx, repl in _ID_PATTERNS:
        if rx.search(out):
            out = rx.sub(repl, out)
            applied.append(repl.strip("[]").lower())
    for part in parts:
        rx = re.compile(r"\b" + re.escape(part) + r"\b", re.IGNORECASE)
        if rx.search(out):
            out = rx.sub("[STUDENT]", out)
            if "name" not in applied:
                applied.append("name")
    return out, applied


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
        raw_name = str(data.get("first_name", "")) + str(data.get("last_name", "")) + str(data.get("student_name", "")) + str(data.get("full_name", ""))
        raw_id = str(data.get("state_student_id", data.get("ssid", "")))
        token_seed = (raw_name + raw_id).strip().lower()

        if not token_seed:
            student_token = f"std_{secrets.token_hex(4)}"
        else:
            student_token = "std_" + hmac.new(_TOKEN_KEY, token_seed.encode(), hashlib.sha256).hexdigest()[:10]

        pii_store: dict[str, str] = {}
        for field in PII_FIELDS:
            value = data.get(field)
            if value and str(value).strip():
                pii_store[field] = str(value)

        session_id = data.get("_session_id", "")
        if session_id and session_id in self._sessions:
            with self._lock:
                self._sessions[session_id][student_token] = pii_store

        name_values = [v for k, v in pii_store.items() if "name" in k]
        cleaned: dict[str, Any] = {"student_token": student_token}
        redactions: list[str] = []

        for key, value in data.items():
            if key in PII_FIELDS or key.startswith("_"):
                continue
            if isinstance(value, str):
                value, applied = scrub_text(value, name_values)
                redactions.extend(applied)
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, str):
                        item, applied = scrub_text(item, name_values)
                        redactions.extend(applied)
                    new_list.append(item)
                value = new_list
            cleaned[key] = value

        if redactions:
            log_privacy_event("free_text_scrubbed", "success", ", ".join(sorted(set(redactions))))
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
            "limitations": (
                "Pattern-based scrubbing reduces but cannot eliminate identifiers in free text. "
                "This tool has not been independently audited; districts must complete their own "
                "FERPA/COPPA review before use with student data."
            ),
        }


_pii_manager = PIIManager()


def get_pii_manager() -> PIIManager:
    return _pii_manager


def sanitize_pii(data: dict[str, Any]) -> dict[str, Any]:
    """Sanitize student PII from a dictionary payload."""
    return get_pii_manager().anonymize_student_record(data)
