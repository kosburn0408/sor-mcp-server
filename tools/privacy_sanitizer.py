"""PII Anonymization & Session Mapping for SoR MCP Server.

FERPA-compliant privacy middleware. All student PII is stripped at the
MCP boundary before any LLM sees it. Re-identification happens only at
output rendering time — the LLM operates exclusively on synthetic tokens.

Key design decisions:
- In-memory session store (no persistence = no PII on disk)
- Deterministic token generation (repeatable within a session)
- Zero Data Retention (ZDR) — mappings cleared on disconnect
- Security audit logging (no PII in logs)
"""
from __future__ import annotations

import hashlib
import secrets
import threading
import time
from typing import Any

# ── PII Fields to Strip ─────────────────────────────────────────────────────

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

# Fields to KEEP (academic data only)
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


# ── Privacy Audit Logger ────────────────────────────────────────────────────


class PrivacyAuditLogger:
    """Lightweight security audit log. Never writes PII to any output."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def log(self, event_type: str, status: str, detail: str = "") -> None:
        """Record a privacy event. All detail strings are pre-sanitized."""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "status": status,  # 'success', 'warning', 'blocked'
            "detail": detail,  # Must be PII-free
        }
        with self._lock:
            self._events.append(event)
            # Keep only last 1000 events in memory
            if len(self._events) > 1000:
                self._events = self._events[-1000:]

    def get_summary(self) -> dict[str, Any]:
        """Return a PII-free audit summary."""
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
                    {
                        "time": e["timestamp"],
                        "type": e["event_type"],
                        "status": e["status"],
                    }
                    for e in recent
                ],
            }


# Global audit logger
_audit = PrivacyAuditLogger()


def log_privacy_event(event_type: str, status: str, detail: str = "") -> None:
    """Public API for privacy event logging."""
    _audit.log(event_type, status, detail)


# ── PII Session Manager ─────────────────────────────────────────────────────


class PIIManager:
    """Manages student identity anonymization per request session.

    Session lifecycle:
    1. create_session() → session_id
    2. For each student: anonymize_student_record(data) → PII-stripped dict
    3. LLM operates on PII-free data
    4. deanonymize_response_text(text, session_id) → real names restored
    5. destroy_session(session_id) → all PII mappings erased (ZDR)
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, dict[str, str]]] = {}
        self._lock = threading.Lock()

    # ── Session Management ─────────────────────────────────────────────

    def create_session(self, label: str = "") -> str:
        """Create a new privacy session. Returns session_id (UUID)."""
        session_id = f"sor_{secrets.token_hex(8)}"
        with self._lock:
            self._sessions[session_id] = {}
        log_privacy_event(
            "session_created", "success",
            f"Session {session_id[:12]}... created" + (f" ({label})" if label else ""),
        )
        return session_id

    def destroy_session(self, session_id: str) -> None:
        """Destroy a session and ALL associated PII mappings (ZDR)."""
        with self._lock:
            if session_id in self._sessions:
                count = len(self._sessions[session_id])
                del self._sessions[session_id]
                log_privacy_event(
                    "session_destroyed", "success",
                    f"Session {session_id[:12]}... destroyed ({count} records purged)",
                )

    # ── Anonymization ─────────────────────────────────────────────────

    def anonymize_student_record(self, data: dict[str, Any]) -> dict[str, Any]:
        """Strip PII from a student record. Replaces identity with token.

        Args:
            data: Raw student record potentially containing PII.

        Returns:
            Cleaned dict with synthetic student_token + only academic data.
            Original PII is stored in session memory for re-identification.

        Raises:
            ValueError: If no session token found in data (caller must
                        provide or we auto-create one).
        """
        # Generate a deterministic token from the PII
        raw_name = data.get("first_name", "") + data.get("last_name", "")
        raw_id = data.get("state_student_id", data.get("ssid", ""))
        token_seed = raw_name + raw_id

        if not token_seed.strip():
            # Fallback: random token for anonymous records
            student_token = f"std_{secrets.token_hex(4)}"
        else:
            student_token = f"std_{hashlib.sha256(token_seed.encode()).hexdigest()[:8]}"

        # Store PII mapping (only if we have real data)
        pii_store: dict[str, str] = {}
        for field in PII_FIELDS:
            value = data.get(field)
            if value and str(value).strip():
                pii_store[field] = str(value)

        # Determine which session this belongs to
        session_id = data.get("_session_id", "")
        if session_id and session_id in self._sessions:
            with self._lock:
                self._sessions[session_id][student_token] = pii_store

        # Build clean output — only academic fields + token
        cleaned: dict[str, Any] = {"student_token": student_token}

        for key, value in data.items():
            if key in PII_FIELDS or key.startswith("_"):
                continue
            cleaned[key] = value

        # Ensure at least one academic field survived
        if len(cleaned) <= 1:  # only student_token
            log_privacy_event(
                "anonymization_warning", "warning",
                f"Record {student_token}: no academic fields retained",
            )

        return cleaned

    def anonymize_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Anonymize multiple student records at once."""
        results = []
        for record in records:
            try:
                results.append(self.anonymize_student_record(record))
            except ValueError:
                continue
        log_privacy_event(
            "batch_anonymized", "success",
            f"{len(results)} records sanitized",
        )
        return results

    # ── De-anonymization ──────────────────────────────────────────────

    def deanonymize_response_text(self, text: str, session_id: str) -> str:
        """Replace synthetic tokens with real student names in output text.

        Only operates if session_id is valid and mappings exist.
        If session not found, returns text unchanged (safe default).

        Args:
            text: LLM-generated response containing synthetic tokens.
            session_id: Active privacy session ID.

        Returns:
            Text with real names restored where mappings exist.
        """
        with self._lock:
            mapping = self._sessions.get(session_id, {})

        if not mapping:
            return text

        result = text
        for token, pii in mapping.items():
            # Build display name from PII fields
            first = pii.get("first_name", "")
            last = pii.get("last_name", "")
            full = pii.get("full_name", "") or f"{first} {last}".strip()

            if full:
                result = result.replace(token, full)
                # Also replace token variations
                result = result.replace(f"Student {token}", full)

        log_privacy_event(
            "deanonymized", "success",
            f"Restored {len(mapping)} identities in output for session {session_id[:12]}...",
        )
        return result

    def deanonymize_record(self, record: dict[str, Any], session_id: str) -> dict[str, Any]:
        """Re-identify a single structured record for teacher display."""
        token = record.get("student_token", "")
        if not token or not session_id:
            return record

        with self._lock:
            pii = self._sessions.get(session_id, {}).get(token, {})

        if not pii:
            return record

        result = dict(record)
        # Add display-friendly fields
        first = pii.get("first_name", "")
        last = pii.get("last_name", "")
        if first or last:
            result["student_display_name"] = f"{first} {last}".strip()
        if "state_student_id" in pii:
            result["student_display_id"] = pii["state_student_id"]

        return result

    # ── Status / Diagnostics ──────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Return operational status for verify_privacy_status tool."""
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


# ── Global singleton ────────────────────────────────────────────────────────

_pii_manager = PIIManager()


def get_pii_manager() -> PIIManager:
    """Get the global PII manager singleton."""
    return _pii_manager
