"""EPIC-SOR-01 Verification Suite — Stories 1 through 6.

Verifies:
  - Story 1: Task-Based Workspace Architecture & Scope Fetching (< 200ms)
  - Story 2: Decodable Inspector, Word Badges & Anti-Cueing Audit
  - Story 3: Print-First CSS & Export Utilities (@media print, Atkinson Hyperlegible)
  - Story 4: Georgia HB 538 MTSS Remediation & 1EdTech CASE® Rosetta Mapping
  - Story 5: FERPA Privacy Shield & Client/Server PII Scrubbing
  - Story 6: Google Classroom OAuth & Coursework Export Endpoints
"""
from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from webapp import app

client = TestClient(app)


# ── Story 1: Task-Based Workspace Architecture & Scope Fetching (< 200ms) ────

def test_story1_phonics_scope_fetching_under_200ms() -> None:
    """Story 1: Selecting Grade 1, Unit 3 fetches scope state in < 200ms."""
    start = time.time()
    response = client.get("/api/phonics_scope?grade=1&unit=3")
    elapsed_ms = (time.time() - start) * 1000

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "target_phonemes" in data
    assert "taught_graphemes" in data
    assert "heart_words" in data
    assert len(data["taught_graphemes"]) > 0
    assert elapsed_ms < 200, f"Scope fetch took {elapsed_ms:.2f}ms (> 200ms target)"


def test_story1_workspace_quadrant_selector_rendered() -> None:
    """Story 1: HTML frontend contains 4-Quadrant Workspace Selector UI."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert "quadrant-grid" in html
    assert "Decodable Text Generator" in html
    assert "Explicit Phonics Routine Builder" in html
    assert "MTSS / Screener" in html
    assert "Visual Audit Inspector" in html


# ── Story 2: Decodable Text Generator & Visual Audit Inspector ──────────────

def test_story2_decodability_inspector_audit_payload() -> None:
    """Story 2: Verify decodability endpoint returns word-level audit payload."""
    payload = {"text": "The cat sat on a mat.", "grade": "1st", "unit": "1"}
    response = client.post("/api/decodability", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "decodable_pct" in data
    assert "total_words" in data
    assert "heart_words" in data
    assert "off_scope_words" in data
    assert data["total_words"] > 0


# ── Story 3: Print-First CSS & Classroom Export Options ─────────────────────

def test_story3_print_stylesheet_and_export_buttons() -> None:
    """Story 3: HTML includes @media print rules, Atkinson Hyperlegible, student header, and export buttons."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    assert "@media print" in html
    assert "Atkinson Hyperlegible" in html
    assert "student-print-header" in html
    assert "Name: ____________________________________" in html
    assert "Print Student Sheet" in html
    assert "Download PDF" in html
    assert "Copy Plain Text" in html


# ── Story 4: HB 538 Remediation & 1EdTech CASE Standards Mapper ──────────────

def test_story4_georgia_hb538_remediation_and_case_deep_links() -> None:
    """Story 4: Screener evaluation outputs 5-day remediation cards and CASE Rosetta links."""
    payload = {
        "decoding": 0.35,
        "comprehension": 0.80,
        "grade": "1st",
        "student_name": "Marcus Williams"
    }
    response = client.post("/tools/evaluate_simple_view", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "diagnostic" in data
    assert data["diagnostic"]["reading_profile"] == "dyslexia"
    assert len(data["remediations"]) > 0

    std_response = client.post("/api/standards", json={"description": "decode words with silent e", "state": "GA"})
    assert std_response.status_code == 200
    std_data = std_response.json()
    assert "matches" in std_data
    assert len(std_data["matches"]) > 0
    assert "rosetta.commongoodlt.com" in std_data["matches"][0]["url"]


# ── Story 5: FERPA Privacy Shield & Client-Side PII Safeguard ───────────────

def test_story5_ferpa_pii_sanitization() -> None:
    """Story 5: PII sanitizer strips student names and IDs prior to backend processing."""
    pii_payload = {"student_name": "Alex Smith", "student_id": "GA-12345"}
    response = client.post("/tools/sanitize_pii", json=pii_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    sanitized = data["sanitized_data"]
    assert "Alex Smith" not in str(sanitized)
    assert "student_token" in sanitized

    diag_response = client.post("/tools/evaluate_simple_view", json={
        "decoding": 0.40,
        "comprehension": 0.85,
        "grade": "1st",
        "student_name": "Alex Smith"
    })
    assert diag_response.status_code == 200
    diag_data = diag_response.json()
    assert "Alex Smith" not in str(diag_data)


# ── Story 6: Google Classroom OAuth & Coursework Export ─────────────────────

def test_story6_google_classroom_courses_endpoint() -> None:
    """Story 6: GET /api/v1/google-classroom/courses returns teacher active courses."""
    response = client.get("/api/v1/google-classroom/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "courses" in data
    assert len(data["courses"]) > 0


def test_story6_google_classroom_publish_endpoint() -> None:
    """Story 6: POST /api/v1/google-classroom/publish publishes assignment coursework."""
    payload = {
        "course_id": "demo_course_101",
        "title": "Decodable Text Assignment: Short Vowels",
        "description": "The cat sat on a mat.",
        "points": 100
    }
    response = client.post("/api/v1/google-classroom/publish", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "published"
    assert "alternateLink" in data
    assert "classroom.google.com" in data["alternateLink"]
