"""Tools for the Science of Reading MCP server.

Organized by domain:
  diagnostics.py   — Lexile analysis, Simple View evaluation
  remediation.py   — Instructional remediation cards (lookup table)
  decodability.py  — Anti-cueing decodability verifier (API + DuckDB)
  standards.py     — CASE/JSON-LD standards alignment + API competency lookup
  privacy.py       — FERPA PII sanitizer
  phonics.py       — API: get_phonics_scope
  orthography.py   — API: map_orthography
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
    lookup_competency,
)
from src.tools.privacy import (
    get_pii_manager,
    PrivacyAuditLogger,
    PIIManager,
)
from src.tools.phonics import (
    get_phonics_scope,
)
from src.tools.orthography import (
    map_orthography,
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
    "lookup_competency",
    # privacy
    "get_pii_manager",
    "PrivacyAuditLogger",
    "PIIManager",
    # API bridge tools
    "get_phonics_scope",
    "map_orthography",
]
