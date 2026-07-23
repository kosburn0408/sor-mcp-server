"""Tools for the Science of Reading MCP server.

Organized by domain:
  diagnostics.py   — Lexile analysis, Simple View evaluation
  remediation.py   — Instructional remediation cards (lookup table)
  decodability.py  — Anti-cueing decodability verifier
  standards.py     — CASE/JSON-LD standards alignment
  privacy.py       — FERPA PII sanitizer
"""

from src.tools.diagnostics import (
    analyze_lexile,
    evaluate_simple_view,
)
from src.tools.remediation import (
    get_instructional_remediation,
    list_available_remediations,
    get_bulk_remediations,
)
from src.tools.decodability import (
    verify_decodable_text,
)
from src.tools.standards import (
    align_standards_case,
)
from src.tools.privacy import (
    get_pii_manager,
    PrivacyAuditLogger,
    PIIManager,
)

__all__ = [
    # diagnostics
    "analyze_lexile",
    "evaluate_simple_view",
    # remediation
    "get_instructional_remediation",
    "list_available_remediations",
    "get_bulk_remediations",
    # decodability
    "verify_decodable_text",
    # standards
    "align_standards_case",
    # privacy
    "get_pii_manager",
    "PrivacyAuditLogger",
    "PIIManager",
]
