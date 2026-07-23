"""Privacy/PII sanitizer for Science of Reading MCP server.

Ported from tools/privacy_sanitizer.py — FERPA-compliant PII anonymization.
All student PII is stripped at the MCP boundary. Zero Data Retention (ZDR).
"""

from tools.privacy_sanitizer import (
    PII_FIELDS,
    ACADEMIC_FIELDS,
    PrivacyAuditLogger,
    PIIManager,
    get_pii_manager,
    log_privacy_event,
)

__all__ = [
    "PII_FIELDS",
    "ACADEMIC_FIELDS",
    "PrivacyAuditLogger",
    "PIIManager",
    "get_pii_manager",
    "log_privacy_event",
]
