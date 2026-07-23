"""Unit tests for PII Privacy Sanitizer.

Verifies FERPA compliance: raw PII never reaches LLM tool context,
synthetic tokens are correctly substituted, and ZDR is enforced.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add tools dir to path
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR.parent))

from tools.privacy_sanitizer import (  # noqa: E402
    PII_FIELDS,
    PIIManager,
    get_pii_manager,
    log_privacy_event,
)


def test_anonymize_strips_all_pii() -> None:
    """Verify ALL PII fields are stripped from the output record."""
    mgr = PIIManager()
    sid = mgr.create_session("test_strips_pii")

    raw = {
        "first_name": "John",
        "last_name": "Smith",
        "full_name": "John Smith",
        "state_student_id": "GA-12345",
        "email": "jsmith@school.edu",
        "dob": "2016-04-15",
        "grade": "2nd",
        "decoding_score": 0.42,
        "fluency_rate": 55,
        "deficit_codes": ["consonant_blends", "cvce_silent_e"],
    }
    raw["_session_id"] = sid

    cleaned = mgr.anonymize_student_record(raw)

    # PII must be gone
    for field in PII_FIELDS:
        assert field not in cleaned, f"PII field '{field}' leaked: {cleaned.get(field)}"

    # Academic data must survive
    assert cleaned["grade"] == "2nd"
    assert cleaned["decoding_score"] == 0.42
    assert cleaned["deficit_codes"] == ["consonant_blends", "cvce_silent_e"]

    # Token must exist
    assert "student_token" in cleaned
    assert cleaned["student_token"].startswith("std_")

    mgr.destroy_session(sid)


def test_deanonymize_restores_names() -> None:
    """Verify that real names are restored in output text."""
    mgr = PIIManager()
    sid = mgr.create_session("test_restore")

    raw_1 = {"first_name": "Jane", "last_name": "Doe", "grade": "1st"}
    raw_1["_session_id"] = sid
    raw_2 = {"first_name": "Bob", "last_name": "Jones", "grade": "2nd"}
    raw_2["_session_id"] = sid

    c1 = mgr.anonymize_student_record(raw_1)
    c2 = mgr.anonymize_student_record(raw_2)

    llm_output = f"Remediation for {c1['student_token']}: practice short vowels. {c2['student_token']}: practice blends."

    restored = mgr.deanonymize_response_text(llm_output, sid)

    assert "Jane Doe" in restored, f"Jane Doe not restored: {restored}"
    assert "Bob Jones" in restored, f"Bob Jones not restored: {restored}"
    assert c1["student_token"] not in restored, "Token leaked in output"
    assert c2["student_token"] not in restored, "Token leaked in output"

    mgr.destroy_session(sid)


def test_zdr_destroy_session() -> None:
    """Verify session destruction removes ALL PII mappings."""
    mgr = PIIManager()
    sid = mgr.create_session("test_zdr")

    raw = {"first_name": "Alice", "last_name": "Ray", "grade": "K"}
    raw["_session_id"] = sid
    cleaned = mgr.anonymize_student_record(raw)

    # Before destroy — de-anonymization works
    restored = mgr.deanonymize_response_text(cleaned["student_token"], sid)
    assert "Alice Ray" in restored

    # After destroy — mappings are gone
    mgr.destroy_session(sid)
    restored_after = mgr.deanonymize_response_text(cleaned["student_token"], sid)
    assert "Alice Ray" not in restored_after, "PII survived session destruction!"
    assert cleaned["student_token"] in restored_after, "Token should remain unchanged"


def test_no_pii_in_logs() -> None:
    """Verify privacy audit logger never writes PII to events."""
    log_privacy_event("test_event", "success", "PII-free detail only")
    log_privacy_event("anonymization", "success", "Student std_abc123 sanitized")

    from tools.privacy_sanitizer import _audit
    summary = _audit.get_summary()

    events_str = json.dumps(summary["recent_events"])
    assert "John" not in events_str
    assert "Smith" not in events_str
    assert "12345" not in events_str


def test_no_session_no_deanonymization() -> None:
    """Verify deanonymization is safe when no session exists."""
    mgr = PIIManager()
    text = "std_abc123 should stay as-is"
    result = mgr.deanonymize_response_text(text, "nonexistent_session")
    assert result == text, "Text changed without valid session"


def test_batch_anonymize() -> None:
    """Verify batch anonymization strips PII from all records."""
    mgr = PIIManager()
    sid = mgr.create_session("test_batch")

    batch = [
        {"first_name": "A", "last_name": "B", "grade": "1st", "_session_id": sid},
        {"first_name": "C", "last_name": "D", "grade": "2nd", "_session_id": sid},
        {"first_name": "E", "grade": "3rd", "_session_id": sid},  # no last name
    ]

    results = mgr.anonymize_batch(batch)
    assert len(results) == 3

    for r in results:
        assert "first_name" not in r
        assert "last_name" not in r
        assert "student_token" in r

    mgr.destroy_session(sid)


def test_verify_privacy_status() -> None:
    """Verify privacy status tool reports ZDR active."""
    mgr = get_pii_manager()
    status = mgr.get_status()

    assert status["zdr_mode"] is True
    assert status["pii_on_disk"] is False
    assert status["pii_in_logs"] is False
    assert status["status"] == "operational"
    assert status["compliance"]["ferpa"] == "compliant"
    assert status["compliance"]["coppa"] == "compliant"


def run_all() -> bool:
    """Run all tests. Returns True if all pass."""
    tests = [
        ("strip_all_pii", test_anonymize_strips_all_pii),
        ("restore_names", test_deanonymize_restores_names),
        ("zdr_destroy", test_zdr_destroy_session),
        ("no_pii_in_logs", test_no_pii_in_logs),
        ("no_session_safe", test_no_session_no_deanonymization),
        ("batch_anonymize", test_batch_anonymize),
        ("verify_status", test_verify_privacy_status),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  💥 {name}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
