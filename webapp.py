"""SoR Web Dashboard — Teacher-First Workspace for the Science of Reading MCP server.

EPIC-SOR-01 Implementation & Usability Polish:
  - Step 1: MTSS Screener (Simple View screening profile + intervention cards for diagnosed skills)
  - Step 2: Decodable Text Checker (scope & sequence + pronunciation-dictionary alignment)
  - Step 3: Explicit Phonics Routine Builder (5-Day I Do / We Do / You Do scripts with multisensory cues)
  - Step 4: Visual Audit Inspector & Anti-Cueing Shield (Color-coded badges & hover tooltips)
  - Classroom Exports: Print-First CSS (@media print, Atkinson Hyperlegible) & Google Classroom OAuth2 v1

Usability Improvements Implemented:
  1. Inline (?) Score Conversion Tooltips for DIBELS NWF & Maze raw-to-decimal scores.
  2. Dynamic Preset Summary Pill.
  3. Data-minimization & Progress Monitoring Information Callout Box.
  4. Clickable student-data handling disclosure modal.
  5. Standalone Utility badges on Tabs 5 & 6.
  6. ✏️ Edit Text in Place toggle button on rendered Decodable Inspector containers.
  7. Visual Google Classroom API status indicator badge (⚡ Demo Mode vs 🔒 Connected).

Usage: python3 webapp.py  (runs on localhost:8093 by default)
"""
from __future__ import annotations

import json
import sys
import re
from pathlib import Path

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import time, uvicorn

from src.routes.google_classroom import router as gc_router

app = FastAPI(title="SoR Dashboard", version="4.0")
app.include_router(gc_router)

# ── Static Files Mount ──────────────────────────────────────────────────────
base_dir = Path(__file__).resolve().parent
static_dir = base_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ── Security Middleware ─────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://edtechlabs.dev", "https://sor.edtechlabs.dev", "http://localhost:8093"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

rate_limits = {}
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = rate_limits.get(ip, {"reset": now + 60, "count": 0})
        if now > window["reset"]:
            window = {"reset": now + 60, "count": 0}
        window["count"] += 1
        rate_limits[ip] = window
        if window["count"] > 60:
            return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(RateLimitMiddleware)

from src.tools.evidence import search_evidence, align_standards
from src.tools.vocabulary import classify_text
from src.tools.remediation import get_instructional_remediation, list_available_remediations
from src.tools.diagnostics import evaluate_simple_view
from src.tools.decodability import check_decodability
from src.tools.phonics import get_phonics_scope
from src.prompts.phonics import explicit_phonics_routine
from src.tools.privacy import sanitize_pii

# ── Sidebar Data Loader ─────────────────────────────────────────────────────

def _load_sidebar_data():
    """Load research and theoretical frameworks from DuckDB."""
    base = Path(__file__).resolve().parent

    frameworks, papers = _query_research(base)
    pillar_findings = _build_pillar_findings(papers)

    return {
        "frameworks": frameworks,
        "papers": papers,
        "pillar_findings": pillar_findings,
    }


def _query_research(base: Path):
    """Query DuckDB for theoretical frameworks and research papers."""
    try:
        import duckdb
        db_path = base / "db" / "sor_evidence.duckdb"
        conn = duckdb.connect(str(db_path))

        frameworks = []
        for row in conn.execute(
            "SELECT id, name, authors, year, description FROM theoretical_frameworks ORDER BY id"
        ).fetchall():
            frameworks.append({
                "id": row[0],
                "name": row[1],
                "authors": row[2] or "",
                "year": row[3] or 0,
                "description": row[4] or "",
            })

        papers = []
        for row in conn.execute(
            "SELECT id, title, authors, year, framework, finding, effect_size, source, url "
            "FROM research_papers ORDER BY id"
        ).fetchall():
            papers.append({
                "id": row[0],
                "title": row[1],
                "authors": row[2] or "",
                "year": row[3],
                "framework": row[4],
                "finding": row[5] or "",
                "effect_size": round(row[6], 2) if row[6] else None,
                "source": row[7],
                "url": row[8] or "",
            })

        conn.close()
        return frameworks, papers
    except Exception:
        return [], []


def _build_pillar_findings(papers):
    """Group papers by pillar and extract plain-language findings."""
    pillar_map = {
        "phonemic_awareness": "🔤 Phonemic Awareness",
        "phonics": "📖 Phonics",
        "fluency": "📈 Fluency",
        "vocabulary": "📚 Vocabulary",
        "comprehension": "🧠 Comprehension",
    }
    findings = {}
    for p in papers:
        fw = p.get("framework", "")
        pillar = pillar_map.get(fw, fw.title().replace("_", " "))
        if pillar not in findings:
            findings[pillar] = []
        findings[pillar].append({
            "title": p["title"],
            "year": p["year"],
            "effect_size": p["effect_size"],
            "source": p["source"],
            "url": p["url"],
            "finding": p["finding"][:200] if p["finding"] else "",
        })
    return findings


# ── Build Frontend ───────────────────────────────────────────────────────────

def build_frontend() -> str:
    """Build the Material Design 3 HTML frontend with Diagnostic-First sequential workflow and UX polish."""
    data = _load_sidebar_data()

    FRAMEWORKS_JSON = json.dumps(data["frameworks"])
    PAPERS_JSON = json.dumps(data["papers"])
    PILLAR_FINDINGS_JSON = json.dumps(data["pillar_findings"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Science of Reading — Teacher-First Workspace</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%236750A4'/><text x='16' y='23' text-anchor='middle' font-size='20'>🧠</text></svg>">
<style>
/* ── Google Material Design 3 Tokens ── */
:root {{
  --md-sys-color-primary: #6750A4;
  --md-sys-color-on-primary: #FFFFFF;
  --md-sys-color-primary-container: #EADDFF;
  --md-sys-color-on-primary-container: #21005D;
  --md-sys-color-secondary: #625B71;
  --md-sys-color-secondary-container: #E8DEF8;
  --md-sys-color-tertiary: #E06D53;
  --md-sys-color-tertiary-container: #FFDBCF;
  --md-sys-color-background: #FAF8FC;
  --md-sys-color-surface: #FFFFFF;
  --md-sys-color-surface-variant: #F4EFF4;
  --md-sys-color-on-surface-variant: #49454F;
  --md-sys-color-outline: #79747E;
  --md-sys-color-outline-variant: #CAC4D0;

  --md-shape-corner-small: 8px;
  --md-shape-corner-medium: 16px;
  --md-shape-corner-large: 24px;
  --md-shape-corner-full: 9999px;

  --md-elevation-1: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --md-elevation-2: 0 4px 12px rgba(103,80,164,0.08), 0 2px 6px rgba(0,0,0,0.04);
  --md-elevation-3: 0 8px 24px rgba(103,80,164,0.12), 0 4px 8px rgba(0,0,0,0.06);
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: 'Inter', sans-serif;
  background-color: var(--md-sys-color-background);
  color: #1C1B1F;
  line-height: 1.6;
  overflow-x: hidden;
}}

h1, h2, h3, h4, .font-heading {{
  font-family: 'Outfit', sans-serif;
}}

/* ── Top App Bar & FERPA Security Shield ── */
.app-bar {{
  background: var(--md-sys-color-surface);
  border-bottom: 1px solid var(--md-sys-color-surface-variant);
  padding: 0.8rem 1.8rem;
  display: flex;
  align-items: center;
  gap: 1.2rem;
  position: sticky;
  top: 0;
  z-index: 500;
  box-shadow: var(--md-elevation-1);
}}

.drawer-trigger-btn {{
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border: none;
  padding: 0.55rem 1.1rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(103,80,164,0.15);
}}
.drawer-trigger-btn:hover {{
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  transform: translateY(-1px);
}}

.app-bar-brand {{
  display: flex;
  align-items: center;
  gap: 0.8rem;
  flex: 1;
}}
.app-bar-icon {{
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, var(--md-sys-color-primary), #4A3E7D);
  color: #fff;
  border-radius: var(--md-shape-corner-medium);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  box-shadow: 0 2px 8px rgba(103,80,164,0.25);
}}
.app-bar-title {{
  font-size: 1.3rem;
  font-weight: 700;
  color: #1C1B1F;
  letter-spacing: -0.01em;
}}
.app-bar-subtitle {{
  font-size: 0.75rem;
  color: var(--md-sys-color-secondary);
  font-weight: 500;
}}

/* FERPA Security Trust Indicator Badge (Clickable) */
.ferpa-shield-badge {{
  background: #E8F5E9;
  color: #1B5E20;
  border: 1px solid #A5D6A7;
  padding: 0.45rem 0.9rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.8rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}}
.ferpa-shield-badge:hover {{
  background: #C8E6C9;
  transform: scale(1.02);
}}

/* Tooltip Icon for Form Fields */
.help-icon-tooltip {{
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 800;
  cursor: help;
  margin-left: 0.4rem;
}}
.help-icon-tooltip .tooltip-text {{
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 130%;
  left: 50%;
  transform: translateX(-50%);
  background: #212121;
  color: #fff;
  padding: 0.6rem 0.9rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 400;
  width: 260px;
  white-space: normal;
  line-height: 1.4;
  z-index: 2000;
  box-shadow: var(--md-elevation-3);
  transition: opacity 0.2s ease, visibility 0.2s ease;
}}
.help-icon-tooltip:hover .tooltip-text {{
  visibility: visible;
  opacity: 1;
}}

/* Toast Notifications for PII Sanitization */
.toast-container {{
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}}
.toast {{
  background: #1C1B1F;
  color: #fff;
  padding: 0.9rem 1.4rem;
  border-radius: var(--md-shape-corner-medium);
  box-shadow: var(--md-elevation-3);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  border-left: 4px solid #4CAF50;
  animation: toastIn 0.3s cubic-bezier(0.4,0,0.2,1);
}}
@keyframes toastIn {{
  from {{ opacity: 0; transform: translateY(12px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* ── Diagnostic-First Sequential 4-Step Quadrant Grid ── */
.workflow-header-banner {{
  background: var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-medium);
  padding: 0.8rem 1.2rem;
  margin-bottom: 1.2rem;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  border-left: 4px solid var(--md-sys-color-primary);
}}

.quadrant-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.2rem;
  margin-bottom: 2rem;
}}
@media(max-width: 768px) {{
  .quadrant-grid {{ grid-template-columns: 1fr; }}
}}

.quadrant-card {{
  background: var(--md-sys-color-surface);
  border: 2px solid var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-large);
  padding: 1.4rem;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-1);
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  position: relative;
}}
.quadrant-card:hover {{
  border-color: var(--md-sys-color-primary);
  box-shadow: var(--md-elevation-2);
  transform: translateY(-2px);
}}
.quadrant-card.active {{
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
  box-shadow: var(--md-elevation-2);
}}
.quadrant-step-badge {{
  position: absolute;
  top: 0.9rem;
  right: 0.9rem;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-primary);
  font-family: 'Outfit', sans-serif;
  font-weight: 800;
  font-size: 0.72rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--md-shape-corner-small);
  letter-spacing: 0.05em;
}}
.quadrant-card.active .quadrant-step-badge {{
  background: var(--md-sys-color-primary);
  color: #fff;
}}

.quadrant-icon {{
  width: 48px;
  height: 48px;
  border-radius: var(--md-shape-corner-medium);
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  flex-shrink: 0;
}}
.quadrant-card.active .quadrant-icon {{
  background: var(--md-sys-color-primary);
  color: #fff;
}}
.quadrant-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1C1B1F;
  margin-bottom: 0.2rem;
}}
.quadrant-desc {{
  font-size: 0.84rem;
  color: var(--md-sys-color-secondary);
  line-height: 1.4;
}}

/* ── M3 Navigation Bar ── */
.m3-tab-bar-container {{
  background: var(--md-sys-color-surface);
  border-bottom: 1px solid var(--md-sys-color-surface-variant);
  position: sticky;
  top: 65px;
  z-index: 400;
  box-shadow: var(--md-elevation-1);
}}
.m3-tab-bar {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.6rem 1rem;
}}

.m3-tab-btn {{
  background: transparent;
  border: none;
  padding: 0.55rem 1.05rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}}
.m3-tab-btn:hover {{
  background: var(--md-sys-color-surface-variant);
  color: var(--md-sys-color-primary);
}}
.m3-tab-btn.active {{
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: 0 4px 12px rgba(103, 80, 164, 0.25);
  font-weight: 700;
}}

/* ── Container & Layout ── */
.container {{
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.8rem 1.2rem;
}}

.tab-pane {{
  display: none;
  animation: m3FadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
.tab-pane.active {{
  display: block;
}}
@keyframes m3FadeIn {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* ── M3 Cards ── */
.m3-card {{
  background: var(--md-sys-color-surface);
  border-radius: var(--md-shape-corner-large);
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: var(--md-elevation-2);
  border: 1px solid rgba(121, 116, 126, 0.12);
}}

.m3-card-title {{
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--md-sys-color-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.7rem;
}}

/* DecodableInspector Word Badges & Audit Bar */
.audit-metrics-bar {{
  background: var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-medium);
  padding: 1.1rem 1.4rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 1.4rem;
  border-left: 5px solid var(--md-sys-color-primary);
}}
.audit-metric-num {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--md-sys-color-primary);
}}
.audit-metric-label {{
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--md-sys-color-secondary);
  letter-spacing: 0.05em;
}}

.inspector-word-container {{
  line-height: 2.3;
  font-size: 1.15rem;
  padding: 1.4rem;
  background: #fff;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-shape-corner-medium);
  margin: 1.2rem 0;
}}

.word-badge {{
  position: relative;
  display: inline-block;
  padding: 0.25rem 0.55rem;
  margin: 0.15rem 0.2rem;
  border-radius: var(--md-shape-corner-small);
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease;
}}
.word-badge:hover {{
  transform: translateY(-2px);
}}
.badge-decodable {{
  background: #E8F5E9;
  color: #1B5E20;
  border: 1px solid #A5D6A7;
}}
.badge-heart {{
  background: #FFF9C4;
  color: #F57F17;
  border: 1px solid #FFF59D;
}}
.badge-heart::after {{
  content: ' 💛';
  font-size: 0.75rem;
}}
.badge-offscope {{
  background: #FFEBEE;
  color: #C62828;
  border: 2px solid #EF5350;
}}

.word-badge .tooltip {{
  visibility: hidden;
  opacity: 0;
  position: absolute;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%);
  background: #212121;
  color: #fff;
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  font-size: 0.78rem;
  white-space: nowrap;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  transition: opacity 0.2s ease, visibility 0.2s ease;
}}
.word-badge:hover .tooltip {{
  visibility: visible;
  opacity: 1;
}}

.export-bar {{
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;
  margin-top: 1.4rem;
  padding-top: 1.2rem;
  border-top: 1px solid var(--md-sys-color-surface-variant);
}}
.export-btn {{
  background: var(--md-sys-color-secondary-container);
  color: #1D192B;
  border: none;
  padding: 0.65rem 1.3rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.88rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}}
.export-btn:hover {{
  background: var(--md-sys-color-primary);
  color: #fff;
}}

.student-print-header {{
  display: none;
}}

/* Print-First CSS (@media print) */
@media print {{
  @page {{
    size: letter portrait;
    margin: 0.75in;
  }}
  
  body {{
    background: #fff !important;
    color: #000 !important;
    font-family: 'Atkinson Hyperlegible', 'Inter', sans-serif !important;
    font-size: 18pt !important;
    line-height: 1.6 !important;
  }}

  .app-bar, .m3-tab-bar-container, .sidebar, .sidebar-backdrop, footer,
  .quadrant-grid, .workflow-header-banner, .m3-btn, .export-bar, form, .m3-card-title i, .ferpa-shield-badge {{
    display: none !important;
  }}

  .container {{
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
  }}

  .m3-card {{
    box-shadow: none !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
  }}

  .student-print-header {{
    display: block !important;
    border-bottom: 2px solid #000;
    padding-bottom: 0.8rem;
    margin-bottom: 1.5rem;
    font-family: 'Atkinson Hyperlegible', sans-serif;
    font-weight: 700;
    font-size: 16pt;
  }}

  .student-header-row {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.4rem;
  }}

  .inspector-word-container {{
    border: none !important;
    padding: 0 !important;
    font-size: 20pt !important;
    line-height: 1.8 !important;
  }}

  .word-badge {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: #000 !important;
  }}
  .badge-heart::after {{
    content: '' !important;
  }}

  .remediation-card {{
    box-shadow: none !important;
    border: 1px solid #000 !important;
    page-break-inside: avoid;
  }}
}}

/* Form Elements */
.form-group {{ margin-bottom: 1.3rem; }}
label {{
  display: flex;
  align-items: center;
  font-family: 'Outfit', sans-serif;
  font-weight: 600;
  font-size: 0.92rem;
  color: #1C1B1F;
  margin-bottom: 0.4rem;
}}
input, select, textarea {{
  width: 100%;
  padding: 0.85rem 1.1rem;
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: var(--md-shape-corner-medium);
  font-size: 0.98rem;
  font-family: inherit;
  background: var(--md-sys-color-surface);
  color: #1C1B1F;
  transition: all 0.2s ease;
}}
input:focus, select:focus, textarea:focus {{
  border-color: var(--md-sys-color-primary);
  outline: none;
  box-shadow: 0 0 0 4px var(--md-sys-color-primary-container);
}}
.row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }}
@media(max-width: 600px) {{ .row {{ grid-template-columns: 1fr; }} }}

.m3-btn {{
  background: linear-gradient(135deg, var(--md-sys-color-primary), #4A3E7D);
  color: var(--md-sys-color-on-primary);
  border: none;
  padding: 0.95rem 1.6rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-size: 0.96rem;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  white-space: normal;
  text-align: center;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  box-shadow: 0 4px 14px rgba(103, 80, 164, 0.3);
  transition: all 0.25s ease;
}}
.m3-btn:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 80, 164, 0.4);
}}

.result {{ display: none; margin-top: 1.8rem; padding-top: 1.8rem; border-top: 2px dashed var(--md-sys-color-outline-variant); }}
.result.show {{ display: block; }}

.scope-info-box {{
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: var(--md-shape-corner-medium);
  padding: 1rem 1.2rem;
  margin-top: 0.8rem;
  font-size: 0.88rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}}
.scope-tag-list {{
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.2rem;
}}
.scope-tag {{
  background: #fff;
  color: var(--md-sys-color-primary);
  padding: 0.2rem 0.6rem;
  border-radius: var(--md-shape-corner-small);
  font-weight: 700;
  font-size: 0.78rem;
}}

/* Sidebar Drawer */
.sidebar-backdrop {{
  position: fixed; inset: 0; background: rgba(0,0,0,0.45); z-index: 800; opacity: 0; pointer-events: none; transition: opacity 0.3s;
}}
.sidebar-backdrop.open {{ opacity: 1; pointer-events: auto; }}

.sidebar {{
  position: fixed; top: 0; left: 0; height: 100vh; width: 420px; max-width: 90vw;
  background: var(--md-sys-color-surface); color: #1C1B1F; z-index: 900; overflow-y: auto;
  transform: translateX(-100%); transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--md-elevation-3); border-right: 1px solid var(--md-sys-color-surface-variant);
}}
.sidebar.open {{ transform: translateX(0); }}

.drawer-section {{
  background: var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-medium);
  padding: 1.2rem;
  margin-bottom: 1.2rem;
  border-left: 4px solid var(--md-sys-color-primary);
}}
.drawer-section-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--md-sys-color-primary);
  margin-bottom: 0.6rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}}
.drawer-concept-item {{
  background: var(--md-sys-color-surface);
  border-radius: var(--md-shape-corner-small);
  padding: 0.75rem 0.9rem;
  margin: 0.5rem 0;
  border: 1px solid rgba(121, 116, 126, 0.12);
}}
.drawer-concept-term {{
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.92rem;
  color: #1C1B1F;
}}
.drawer-concept-def {{
  font-size: 0.86rem;
  color: #49454F;
  margin-top: 0.2rem;
  line-height: 1.5;
}}
</style>
</head>
<body>

<!-- Toast Notification Container for FERPA Shield -->
<div class="toast-container" id="toastContainer"></div>

<!-- Sidebar Backdrop -->
<div class="sidebar-backdrop" id="sidebarBackdrop"></div>

<!-- Context-Aware Dynamic Pull-Out Left Drawer -->
<aside class="sidebar" id="sidebar">
  <div style="padding:1.4rem;border-bottom:1px solid var(--md-sys-color-surface-variant);background:var(--md-sys-color-primary-container);display:flex;align-items:center;justify-content:space-between">
    <div>
      <h2 style="color:var(--md-sys-color-on-primary-container);font-size:1.15rem;font-weight:700" id="drawerTitle">🔬 Topic & Research Guide</h2>
      <div style="font-size:0.78rem;color:var(--md-sys-color-secondary);margin-top:0.2rem" id="drawerSubTitle">Contextual Science of Reading Research & Concepts</div>
    </div>
    <button onclick="closeSidebar()" style="background:transparent;border:none;font-size:1.3rem;color:var(--md-sys-color-on-primary-container);cursor:pointer;padding:0.4rem" title="Close Drawer"><i class="fa-solid fa-xmark"></i></button>
  </div>
  <div style="padding:1.4rem" id="sidebarDynamicContent"></div>
</aside>

<!-- FERPA Privacy & Zero Data Retention Modal Dialog -->
<div class="sidebar-backdrop" id="ferpaModalBackdrop" style="z-index:2200"></div>
<div id="ferpaModal" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border-radius:var(--md-shape-corner-large);max-width:600px;width:92vw;padding:2rem;box-shadow:var(--md-elevation-3);z-index:2300;display:none">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem;border-bottom:1px solid #E0E0E0;padding-bottom:0.8rem">
    <h3 style="color:#1B5E20;margin:0;display:flex;align-items:center;gap:0.6rem">
      <i class="fa-solid fa-shield-halved"></i> How Student Data Is Handled
    </h3>
    <button onclick="closeFerpaModal()" style="background:none;border:none;font-size:1.3rem;cursor:pointer">✕</button>
  </div>

  <div style="font-size:0.9rem;color:#333;line-height:1.6">
    <p style="margin-bottom:0.8rem">
      <strong>🔒 Names removed before sending:</strong> The student name you type is replaced with a placeholder in your browser before anything is sent. Text you paste is also scrubbed of that name and of identifier-like patterns (long ID numbers such as GTIDs, emails, phone numbers, dates).
    </p>
    <p style="margin-bottom:0.8rem">
      <strong>🗑️ Nothing stored:</strong> Requests are processed in memory. The app does not write student names or scores to disk or to a database.
    </p>
    <p style="margin-bottom:1rem">
      <strong>⚠️ Limits:</strong> Automatic scrubbing cannot catch every identifier (for example, a classmate's name typed into a passage). Don't paste student records into the app. This tool has not been independently audited, and using it does not by itself make a district FERPA or COPPA compliant; districts should complete their own privacy review.
    </p>
    <div style="background:#E8F5E9;padding:0.9rem;border-radius:var(--md-shape-corner-medium);border-left:4px solid #2E7D32;font-size:0.84rem">
      <strong>💡 District Privacy Reviewers:</strong> For details, see the data privacy section of the <a href="https://github.com/kosburn0408/sor-mcp-server/blob/main/USER_GUIDE.md#6-data-privacy--ferpa-shield" target="_blank" style="color:#1B5E20;font-weight:700">USER_GUIDE.md on GitHub</a> or audit source code at <code>src/tools/privacy.py</code>.
    </div>
  </div>

  <div style="margin-top:1.4rem;text-align:right">
    <button onclick="closeFerpaModal()" class="m3-btn" style="width:auto;padding:0.6rem 1.6rem">Close Privacy Disclosure</button>
  </div>
</div>

<!-- Google Classroom Export Modal Dialog -->
<div class="sidebar-backdrop" id="gcModalBackdrop" style="z-index:2000"></div>
<div id="gcModal" style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border-radius:var(--md-shape-corner-large);max-width:550px;width:92vw;padding:1.8rem;box-shadow:var(--md-elevation-3);z-index:2100;display:none">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
    <h3 style="color:var(--md-sys-color-primary);margin:0;display:flex;align-items:center;gap:0.6rem">
      <i class="fa-solid fa-graduation-cap"></i> Export to Google Classroom
    </h3>
    <button onclick="closeGCModal()" style="background:none;border:none;font-size:1.3rem;cursor:pointer">✕</button>
  </div>

  <!-- Dynamic Connection Status Indicator Pill -->
  <div id="gcConnectionStatusPill" style="margin-bottom:1.2rem">
    <span class="scope-tag" style="background:#FFF3E0;color:#E65100"><i class="fa-solid fa-bolt"></i> ⚡ Demo Simulation Mode Active</span>
  </div>

  <div id="gcModalSuccess" style="display:none;text-align:center;padding:1.5rem 0">
    <div style="font-size:3rem;margin-bottom:0.8rem">🎉</div>
    <h4 style="color:#2E7D32;margin-bottom:0.5rem">Assignment Successfully Published!</h4>
    <p style="font-size:0.9rem;color:#555;margin-bottom:1.2rem">Your decodable reading assignment is now live for your students in Google Classroom.</p>
    <a id="gcOutboundLink" href="https://classroom.google.com" target="_blank" class="export-btn" style="text-decoration:none;display:inline-flex">
      🔗 Open in Google Classroom
    </a>
  </div>

  <form id="gcPublishForm">
    <div class="form-group">
      <label>Google OAuth Access Token (Optional for Demo Mode)</label>
      <input type="password" id="gcAccessToken" oninput="updateGCConnectionStatus()" placeholder="Paste Bearer Token or leave blank for demo">
    </div>
    <div class="form-group">
      <label>Select Target Classroom Course</label>
      <select id="gcCourseSelect">
        <option value="demo_course_101">1st Grade Reading — Unit 3</option>
        <option value="demo_course_102">MTSS Literacy Intervention Group</option>
      </select>
    </div>
    <div class="form-group">
      <label>Assignment Title</label>
      <input type="text" id="gcTitle" value="Decodable Text Practice Sheet" required>
    </div>
    <div class="form-group">
      <label>Instructions & Decodable Content</label>
      <textarea id="gcContent" rows="5" required></textarea>
    </div>
    <div class="form-group">
      <label>Points</label>
      <input type="number" id="gcPoints" value="100">
    </div>
    <div style="display:flex;gap:0.8rem;margin-top:1.2rem">
      <button type="button" onclick="closeGCModal()" class="export-btn" style="background:#E8DEF8">Cancel</button>
      <button type="submit" class="m3-btn" style="width:auto;flex:1"><i class="fa-solid fa-paper-plane"></i> Publish Coursework</button>
    </div>
  </form>
</div>

<!-- Top App Bar -->
<header class="app-bar">
  <button class="drawer-trigger-btn" id="sidebarToggle" title="Open Topic & Research Guide">
    <i class="fa-solid fa-bars-staggered"></i>
    <span>Topic & Research Guide</span>
  </button>
  <div class="app-bar-brand">
    <div class="app-bar-icon"><i class="fa-solid fa-brain"></i></div>
    <div>
      <div class="app-bar-title">EdTech Labs</div>
      <div class="app-bar-subtitle">Science of Reading Teacher-First Workspace</div>
    </div>
  </div>
  <div class="ferpa-shield-badge" onclick="openFerpaModal()" title="How student data is handled">
    <i class="fa-solid fa-shield-halved"></i>
    <span>🔒 Student names removed before processing</span>
  </div>
</header>

<!-- M3 Segmented Navigation Tabs (Diagnostic-First Sequential Ordering) -->
<div class="m3-tab-bar-container">
  <nav class="m3-tab-bar">
    <button class="m3-tab-btn active" data-tab="tab-diagnose" onclick="switchTab('tab-diagnose')">
      <i class="fa-solid fa-bullseye"></i> Step 1: MTSS Screener
    </button>
    <button class="m3-tab-btn" data-tab="tab-decodable" onclick="switchTab('tab-decodable')">
      <i class="fa-solid fa-book-open"></i> Step 2: Decodable Text Checker
    </button>
    <button class="m3-tab-btn" data-tab="tab-phonics" onclick="switchTab('tab-phonics')">
      <i class="fa-solid fa-puzzle-piece"></i> Step 3: Phonics Routine
    </button>
    <button class="m3-tab-btn" data-tab="tab-auditor" onclick="switchTab('tab-auditor')">
      <i class="fa-solid fa-magnifying-glass"></i> Step 4: Visual Auditor
    </button>
    <button class="m3-tab-btn" data-tab="tab-vocab" onclick="switchTab('tab-vocab')">
      <i class="fa-solid fa-layer-group"></i> Classify Vocabulary <span style="font-size:0.68rem;opacity:0.85;background:rgba(0,0,0,0.08);padding:0.1rem 0.4rem;border-radius:4px;margin-left:0.2rem">Standalone</span>
    </button>
    <button class="m3-tab-btn" data-tab="tab-standards" onclick="switchTab('tab-standards')">
      <i class="fa-solid fa-award"></i> Standards Alignment <span style="font-size:0.68rem;opacity:0.85;background:rgba(0,0,0,0.08);padding:0.1rem 0.4rem;border-radius:4px;margin-left:0.2rem">50 States</span>
    </button>
  </nav>
</div>

<!-- Main Container -->
<div class="container">

  <!-- Student Printable Header (@media print visible) -->
  <div class="student-print-header">
    <div class="student-header-row">
      <span>Name: ____________________________________</span>
      <span>Date: __________________</span>
    </div>
    <div class="student-header-row" style="font-size:12pt;font-weight:normal;color:#444">
      <span>Science of Reading Practice Sheet</span>
      <span>Grade: _______ Unit: _______</span>
    </div>
  </div>

  <!-- Diagnostic Workflow Banner -->
  <div class="workflow-header-banner">
    <i class="fa-solid fa-circle-nodes"></i>
    <span>Diagnostic-to-Classroom Workflow: Step 1 (Diagnose) → Step 2 (Select Scope & Generate) → Step 3 (Script Routine) → Step 4 (Audit & Export)</span>
  </div>

  <!-- ── Diagnostic-First 4-Step Quadrant Grid ── -->
  <div class="quadrant-grid">
    <div class="quadrant-card active" id="quadrant-remediation" onclick="switchTab('tab-diagnose')">
      <div class="quadrant-step-badge">STEP 1</div>
      <div class="quadrant-icon"><i class="fa-solid fa-bullseye"></i></div>
      <div>
        <div class="quadrant-title">🎯 MTSS Screener & Remediation</div>
        <div class="quadrant-desc">Turn screener scores into a Simple View screening profile and intervention cards for diagnosed skills.</div>
      </div>
    </div>
    <div class="quadrant-card" id="quadrant-decodable" onclick="switchTab('tab-decodable')">
      <div class="quadrant-step-badge">STEP 2</div>
      <div class="quadrant-icon"><i class="fa-solid fa-book-open"></i></div>
      <div>
        <div class="quadrant-title">📖 Decodable Text Checker</div>
        <div class="quadrant-desc">Check a passage against the phonics patterns taught through a grade and unit.</div>
      </div>
    </div>
    <div class="quadrant-card" id="quadrant-phonics" onclick="switchTab('tab-phonics')">
      <div class="quadrant-step-badge">STEP 3</div>
      <div class="quadrant-icon"><i class="fa-solid fa-puzzle-piece"></i></div>
      <div>
        <div class="quadrant-title">🧩 Explicit Phonics Routine Builder</div>
        <div class="quadrant-desc">Generate 5-day I Do / We Do / You Do scripts with multisensory cues.</div>
      </div>
    </div>
    <div class="quadrant-card" id="quadrant-auditor" onclick="switchTab('tab-auditor')">
      <div class="quadrant-step-badge">STEP 4</div>
      <div class="quadrant-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
      <div>
        <div class="quadrant-title">🔍 Visual Audit & Anti-Cueing Shield</div>
        <div class="quadrant-desc">Visual proof inspector with color badges & Google Classroom export.</div>
      </div>
    </div>
  </div>

  <!-- ── STEP 1: MTSS SCREENER (Default Landing) ── -->
  <div class="tab-pane active" id="tab-diagnose">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-bullseye"></i> Step 1: MTSS Screener &amp; Intervention Planning</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Enter screener scores to see the student's Simple View of Reading screening profile, then choose the skills a diagnostic identified to get explicit intervention scripts. This is a screening aid, not a diagnosis. Find aligned standards with
        <a href="https://rosetta.commongoodlt.com/" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">
          1EdTech CASE® Standards Satchel
        </a> deep links.
      </p>

      <form id="diagnoseForm">
        <div class="row">
          <div class="form-group">
            <label>
              Example Profile
              <span class="help-icon-tooltip">?
                <span class="tooltip-text">Examples fill in illustrative scores and a diagnosed skill so you can see the workflow. Use Custom with your own screener and diagnostic results.</span>
              </span>
            </label>
            <select id="hb538Deficit" onchange="autofillDeficitScores()">
              <option value="custom" selected>Custom Assessment Input</option>
              <option value="nwf_low">Example: low nonsense-word fluency (CVC decoding)</option>
              <option value="phoneme_segmentation">Example: phoneme segmentation difficulty</option>
              <option value="vowel_teams">Example: vowel team errors</option>
              <option value="consonant_blends">Example: consonant blend errors</option>
            </select>
            <div id="presetSummaryPill" style="font-size:0.8rem;color:var(--md-sys-color-primary);margin-top:0.4rem;font-weight:600">
              <i class="fa-solid fa-circle-info"></i> Enter your own scores, or pick an example. Georgia's Early Literacy Act (HB 538) requires universal screening in K–3; follow your district's approved screener and intervention guidance.
            </div>
          </div>
          <div class="form-group">
            <label>Grade Level</label>
            <select id="grade">
              <option value="K">Kindergarten</option>
              <option value="1st" selected>1st Grade</option>
              <option value="2nd">2nd Grade</option>
              <option value="3rd">3rd Grade</option>
            </select>
          </div>
        </div>

        <div class="row">
          <div class="form-group">
            <label>
              Decoding Score (0.0 – 1.0)
              <span class="help-icon-tooltip">?
                <span class="tooltip-text">Your word-reading/decoding measure expressed on a 0–1 scale (for example, a percentile rank divided by 100). Use the same scale for the cutoff.</span>
              </span>
            </label>
            <input type="number" id="decoding" step="0.01" min="0" max="1" value="0.38" required>
          </div>
          <div class="form-group">
            <label>
              Language Comprehension (0.0 – 1.0)
              <span class="help-icon-tooltip">?
                <span class="tooltip-text">A language or listening comprehension measure on the same 0–1 scale.</span>
              </span>
            </label>
            <input type="number" id="comprehension" step="0.01" min="0" max="1" value="0.85" required>
          </div>
        </div>

        <div class="row">
          <div class="form-group">
            <label>
              At-Risk Cutoff (0.0 – 1.0)
              <span class="help-icon-tooltip">?
                <span class="tooltip-text">Set this to your screener's at-risk benchmark on the same 0–1 scale. 0.60 is only a placeholder.</span>
              </span>
            </label>
            <input type="number" id="cutoff" step="0.01" min="0.01" max="0.99" value="0.60" required>
          </div>
          <div class="form-group">
            <label>Skills Identified by a Diagnostic (optional)</label>
            <select id="diagnosedSkills" multiple size="4">
              <option value="phoneme_segmentation">Phoneme segmentation</option>
              <option value="cvc_short_a">Short a (CVC)</option>
              <option value="cvc_mixed">Mixed short vowels (CVC)</option>
              <option value="consonant_blends">Consonant blends</option>
              <option value="consonant_digraphs">Consonant digraphs</option>
              <option value="cvce_silent_e">Silent-e (CVCe)</option>
              <option value="r_controlled">R-controlled vowels</option>
              <option value="vowel_teams">Vowel teams</option>
              <option value="prefix_un">Prefix un-</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>Student Name (optional; replaced before anything is sent)</label>
          <input type="text" id="studentNameInput" placeholder="Name is replaced with [STUDENT] in your browser">
        </div>

        <button type="submit" class="m3-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> Step 1: Show Screening Profile &amp; Intervention Cards</button>
      </form>

      <!-- FERPA Zero Data Retention & Progress Monitoring Info Callout -->
      <div style="background:#F3EDF7;border:1px solid #E8DEF8;border-radius:var(--md-shape-corner-medium);padding:0.9rem 1.1rem;margin-top:1.2rem;font-size:0.84rem;color:#49454F;display:flex;align-items:flex-start;gap:0.7rem">
        <i class="fa-solid fa-shield-halved" style="color:var(--md-sys-color-primary);font-size:1.2rem;margin-top:0.1rem"></i>
        <div>
          <strong>🔒 Nothing is stored:</strong> Profiles are computed in memory and not saved. To track 6-week MTSS progress (Rate of Improvement / ROI), click <strong>"Export to Google Classroom"</strong> or <strong>"Print Student Sheet"</strong> to log in your district SIS/LMS.
        </div>
      </div>

      <div class="spinner" id="spinner"><i class="fa-solid fa-circle-notch fa-spin fa-2x"></i><br><br>Computing Simple View screening profile...</div>

      <div class="result" id="result">
        <div id="profileArea"></div>
        <div id="remediationArea"></div>
        <div id="nextSteps"></div>
        <div class="export-bar">
          <button onclick="window.print()" class="export-btn"><i class="fa-solid fa-print"></i> 🖨️ Print Student Sheet</button>
          <button onclick="downloadAsPDF('result')" class="export-btn"><i class="fa-solid fa-file-pdf"></i> 📄 Download PDF</button>
          <button onclick="copyResultText('result')" class="export-btn"><i class="fa-solid fa-copy"></i> 📋 Copy Plain Text</button>
          <button onclick="openGCModal('MTSS Literacy Remediation Plan', document.getElementById('result').innerText)" class="export-btn" style="background:#EADDFF;color:#21005D"><i class="fa-solid fa-graduation-cap"></i> 🎓 Export to Google Classroom</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ── STEP 2: DECODABLE TEXT CHECKER ── -->
  <div class="tab-pane" id="tab-decodable">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-book-open"></i> Step 2: Decodable Text Checker</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Choose the grade and unit your class has reached, then paste a passage. Each word is checked sound by sound against the patterns taught so far, using a pronunciation dictionary. The default sequence is illustrative; districts can load their adopted program's scope &amp; sequence (set <code>SOR_SCOPE_PATH</code>). To generate new decodable text, use the MCP server with an AI assistant, which checks each draft with this same engine.
      </p>

      <form id="decodableGeneratorForm">
        <div class="row">
          <div class="form-group">
            <label>Grade Level</label>
            <select id="scopeGrade" onchange="populateUnits(); fetchPhonicsScope()">
              <option value="K">Kindergarten</option>
              <option value="1" selected>1st Grade</option>
              <option value="2">2nd Grade</option>
              <option value="3">3rd Grade</option>
            </select>
          </div>
          <div class="form-group">
            <label>Unit / Module Focus</label>
            <select id="scopeUnit" onchange="fetchPhonicsScope()">
              <option value="1">Unit 1</option>
            </select>
          </div>
        </div>

        <div class="scope-info-box" id="scopeInfoBox">
          <div style="font-weight:700"><i class="fa-solid fa-layer-group"></i> Taught through this unit (cumulative):</div>
          <div>New this unit: <span id="newPatternsSpan">—</span></div>
          <div>Taught graphemes: <span id="taughtGraphemesSpan">—</span></div>
          <div>Heart words taught: <span id="heartWordsSpan">—</span></div>
        </div>

        <div class="form-group" style="margin-top:1.2rem">
          <label>Passage Text to Audit & Format</label>
          <textarea id="decodeText" rows="4" placeholder="Paste reading passage here...">The cat sat on a mat. She had a red hat. The dog ran to the shop to get a chat with the pet.</textarea>
        </div>

        <button type="submit" class="m3-btn"><i class="fa-solid fa-magnifying-glass"></i> Step 2: Audit Decodability & Render Visual Badges</button>
      </form>

      <div class="result" id="decodeResult"></div>
    </div>
  </div>

  <!-- ── STEP 3: EXPLICIT PHONICS ROUTINE BUILDER ── -->
  <div class="tab-pane" id="tab-phonics">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-puzzle-piece"></i> Step 3: Explicit Phonics Routine Builder</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">Generate a 5-day explicit phonics routine (I Do / We Do / You Do) with word chains and multisensory cues.</p>
      
      <form id="phonicsRoutineForm">
        <div class="row">
          <div class="form-group">
            <label>Target Phoneme / Skill</label>
            <input type="text" id="targetPhoneme" placeholder="e.g. /sh/, /ch/, /ai/, /silent_e/..." value="/sh/" required>
          </div>
          <div class="form-group">
            <label>Multisensory Cue Technique</label>
            <select id="multisensoryCue">
              <option value="finger tapping" selected>Finger Tapping (Phoneme Segmentation)</option>
              <option value="Elkonin boxes">Elkonin Sound Boxes</option>
              <option value="sky writing">Sky Writing / Arm Tapping</option>
              <option value="magic e wand">Magic-E Wand</option>
            </select>
          </div>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> Step 3: Build 5-Day Scripted Routine</button>
      </form>

      <div class="result" id="phonicsRoutineResult"></div>
    </div>
  </div>

  <!-- ── STEP 4: VISUAL AUDIT INSPECTOR & ANTI-CUEING SHIELD ── -->
  <div class="tab-pane" id="tab-auditor">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-magnifying-glass"></i> Step 4: Visual Audit Inspector & Anti-Cueing Shield</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Paste a passage, lesson script or set of teacher prompts. The audit flags three-cueing prompts (guess from the picture, "what would make sense") with decoding-focused replacements, and checks decodability using the grade and unit chosen in Step 2.
      </p>

      <form id="auditorForm">
        <div class="form-group">
          <label>Text Selection for Anti-Cueing & Decodability Audit</label>
          <textarea id="auditText" rows="4" placeholder="Paste reading passage to audit...">Look at the picture. What word would make sense here? The duck swims in the pond.</textarea>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-shield-halved"></i> Step 4: Run Visual Audit & Anti-Cueing Inspection</button>
      </form>
      <div class="result" id="auditResult"></div>
    </div>
  </div>

  <!-- ── WORKSPACE 5: CLASSIFY VOCABULARY ── -->
  <div class="tab-pane" id="tab-vocab">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-layer-group"></i> Three-Tier Vocabulary Classifier</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">Analyze text passages using Beck's 3-Tier vocabulary framework to highlight high-utility Tier 2 academic words.</p>
      <form id="vocabForm">
        <div class="form-group">
          <label>Text Selection</label>
          <textarea id="vocabText" rows="4" placeholder="Paste passage for vocabulary classification..."></textarea>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-filter"></i> Classify Vocabulary Tiers</button>
      </form>
      <div class="result" id="vocabResult"></div>
    </div>
  </div>

  <!-- ── WORKSPACE 6: STANDARDS ALIGNMENT (CASE® EXCHANGE) ── -->
  <div class="tab-pane" id="tab-standards">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-award"></i> State Standards Alignment Lookup</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Find academic standards across <strong>all 50 U.S. states</strong> powered by
        <a href="https://rosetta.commongoodlt.com/" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">
          Standards Satchel (Rosetta)
        </a> CASE® Network.
      </p>
      <form id="standardsForm">
        <div class="row">
          <div class="form-group">
            <label>Learning Goal / Skill</label>
            <input type="text" id="standardsSkill" placeholder="e.g. decode words with silent e..." required>
          </div>
          <div class="form-group">
            <label>State Framework</label>
            <select id="standardsState">
              <option value="GA" selected>Georgia (current K-12 ELA, via SuitCASE)</option>
              <option value="CA">California (CCSS-CA)</option>
              <option value="TX">Texas (TEKS)</option>
              <option value="FL">Florida (B.E.S.T.)</option>
              <option value="NY">New York (Next Gen)</option>
              <option value="NC">North Carolina (SCOS)</option>
              <option value="OH">Ohio (Learning Standards)</option>
              <option value="PA">Pennsylvania (Academic Standards)</option>
              <option value="VA">Virginia (SOL)</option>
            </select>
          </div>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-award"></i> Find Standards (Standards Satchel)</button>
      </form>
      <div class="result" id="standardsResult"></div>
    </div>
  </div>

</div><!-- /container -->

<footer>
  <p>© 2026 EdTech Labs • Science of Reading Teacher-First Workspace</p>
  <p style="font-size:0.8rem;color:var(--md-sys-color-secondary);margin-top:0.4rem">🔒 Student names are removed before processing • Nothing is stored • See "How Student Data Is Handled"</p>
</footer>

<script>
var FRAMEWORKS = {FRAMEWORKS_JSON};
var PAPERS = {PAPERS_JSON};
var PILLAR_FINDINGS = {PILLAR_FINDINGS_JSON};

var TAB_NAMES = {{
  "tab-diagnose": "Step 1: MTSS Screener & Remediation",
  "tab-decodable": "Step 2: Decodable Text Checker",
  "tab-phonics": "Step 3: Phonics Routine Builder",
  "tab-auditor": "Step 4: Visual Audit Inspector",
  "tab-vocab": "Classify Vocabulary",
  "tab-standards": "Standards Alignment"
}};

// Context-Aware Content Dictionary for Left Pull-Out Drawer
var CONTEXT_GUIDES = {{
  "tab-diagnose": {{
    title: "🎯 Step 1: MTSS Screener Guide",
    research: {{
      title: "Gough & Tunmer (1986), Decoding, Reading, and Reading Disability",
      summary: "Reading comprehension depends on both word recognition (decoding) and language comprehension; a weakness in either limits reading. Screening profiles help target assessment and instruction but are not diagnoses.",
      doi: "https://doi.org/10.1177/074193258600700104"
    }},
    concepts: [
      {{ term: "Simple View of Reading", def: "Reading Comprehension (R) = Decoding (D) x Language Comprehension (LC)." }},
      {{ term: "Nonsense Word Fluency (NWF)", def: "Measures decoding of unfamiliar letter strings, so students can't rely on memorized words." }},
      {{ term: "CASE Network GUIDs", def: "1EdTech open standard linking learning goals directly to state framework standard codes." }}
    ]
  }},
  "tab-decodable": {{
    title: "📖 Step 2: Decodability & Scope Guide",
    research: {{
      title: "Ehri, Nunes, Stahl & Willows (2001), NRP phonics meta-analysis",
      summary: "Systematic phonics instruction outperformed unsystematic or no phonics (d = 0.41 overall), with larger effects when begun in kindergarten or first grade (d = 0.55) than later (d = 0.27).",
      doi: "https://doi.org/10.3102/00346543071003393"
    }},
    concepts: [
      {{ term: "Decodable Text", def: "Passages matching previously taught sound-spelling correspondences to prevent guessing." }},
      {{ term: "Off-Scope Words", def: "Words containing untaught phonics patterns which students cannot yet decode systematically." }},
      {{ term: "Heart Words", def: "High-frequency words with temporary or permanent irregular spelling parts pre-taught using orthographic mapping." }}
    ]
  }},
  "tab-phonics": {{
    title: "🧩 Step 3: Explicit Phonics Routine Guide",
    research: {{
      title: "Foorman et al. (2016), WWC Foundational Skills Practice Guide",
      summary: "Recommends teaching students to decode words, analyze word parts, and write and recognize words (strong evidence), with explicit modeling and practice.",
      doi: "https://ies.ed.gov/ncee/wwc/PracticeGuide/21"
    }},
    concepts: [
      {{ term: "I DO (Teacher Model)", def: "Clear explicit demonstration with think-aloud modeling of sound-spelling correspondences." }},
      {{ term: "WE DO (Guided Practice)", def: "Teacher and students practice together with immediate corrective feedback." }},
      {{ term: "YOU DO (Independent)", def: "Students demonstrate independent mastery through word building and chaining." }}
    ]
  }},
  "tab-auditor": {{
    title: "🔍 Step 4: Anti-Cueing Audit Guide",
    research: {{
      title: "Ehri (2014), Orthographic Mapping; Kilpatrick (2015)",
      summary: "Skilled word reading depends on connecting a word's letters to its sounds (orthographic mapping). Three-cueing (MSV) prompts steer students to guess from pictures or context instead of decoding.",
      doi: "https://doi.org/10.1080/10888438.2013.819356"
    }},
    concepts: [
      {{ term: "Anti-Cueing Guardrail", def: "Flagging and eliminating prompts that encourage guessing from pictures or initial letters." }},
      {{ term: "Sound-by-Sound Breakdown", def: "Each word split into its letters or letter teams and the sound each one spells (e.g. ch - a - t → /ch/ /ă/ /t/)." }}
    ]
  }},
  "tab-vocab": {{
    title: "📚 Three-Tier Vocabulary Guide",
    research: {{
      title: "Beck, McKeown & Kucan (2013); Marulis & Neuman (2010)",
      summary: "The three-tier model prioritizes high-utility Tier 2 words for instruction. A meta-analysis of vocabulary interventions for pre-K and kindergarten children found large gains in word learning (g = 0.88).",
      doi: "https://doi.org/10.3102/0034654310377077"
    }},
    concepts: [
      {{ term: "Tier 1", def: "Basic conversational words." }},
      {{ term: "Tier 2", def: "High-utility cross-domain academic words." }},
      {{ term: "Tier 3", def: "Domain-specific technical terms." }}
    ]
  }},
  "tab-standards": {{
    title: "🏛️ Standards Satchel CASE® Guide",
    research: {{
      title: "1EdTech CASE® Specification & Common Good Learning Tools",
      summary: "Interoperable academic standards mapping across 50 state frameworks.",
      doi: "https://rosetta.commongoodlt.com/"
    }},
    concepts: [
      {{ term: "Standards Satchel", def: "Rosetta framework portal hosted by Common Good Learning Tools." }}
    ]
  }}
}};

function sanitizeClientPII(inputStr, extraNames) {{
  if (typeof inputStr !== 'string') return inputStr;
  var cleaned = inputStr;
  var detected = [];

  var idPatterns = [
    [/[\\w.+-]+@[\\w-]+\\.[\\w.-]+/g, '[EMAIL_REDACTED]', 'Email'],
    [/\\b(?:\\+?1[\\s.-]?)?\\(?\\d{{3}}\\)?[\\s.-]\\d{{3}}[\\s.-]\\d{{4}}\\b/g, '[PHONE_REDACTED]', 'Phone'],
    [/\\b\\d{{1,2}}[\\/-]\\d{{1,2}}[\\/-]\\d{{2,4}}\\b/g, '[DATE_REDACTED]', 'Date'],
    [/\\b[A-Z]{{2,3}}-?\\d{{4,}}\\b/g, '[ID_REDACTED]', 'Student ID'],
    [/\\b\\d{{6,}}\\b/g, '[ID_REDACTED]', 'Student ID']
  ];
  idPatterns.forEach(function(p) {{
    if (p[0].test(cleaned)) {{
      detected.push(p[2]);
      cleaned = cleaned.replace(p[0], p[1]);
    }}
  }});

  var nameField = document.getElementById('studentNameInput');
  var names = (extraNames || []).concat(nameField && nameField.value ? [nameField.value] : []);
  var parts = [];
  names.forEach(function(n) {{
    String(n).split(/[\\s,]+/).forEach(function(part) {{ if (part.length >= 2) parts.push(part); }});
  }});
  parts.sort(function(a, b) {{ return b.length - a.length; }});
  parts.forEach(function(part) {{
    var rx = new RegExp('\\\\b' + part.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + '\\\\b', 'gi');
    if (rx.test(cleaned)) {{
      if (detected.indexOf('Student Name') === -1) detected.push('Student Name');
      cleaned = cleaned.replace(rx, '[STUDENT]');
    }}
  }});

  if (detected.length > 0) {{
    showToast('🔒 Removed before sending: ' + detected.filter(function(v, i, a) {{ return a.indexOf(v) === i; }}).join(', ') + '.');
  }}
  return cleaned;
}}

function showToast(msg) {{
  var container = document.getElementById('toastContainer');
  var toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = '<i class="fa-solid fa-shield-halved" style="color:#4CAF50"></i> <span>' + msg + '</span>';
  container.appendChild(toast);
  setTimeout(function() {{
    toast.style.opacity = '0';
    setTimeout(function() {{ toast.remove(); }}, 300);
  }}, 4000);
}}

function openFerpaModal() {{
  document.getElementById('ferpaModalBackdrop').classList.add('open');
  document.getElementById('ferpaModal').style.display = 'block';
}}

function closeFerpaModal() {{
  document.getElementById('ferpaModalBackdrop').classList.remove('open');
  document.getElementById('ferpaModal').style.display = 'none';
}}

function updateGCConnectionStatus() {{
  var token = document.getElementById('gcAccessToken').value;
  var pill = document.getElementById('gcConnectionStatusPill');
  if (token && token.trim().length > 10) {{
    pill.innerHTML = '<span class="scope-tag" style="background:#E8F5E9;color:#1B5E20"><i class="fa-solid fa-lock"></i> 🔒 Connected to Live Google Classroom API</span>';
  }} else {{
    pill.innerHTML = '<span class="scope-tag" style="background:#FFF3E0;color:#E65100"><i class="fa-solid fa-bolt"></i> ⚡ Demo Simulation Mode Active</span>';
  }}
}}

function openGCModal(title, content) {{
  document.getElementById('gcTitle').value = title || 'Decodable Reading Assignment';
  document.getElementById('gcContent').value = content || document.getElementById('decodeText').value;
  document.getElementById('gcModalSuccess').style.display = 'none';
  document.getElementById('gcPublishForm').style.display = 'block';
  updateGCConnectionStatus();
  document.getElementById('gcModalBackdrop').classList.add('open');
  document.getElementById('gcModal').style.display = 'block';
  fetchGCCourses();
}}

function closeGCModal() {{
  document.getElementById('gcModalBackdrop').classList.remove('open');
  document.getElementById('gcModal').style.display = 'none';
}}

async function fetchGCCourses() {{
  var token = document.getElementById('gcAccessToken').value;
  var headers = token ? {{'Authorization': 'Bearer ' + token}} : {{}};
  try {{
    var resp = await fetch('/api/v1/google-classroom/courses', {{headers: headers}});
    var data = await resp.json();
    if (data.courses && data.courses.length > 0) {{
      var select = document.getElementById('gcCourseSelect');
      select.innerHTML = '';
      data.courses.forEach(function(c) {{
        var opt = document.createElement('option');
        opt.value = c.id;
        opt.innerText = c.name + (c.section ? ' (' + c.section + ')' : '');
        select.appendChild(opt);
      }});
    }}
  }} catch(e) {{ console.error('Course fetch error:', e); }}
}}

document.getElementById('gcPublishForm').addEventListener('submit', async function(e) {{
  e.preventDefault();
  var payload = {{
    course_id: document.getElementById('gcCourseSelect').value,
    title: document.getElementById('gcTitle').value,
    description: document.getElementById('gcContent').value,
    points: parseFloat(document.getElementById('gcPoints').value),
    access_token: document.getElementById('gcAccessToken').value
  }};

  var resp = await fetch('/api/v1/google-classroom/publish', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(payload)
  }});
  var r = await resp.json();
  if (r.status === 'published') {{
    document.getElementById('gcPublishForm').style.display = 'none';
    document.getElementById('gcOutboundLink').href = r.alternateLink || 'https://classroom.google.com';
    document.getElementById('gcModalSuccess').style.display = 'block';
    showToast('🎓 Successfully published assignment to Google Classroom!');
  }} else {{
    alert('Failed to publish: ' + (r.detail || 'Unknown error'));
  }}
}});

var SCOPE_UNITS = {{}};

async function populateUnits() {{
  var grade = document.getElementById('scopeGrade').value;
  var sel = document.getElementById('scopeUnit');
  try {{
    if (!SCOPE_UNITS[grade]) {{
      var resp = await fetch('/api/scope_units?grade=' + encodeURIComponent(grade));
      SCOPE_UNITS[grade] = (await resp.json()).units || [];
    }}
    var current = sel.value;
    sel.innerHTML = SCOPE_UNITS[grade].map(function(u) {{
      return '<option value="' + u.unit + '">Unit ' + u.unit + ': ' + u.title + '</option>';
    }}).join('');
    if (current && sel.querySelector('option[value="' + current + '"]')) sel.value = current;
  }} catch(e) {{
    console.error('Unit list error:', e);
  }}
}}

async function fetchPhonicsScope() {{
  var grade = document.getElementById('scopeGrade').value;
  var unit = document.getElementById('scopeUnit').value || '1';

  try {{
    var resp = await fetch('/api/phonics_scope?grade=' + encodeURIComponent(grade) + '&unit=' + encodeURIComponent(unit));
    var data = await resp.json();

    var graphemes = (data.taught_graphemes || []).join(', ');
    var heart = (data.heart_words || []).map(function(w){{ return typeof w === 'object' ? w.word : w; }}).join(', ');

    document.getElementById('newPatternsSpan').innerText = (data.new_patterns || []).join('; ') || '—';
    document.getElementById('taughtGraphemesSpan').innerText = graphemes || 'None';
    document.getElementById('heartWordsSpan').innerText = heart || 'None';
  }} catch(e) {{
    console.error('Scope fetch error:', e);
  }}
}}

function switchTab(tabId) {{
  var tabs = document.querySelectorAll('.m3-tab-btn');
  var panes = document.querySelectorAll('.tab-pane');
  var quadrants = document.querySelectorAll('.quadrant-card');

  tabs.forEach(function(t) {{ t.classList.remove('active'); }});
  panes.forEach(function(p) {{ p.classList.remove('active'); }});
  quadrants.forEach(function(q) {{ q.classList.remove('active'); }});

  var selectedTab = document.querySelector('.m3-tab-btn[data-tab="' + tabId + '"]');
  var selectedPane = document.getElementById(tabId);
  if (selectedTab && selectedPane) {{
    selectedTab.classList.add('active');
    selectedPane.classList.add('active');
  }}

  var quadMap = {{
    'tab-diagnose': 'quadrant-remediation',
    'tab-decodable': 'quadrant-decodable',
    'tab-phonics': 'quadrant-phonics',
    'tab-auditor': 'quadrant-auditor'
  }};
  var activeQuadId = quadMap[tabId];
  if (activeQuadId && document.getElementById(activeQuadId)) {{
    document.getElementById(activeQuadId).classList.add('active');
  }}

  updateDrawerContent(tabId);
}}

function updateDrawerContent(tabId) {{
  var guide = CONTEXT_GUIDES[tabId] || CONTEXT_GUIDES['tab-diagnose'];
  var tabName = TAB_NAMES[tabId] || 'Step 1: MTSS Screener & Remediation';

  document.getElementById('drawerTitle').innerText = guide.title;
  document.getElementById('drawerSubTitle').innerText = 'Viewing Tool: ' + tabName;

  var html = '';
  html += '<div style="background:var(--md-sys-color-primary-container);color:var(--md-sys-color-on-primary-container);padding:0.65rem 1rem;border-radius:var(--md-shape-corner-medium);margin-bottom:1.2rem;font-size:0.88rem;font-weight:700;display:flex;align-items:center;gap:0.6rem">';
  html += '<i class="fa-solid fa-compass" style="color:var(--md-sys-color-primary);font-size:1.1rem"></i> Active Tab Context: ' + tabName;
  html += '</div>';

  html += '<div class="drawer-section">';
  html += '<div class="drawer-section-title"><i class="fa-solid fa-flask"></i> Theoretical & Research Basis</div>';
  html += '<strong style="font-size:0.9rem;color:#1C1B1F">' + guide.research.title + '</strong>';
  html += '<p style="font-size:0.86rem;color:#444;margin-top:0.3rem">' + guide.research.summary + '</p>';
  if (guide.research.doi) {{
    html += '<a href="' + guide.research.doi + '" target="_blank" style="display:inline-flex;align-items:center;gap:0.4rem;font-size:0.78rem;color:var(--md-sys-color-primary);font-weight:700;margin-top:0.5rem;text-decoration:underline"><i class="fa-solid fa-arrow-up-right-from-square"></i> Read Original Citation</a>';
  }}
  html += '</div>';

  html += '<div class="drawer-section" style="border-left-color:var(--md-sys-color-tertiary)">';
  html += '<div class="drawer-section-title" style="color:var(--md-sys-color-tertiary)"><i class="fa-solid fa-book-bookmark"></i> Tool Concepts & Key Vocabulary</div>';
  guide.concepts.forEach(function(c) {{
    html += '<div class="drawer-concept-item">';
    html += '<div class="drawer-concept-term">' + c.term + '</div>';
    html += '<div class="drawer-concept-def">' + c.def + '</div>';
    html += '</div>';
  }});
  html += '</div>';

  document.getElementById('sidebarDynamicContent').innerHTML = html;
}}

var sidebar = document.getElementById('sidebar');
var backdrop = document.getElementById('sidebarBackdrop');
var toggle = document.getElementById('sidebarToggle');
var isOpen = false;

function openSidebar() {{
  isOpen = true;
  var activePane = document.querySelector('.tab-pane.active');
  var activeTabId = activePane ? activePane.id : 'tab-diagnose';
  updateDrawerContent(activeTabId);
  sidebar.classList.add('open');
  backdrop.classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function closeSidebar() {{
  isOpen = false;
  sidebar.classList.remove('open');
  backdrop.classList.remove('open');
  document.body.style.overflow = '';
}}

toggle.addEventListener('click', function(e) {{
  e.stopPropagation();
  if(isOpen) closeSidebar(); else openSidebar();
}});

backdrop.addEventListener('click', closeSidebar);

var PRESETS = {{
  nwf_low: {{ decoding: 0.35, comprehension: 0.80, skills: ['cvc_mixed'], label: 'low nonsense-word fluency; diagnostic showed short-vowel CVC errors' }},
  phoneme_segmentation: {{ decoding: 0.28, comprehension: 0.75, skills: ['phoneme_segmentation'], label: 'phoneme segmentation difficulty' }},
  vowel_teams: {{ decoding: 0.42, comprehension: 0.85, skills: ['vowel_teams'], label: 'vowel team errors' }},
  consonant_blends: {{ decoding: 0.38, comprehension: 0.82, skills: ['consonant_blends'], label: 'consonant blend errors' }}
}};

function autofillDeficitScores() {{
  var val = document.getElementById('hb538Deficit').value;
  var pill = document.getElementById('presetSummaryPill');
  var skillSel = document.getElementById('diagnosedSkills');
  var preset = PRESETS[val];
  if (preset) {{
    document.getElementById('decoding').value = preset.decoding.toFixed(2);
    document.getElementById('comprehension').value = preset.comprehension.toFixed(2);
    Array.prototype.forEach.call(skillSel.options, function(o) {{ o.selected = preset.skills.indexOf(o.value) !== -1; }});
    if (pill) pill.innerHTML = '<i class="fa-solid fa-circle-check"></i> Example loaded (illustrative scores): ' + preset.label + '.';
  }} else {{
    if (pill) pill.innerHTML = '<i class="fa-solid fa-circle-info"></i> Enter your own scores, set the cutoff to your screener\\'s benchmark, and choose any skills a diagnostic identified.';
  }}
}}

function toggleInspectorEditable(targetId) {{
  var resEl = document.getElementById(targetId);
  if (!resEl) return;
  var container = resEl.querySelector('.inspector-word-container');
  if (!container) return;
  
  if (container.contentEditable === 'true') {{
    container.contentEditable = 'false';
    container.style.border = '1px solid var(--md-sys-color-outline-variant)';
    showToast('🔒 Locked text in place.');
  }} else {{
    container.contentEditable = 'true';
    container.style.border = '2px dashed #E65100';
    container.focus();
    showToast('✏️ Text is now editable in place. Click badges to edit text directly!');
  }}
}}

function escapeHtml(str) {{
  return String(str).replace(/[&<>"']/g, function(c) {{
    return {{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}}[c];
  }});
}}

var STATUS_STYLE = {{
  decodable: ['badge-decodable', '🟢 Decodable'],
  heart_word: ['badge-heart', '💛 Taught heart word'],
  not_yet_decodable: ['badge-offscope', '🔴 Not yet decodable'],
  irregular: ['badge-offscope', '🔴 Irregular, not yet taught as a heart word'],
  not_in_dictionary: ['badge-offscope', '⚪ Not in dictionary: check by hand']
}};

function renderDecodableInspector(r, targetId) {{
  var resEl = document.getElementById(targetId);
  if (r.error_code) {{
    resEl.innerHTML = '<p style="color:#B3261E"><strong>Error:</strong> ' + escapeHtml(r.error_message || r.error_code) + '</p>';
    resEl.classList.add('show');
    return;
  }}
  var byWord = {{}};
  (r.words || []).forEach(function(w) {{ byWord[w.word.toLowerCase()] = w; }});
  var cueing = r.cueing_flags || [];
  var counts = r.counts || {{}};

  var html = '<h3 style="color:var(--md-sys-color-primary);margin-bottom:0.8rem"><i class="fa-solid fa-microscope"></i> Decodability Report: Grade ' + escapeHtml(r.grade_level) + ', Unit ' + escapeHtml(r.unit) + (r.unit_title ? ' (' + escapeHtml(r.unit_title) + ')' : '') + '</h3>';

  html += '<div class="audit-metrics-bar">';
  html += '<div><div class="audit-metric-num">' + r.decodable_pct + '%</div><div class="audit-metric-label">Decodable with taught patterns</div></div>';
  html += '<div><div class="audit-metric-num">' + r.accessible_pct + '%</div><div class="audit-metric-label">Decodable + taught heart words (target ' + r.target_pct + '%)</div></div>';
  html += '<div><div class="audit-metric-num">' + r.total_words + '</div><div class="audit-metric-label">Total words</div></div>';
  if (cueing.length) {{
    html += '<div><div class="audit-metric-num" style="color:#B3261E"><i class="fa-solid fa-triangle-exclamation"></i> ' + cueing.length + '</div><div class="audit-metric-label">Three-cueing prompts found</div></div>';
  }} else {{
    html += '<div><div class="audit-metric-num" style="color:#2E7D32"><i class="fa-solid fa-check-circle"></i> None</div><div class="audit-metric-label">Three-cueing prompts</div></div>';
  }}
  html += '</div>';

  var text = r.text || document.getElementById('decodeText').value;
  var tokens = text.split(/([A-Za-z]+(?:'[A-Za-z]+)?)/);
  html += '<div class="inspector-word-container">';
  tokens.forEach(function(tok) {{
    var info = byWord[tok.toLowerCase()];
    if (!info) {{ html += escapeHtml(tok); return; }}
    var style = STATUS_STYLE[info.status] || STATUS_STYLE.not_in_dictionary;
    var tip = style[1];
    if (info.breakdown) tip += ': ' + info.breakdown;
    if (info.missing_patterns && info.missing_patterns.length) tip += ' | Needs: ' + info.missing_patterns.join('; ');
    html += '<span class="word-badge ' + style[0] + '">' + escapeHtml(tok) + '<span class="tooltip">' + escapeHtml(tip) + '</span></span>';
  }});
  html += '</div>';

  var missing = r.missing_patterns || {{}};
  var missingKeys = Object.keys(missing);
  if (missingKeys.length || (r.irregular_words || []).length || (r.not_in_dictionary_words || []).length) {{
    html += '<div style="margin-top:1rem;padding:1rem;background:#FFF8E1;border-radius:var(--md-shape-corner-medium);border-left:4px solid #F9A825">';
    html += '<strong>What blocks this passage</strong><ul style="margin:0.5rem 0 0 1.2rem">';
    missingKeys.forEach(function(k) {{ html += '<li>Untaught pattern <strong>' + escapeHtml(k) + '</strong>: ' + escapeHtml(missing[k].join(', ')) + '</li>'; }});
    if ((r.irregular_words || []).length) html += '<li>Irregular words not yet taught as heart words: ' + escapeHtml(r.irregular_words.join(', ')) + '</li>';
    if ((r.not_in_dictionary_words || []).length) html += '<li>Check by hand (not in the pronunciation dictionary): ' + escapeHtml(r.not_in_dictionary_words.join(', ')) + '</li>';
    html += '</ul></div>';
  }}

  if (cueing.length) {{
    html += '<div style="margin-top:1rem;padding:1rem;background:#FDECEA;border-radius:var(--md-shape-corner-medium);border-left:4px solid #B3261E">';
    html += '<strong>Three-cueing prompts to replace</strong><ul style="margin:0.5rem 0 0 1.2rem">';
    cueing.forEach(function(f) {{
      html += '<li>"' + escapeHtml(f.matched_text) + '": ' + escapeHtml(f.why) + ' <em>Try instead:</em> "' + escapeHtml(f.suggested_prompt) + '"</li>';
    }});
    html += '</ul></div>';
  }}

  html += '<p style="font-size:0.78rem;color:var(--md-sys-color-secondary);margin-top:0.8rem">' + escapeHtml(r.method || '') + ' Scope source: ' + escapeHtml(r.scope_source || '') + '.</p>';

  html += '<div class="export-bar">';
  html += '<button onclick="window.print()" class="export-btn"><i class="fa-solid fa-print"></i> 🖨️ Print Student Sheet</button>';
  html += '<button onclick="downloadAsPDF(' + "'" + targetId + "'" + ')" class="export-btn"><i class="fa-solid fa-file-pdf"></i> 📄 Download PDF</button>';
  html += '<button onclick="copyResultText(' + "'" + targetId + "'" + ')" class="export-btn"><i class="fa-solid fa-copy"></i> 📋 Copy Plain Text</button>';
  html += '<button onclick="toggleInspectorEditable(' + "'" + targetId + "'" + ')" class="export-btn" style="background:#FFF3E0;color:#E65100"><i class="fa-solid fa-pen-to-square"></i> ✏️ Edit Text in Place</button>';
  html += '<button onclick="openGCModal(' + "'Decodable Text Practice'" + ', document.getElementById(' + "'decodeText'" + ').value)" class="export-btn" style="background:#EADDFF;color:#21005D"><i class="fa-solid fa-graduation-cap"></i> 🎓 Export to Google Classroom</button>';
  html += '</div>';

  resEl.innerHTML = html;
  resEl.classList.add('show');
}}

function copyResultText(elementId) {{
  var el = document.getElementById(elementId);
  var text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text);
  showToast('📋 Copied plain text to clipboard!');
}}

function downloadAsPDF(elementId) {{
  window.print();
}}

document.getElementById('decodableGeneratorForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var rawText = document.getElementById('decodeText').value;
  var text = sanitizeClientPII(rawText);

  var grade = document.getElementById('scopeGrade').value;
  var unit = document.getElementById('scopeUnit').value;

  var resp = await fetch('/api/decodability', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{text: text, grade: grade, unit: unit}})
  }});
  var r = await resp.json();
  renderDecodableInspector(r, 'decodeResult');
}});

document.getElementById('phonicsRoutineForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var rawPhoneme = document.getElementById('targetPhoneme').value;
  var phoneme = sanitizeClientPII(rawPhoneme);
  var cue = document.getElementById('multisensoryCue').value;

  var resp = await fetch('/api/phonics_routine', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{target_phoneme: phoneme, grade: '1st', multisensory: cue}})
  }});
  var r = await resp.json();
  
  var html = '<h3 style="color:var(--md-sys-color-primary);margin-bottom:1rem"><i class="fa-solid fa-puzzle-piece"></i> 5-Day Explicit Phonics Routine Script</h3>';
  html += '<div style="background:var(--md-sys-color-surface-variant);padding:1.4rem;border-radius:var(--md-shape-corner-medium);white-space:pre-wrap;font-family:monospace;line-height:1.6">' + r.routine + '</div>';
  html += '<div class="export-bar"><button onclick="window.print()" class="export-btn"><i class="fa-solid fa-print"></i> 🖨️ Print Student Sheet</button><button onclick="copyResultText(' + "'phonicsRoutineResult'" + ')" class="export-btn"><i class="fa-solid fa-copy"></i> 📋 Copy Plain Text</button><button onclick="openGCModal(' + "'Explicit Phonics Routine'" + ', r.routine)" class="export-btn" style="background:#EADDFF;color:#21005D"><i class="fa-solid fa-graduation-cap"></i> 🎓 Export to Google Classroom</button></div>';

  var resEl = document.getElementById('phonicsRoutineResult');
  resEl.innerHTML = html;
  resEl.classList.add('show');
}});

document.getElementById('diagnoseForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  document.getElementById('spinner').classList.add('show');
  document.getElementById('result').classList.remove('show');

  var sanitizedName = document.getElementById('studentNameInput').value.trim();

  var skills = Array.prototype.filter.call(document.getElementById('diagnosedSkills').options, function(o) {{ return o.selected; }}).map(function(o) {{ return o.value; }});
  var data = {{
    decoding: parseFloat(document.getElementById('decoding').value),
    comprehension: parseFloat(document.getElementById('comprehension').value),
    cutoff: parseFloat(document.getElementById('cutoff').value),
    diagnosed_skills: skills,
    grade: document.getElementById('grade').value,
    student_name: sanitizedName ? '[STUDENT]' : ''
  }};

  try {{
    var resp = await fetch('/tools/evaluate_simple_view', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(data)
    }});
    var result = await resp.json();
    if (result.error) return alert('Error: ' + result.error);
    renderResult(result);
  }} catch(err) {{
    alert('Connection error: ' + err.message);
  }} finally {{
    document.getElementById('spinner').classList.remove('show');
  }}
}});

function renderResult(r) {{
  var profile = r.diagnostic;
  var badges = {{
    'on_track': '<span class="profile-badge profile-typical">✅ On Track</span>',
    'word_recognition_difficulty': '<span class="profile-badge profile-dyslexia">⚠️ Word-Recognition Difficulty</span>',
    'language_comprehension_difficulty': '<span class="profile-badge profile-hyperlexic">📚 Language-Comprehension Difficulty</span>',
    'mixed_difficulty': '<span class="profile-badge profile-garden">🔶 Mixed Difficulty</span>'
  }};

  var html = '<h3>' + badges[profile.reading_profile] + '</h3>';
  html += '<p style="margin:0.4rem 0">' + escapeHtml(profile.profile_label) + ' (cutoff ' + profile.cutoff.toFixed(2) + ').</p>';
  if (profile.near_cutoff) html += '<p style="color:#E65100;margin:0.4rem 0"><strong>Near the cutoff:</strong> this profile is uncertain; confirm with another measure.</p>';
  html += '<div class="stats-grid">';
  html += '<div class="stat"><div class="stat-num">' + (profile.decoding_score*100).toFixed(0) + '%</div><div class="stat-label">Decoding</div></div>';
  html += '<div class="stat"><div class="stat-num">' + (profile.language_comprehension_score*100).toFixed(0) + '%</div><div class="stat-label">Language Comprehension</div></div>';
  html += '<div class="stat"><div class="stat-num">' + profile.deficit_codes.length + '</div><div class="stat-label">Diagnosed Skills</div></div>';
  html += '<div class="stat"><div class="stat-num">' + r.remediations.length + '</div><div class="stat-label">Intervention Cards</div></div>';
  html += '</div>';
  html += '<p style="font-size:0.82rem;padding:0.8rem;background:#F3EDF7;border-radius:var(--md-shape-corner-small)"><strong>Screening, not diagnosis:</strong> ' + escapeHtml(r.caveat || '') + '</p>';
  (r.warnings || []).forEach(function(w) {{ html += '<p style="font-size:0.82rem;color:#E65100">⚠️ ' + escapeHtml(w) + '</p>'; }});

  document.getElementById('profileArea').innerHTML = html;

  var cardsHtml = '';
  if (r.remediations.length) {{
    cardsHtml = '<h3 style="margin-top:1.5rem;color:var(--md-sys-color-primary)">📋 Intervention Cards for Diagnosed Skills</h3>';
    r.remediations.forEach(function(card){{
      cardsHtml += '<div class="remediation-card">' + renderMarkdownCard(card) + '</div>';
    }});
  }}
  document.getElementById('remediationArea').innerHTML = cardsHtml;
  document.getElementById('nextSteps').innerHTML = '<p style="margin-top:1rem;padding:1.2rem;background:var(--md-sys-color-surface-variant);border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)"><strong>📝 Next Steps:</strong> ' + escapeHtml(r.next_steps) + '</p>';
  document.getElementById('result').classList.add('show');
  document.getElementById('result').scrollIntoView({{behavior: 'smooth'}});
}}

function renderMarkdownCard(card) {{
  var md = typeof card === 'string' ? card : card.markdown || JSON.stringify(card);
  var html = md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
    .replace(/^> (.+)$/gm, '<blockquote style="color:#555;font-style:italic;border-left:3px solid var(--md-sys-color-tertiary);padding-left:1rem;margin:.5rem 0">$1</blockquote>')
    .replace(/^🔵 (.+)$/gm, '<div class="script-line script-i">🔵 <strong>I DO:</strong> $1</div>')
    .replace(/^🟡 (.+)$/gm, '<div class="script-line script-we">🟡 <strong>WE DO:</strong> $1</div>')
    .replace(/^🟢 (.+)$/gm, '<div class="script-line script-you">🟢 <strong>YOU DO:</strong> $1</div>')
    .replace(/^❌ (.+)$/gm, '<div class="feedback feedback-error">❌ $1</div>')
    .replace(/^✅ (.+)$/gm, '<div class="feedback feedback-praise">✅ $1</div>')
    .replace(/\\n\\n/g, '<br><br>')
    .replace(/\\n/g, '<br>');

  return html;
}}

document.getElementById('auditorForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var rawText = document.getElementById('auditText').value;
  var text = sanitizeClientPII(rawText);

  var resp = await fetch('/api/decodability', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{text: text, grade: document.getElementById('scopeGrade').value, unit: document.getElementById('scopeUnit').value || '1'}})
  }});
  var r = await resp.json();
  renderDecodableInspector(r, 'auditResult');
}});

document.getElementById('vocabForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var rawText = document.getElementById('vocabText').value;
  var text = sanitizeClientPII(rawText);

  var resp = await fetch('/api/vocabulary', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{text: text}})
  }});
  var r = await resp.json();

  var summary = r.tier_summary || {{}};
  var t1Count = summary.tier_1 ? summary.tier_1.count : (r.tier_counts ? r.tier_counts.tier_1 : 0);
  var t2Count = summary.tier_2 ? summary.tier_2.count : (r.tier_counts ? r.tier_counts.tier_2 : 0);
  var t3Count = summary.tier_3 ? summary.tier_3.count : (r.tier_counts ? r.tier_counts.tier_3 : 0);
  var totalWords = r.total_words || 0;

  var html = '<h3 style="margin-top:1rem;color:var(--md-sys-color-primary)">📚 Three-Tier Vocabulary Breakdown</h3>';
  html += '<div class="stats-grid">';
  html += '<div class="stat"><div class="stat-num">' + t1Count + '</div><div class="stat-label">Tier 1 (Basic)</div></div>';
  html += '<div class="stat"><div class="stat-num">' + t2Count + '</div><div class="stat-label">Tier 2 (Academic)</div></div>';
  html += '<div class="stat"><div class="stat-num">' + t3Count + '</div><div class="stat-label">Tier 3 (Domain)</div></div>';
  html += '<div class="stat"><div class="stat-num">' + totalWords + '</div><div class="stat-label">Total Words</div></div>';
  html += '</div>';

  if (r.tier_2_words && r.tier_2_words.length > 0) {{
    var t2List = r.tier_2_words.map(function(w){{ return '<strong>' + w.word + '</strong> (x' + w.count + ')'; }}).join(', ');
    html += '<p style="color:var(--md-sys-color-primary);margin-top:0.8rem;padding:0.9rem;background:var(--md-sys-color-primary-container);border-radius:var(--md-shape-corner-medium)"><strong>🎯 Tier 2 (Academic) Words to Pre-Teach:</strong> ' + t2List + '</p>';
  }}
  document.getElementById('vocabResult').innerHTML = html;
  document.getElementById('vocabResult').classList.add('show');
}});

document.getElementById('standardsForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var rawSkill = document.getElementById('standardsSkill').value;
  var skill = sanitizeClientPII(rawSkill);

  var data = {{description: skill, state: document.getElementById('standardsState').value}};
  var resp = await fetch('/api/standards', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var r = await resp.json();

  var html = '<h3 style="margin-top:1rem;color:var(--md-sys-color-primary)">🏛️ Standards Matches for ' + r.state + ' (' + r.total_matches + ')</h3>';
  (r.notices || []).forEach(function(n) {{ html += '<p style="font-size:0.84rem;color:#E65100;margin:0.4rem 0">⚠️ ' + escapeHtml(n) + '</p>'; }});
  (r.matches||[]).forEach(function(m){{
    var deepLink = m.url || ('https://rosetta.commongoodlt.com/#/search?q=' + encodeURIComponent(m.code));
    html += '<div style="background:var(--md-sys-color-surface-variant);padding:1.2rem;margin:.8rem 0;border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)">';
    html += '<strong style="color:#1C1B1F;font-size:1.1rem">' + escapeHtml(m.code) + (m.title ? ' — ' + escapeHtml(m.title) : '') + '</strong>';
    html += '<p style="font-size:.95rem;color:#333;margin-top:.4rem">' + escapeHtml(m.description) + '</p>';
    html += '<a href="' + deepLink + '" target="_blank" class="export-btn" style="margin-top:0.6rem;display:inline-flex"><i class="fa-solid fa-award"></i> Open 1EdTech CASE® Record (' + escapeHtml(m.code) + ')</a>';
    html += '</div>';
  }});

  document.getElementById('standardsResult').innerHTML = html;
  document.getElementById('standardsResult').classList.add('show');
}});

// Fetch initial scope on page load (< 200ms)
populateUnits().then(function() {{
  var sel = document.getElementById('scopeUnit');
  if (sel.querySelector('option[value="3"]')) sel.value = '3';
  fetchPhonicsScope();
}});
</script>
</body>
</html>"""


# ── API Routes (Stories 1–6) ───────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=build_frontend(), headers={"Cache-Control": "no-cache"})


@app.get("/api/phonics_scope")
@app.get("/tools/get_phonics_scope")
async def phonics_scope_route(grade: str = "1", unit: str = "1"):
    """Story 1: Fetch phonics scope and sequence (< 200ms)."""
    return await get_phonics_scope(grade_level=grade, unit=unit)


@app.post("/api/phonics_routine")
@app.post("/tools/explicit_phonics_routine")
async def phonics_routine_route(data: dict):
    """Story 1 & 3: Generate explicit phonics routine."""
    target_phoneme = data.get("target_phoneme", "/sh/")
    grade = data.get("grade", "1st")
    multisensory = data.get("multisensory", "finger tapping")
    routine = await explicit_phonics_routine(target_phoneme=target_phoneme, grade=grade, multisensory=multisensory)
    return {"status": "ok", "routine": routine}


@app.post("/api/diagnose")
@app.post("/tools/evaluate_simple_view")
async def diagnose(data: dict):
    """Story 4 & 5: Simple View screening profile + intervention cards for diagnosed skills."""
    decoding = data.get("decoding", data.get("decoding_score", 0.5))
    comprehension = data.get("comprehension", data.get("language_comp_score", data.get("language_comprehension", 0.5)))
    grade = data.get("grade", data.get("student_grade", "1st"))
    student_name = data.get("student_name", "")
    cutoff = data.get("cutoff")
    diagnosed_skills = data.get("diagnosed_skills") or []

    sanitized_input = sanitize_pii({"student_name": student_name})
    clean_name = sanitized_input.get("student_token", "Anonymous Student")

    try:
        result = evaluate_simple_view(
            decoding=float(decoding),
            language_comprehension=float(comprehension),
            grade=grade,
            cutoff=float(cutoff) if cutoff not in (None, "") else None,
            diagnosed_skills=list(diagnosed_skills),
        )
        result["student_alias"] = clean_name
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/remediations")
@app.get("/tools/get_instructional_remediation")
async def list_remediations():
    return list_available_remediations()


@app.post("/api/decodability")
@app.post("/tools/verify_decodable_text")
async def check_decodability_route(data: dict):
    """Story 2: Check text decodability against the cumulative scope for grade/unit."""
    try:
        target = float(data.get("target_pct", 90))
    except (TypeError, ValueError):
        target = 90.0
    return check_decodability(
        data.get("text", ""),
        data.get("grade", "1"),
        unit=data.get("unit", 1),
        target_pct=target,
    )


@app.get("/api/scope_units")
async def scope_units(grade: str = "1"):
    """List unit titles in the active scope & sequence for a grade."""
    from src.engine.scope_sequence import load_sequence, normalize_grade

    g = normalize_grade(grade) or "1"
    units = load_sequence().get(g, [])
    return {"grade": g, "units": [{"unit": i + 1, "title": u.get("title", "")} for i, u in enumerate(units)]}


@app.post("/api/vocabulary")
async def classify(data: dict):
    """Classify vocabulary into Tier 1/2/3."""
    return classify_text(data.get("text", ""))


@app.get("/api/evidence")
async def evidence(topic: str = ""):
    """Search research evidence."""
    return search_evidence(topic)


@app.post("/api/standards")
async def standards(data: dict):
    """Story 4: Find standards matching a skill description with CASE deep links."""
    return align_standards(data.get("description", ""), data.get("state", "GA"))


@app.post("/api/sanitize_pii")
@app.post("/tools/sanitize_pii")
async def sanitize_pii_route(data: dict):
    """Story 5: Remove student identifiers before processing (data minimization)."""
    sanitized = sanitize_pii(data)
    return {"status": "ok", "sanitized_data": sanitized}


@app.get("/USER_GUIDE.md")
@app.get("/user_guide.md")
@app.get("/USER_GUIDE")
@app.get("/user_guide")
async def user_guide_redirect():
    return RedirectResponse(url="https://github.com/kosburn0408/sor-mcp-server/blob/main/USER_GUIDE.md", status_code=302)


@app.get("/README.md")
@app.get("/readme.md")
@app.get("/README")
@app.get("/readme")
async def readme_redirect():
    return RedirectResponse(url="https://github.com/kosburn0408/sor-mcp-server/blob/main/README.md", status_code=302)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sor-dashboard", "version": "4.0", "epic": "EPIC-SOR-01"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SoR Web Dashboard")
    parser.add_argument("--port", type=int, default=8093, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    args = parser.parse_args()

    print(f"📖 SoR Teacher-First Workspace → http://localhost:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
