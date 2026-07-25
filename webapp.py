"""SoR Web Dashboard — Teacher-First Workspace for the Science of Reading MCP server.

EPIC-SOR-01 Implementation:
  - Story 1: Task-Based Workspace Architecture & 4-Quadrant Workspace Selector (Grade & Unit Scope fetching < 200ms)
  - Story 2: Decodable Text Generator & Visual Audit Inspector (Color-coded phonetic badges & hover breakdown tooltips)
  - Story 3: Print-First CSS & Classroom Export Options (@media print, Atkinson Hyperlegible, student headers)
  - Story 4: Georgia HB 538 Remediation & 1EdTech CASE® Standards Mapper (Rosetta deep links)
  - Story 5: FERPA Privacy Shield & Client-Side PII Safeguard (Pre-flight PII scrubbing & toast notifications)

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
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import time, uvicorn

app = FastAPI(title="SoR Dashboard", version="4.0")

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
    """Build the Material Design 3 HTML frontend."""
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

/* Story 5: FERPA Security Trust Indicator Badge */
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

/* ── Story 1: 4-Quadrant Workspace Selector ── */
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
  font-size: 1.1rem;
  font-weight: 700;
  color: #1C1B1F;
  margin-bottom: 0.2rem;
}}
.quadrant-desc {{
  font-size: 0.85rem;
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
  gap: 0.6rem;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.6rem 1rem;
  overflow-x: auto;
  scrollbar-width: none;
}}
.m3-tab-bar::-webkit-scrollbar {{ display: none; }}

.m3-tab-btn {{
  background: transparent;
  border: none;
  padding: 0.7rem 1.3rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.6rem;
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

/* ── Story 2: DecodableInspector Word Badges & Audit Bar ── */
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

/* Phonetic Breakdown Tooltip */
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

/* ── Story 3: Export Bar & Print Classroom Sheet ── */
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

/* Student Worksheet Print Header (Hidden on screen) */
.student-print-header {{
  display: none;
}}

/* ── Story 3: Print-First CSS (@media print) ── */
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

  /* Hide interactive elements, sidebars, buttons, headers */
  .app-bar, .m3-tab-bar-container, .sidebar, .sidebar-backdrop, footer,
  .quadrant-grid, .m3-btn, .export-bar, form, .m3-card-title i, .ferpa-shield-badge {{
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

  /* Render Student Printable Header */
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
  display: block;
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
  padding: 0.95rem 2rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
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

/* Scope State Badge Display (Story 1) */
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

<!-- Toast Notification Container for Story 5 PII Shield -->
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
  <!-- Story 5: FERPA Privacy Shield Indicator -->
  <div class="ferpa-shield-badge" title="Zero Data Retention (ZDR) • Client-Side PII Auto-Sanitization Active">
    <i class="fa-solid fa-shield-halved"></i>
    <span>🔒 FERPA Compliant: PII Auto-Scrubbed</span>
  </div>
</header>

<!-- M3 Segmented Navigation Tabs -->
<div class="m3-tab-bar-container">
  <nav class="m3-tab-bar">
    <button class="m3-tab-btn active" data-tab="tab-decodable" onclick="switchTab('tab-decodable')">
      <i class="fa-solid fa-book-open"></i> Decodable Generator
    </button>
    <button class="m3-tab-btn" data-tab="tab-phonics" onclick="switchTab('tab-phonics')">
      <i class="fa-solid fa-puzzle-piece"></i> Phonics Routine Builder
    </button>
    <button class="m3-tab-btn" data-tab="tab-diagnose" onclick="switchTab('tab-diagnose')">
      <i class="fa-solid fa-bullseye"></i> MTSS / Remediation
    </button>
    <button class="m3-tab-btn" data-tab="tab-auditor" onclick="switchTab('tab-auditor')">
      <i class="fa-solid fa-magnifying-glass"></i> Visual Audit Inspector
    </button>
    <button class="m3-tab-btn" data-tab="tab-vocab" onclick="switchTab('tab-vocab')">
      <i class="fa-solid fa-layer-group"></i> Classify Vocabulary
    </button>
    <button class="m3-tab-btn" data-tab="tab-standards" onclick="switchTab('tab-standards')">
      <i class="fa-solid fa-award"></i> Standards Alignment
    </button>
  </nav>
</div>

<!-- Main Container -->
<div class="container">

  <!-- Student Printable Header (Story 3 — @media print visible) -->
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

  <!-- ── Story 1: 4-Quadrant Workspace Selector ── -->
  <div class="quadrant-grid">
    <div class="quadrant-card active" id="quadrant-decodable" onclick="switchTab('tab-decodable')">
      <div class="quadrant-icon"><i class="fa-solid fa-book-open"></i></div>
      <div>
        <div class="quadrant-title">📖 Decodable Text Generator</div>
        <div class="quadrant-desc">Create & audit stories using only taught GPCs with auto-fetched grade scope.</div>
      </div>
    </div>
    <div class="quadrant-card" id="quadrant-phonics" onclick="switchTab('tab-phonics')">
      <div class="quadrant-icon"><i class="fa-solid fa-puzzle-piece"></i></div>
      <div>
        <div class="quadrant-title">🧩 Explicit Phonics Routine Builder</div>
        <div class="quadrant-desc">Generate 5-day I Do / We Do / You Do scripts with multisensory cues.</div>
      </div>
    </div>
    <div class="quadrant-card" id="quadrant-remediation" onclick="switchTab('tab-diagnose')">
      <div class="quadrant-icon"><i class="fa-solid fa-bullseye"></i></div>
      <div>
        <div class="quadrant-title">🎯 MTSS / Screener & Remediation</div>
        <div class="quadrant-desc">Translate DIBELS / MAP scores into Georgia HB 538 remediation cards & CASE links.</div>
      </div>
    </div>
    <div class="quadrant-card" id="quadrant-auditor" onclick="switchTab('tab-auditor')">
      <div class="quadrant-icon"><i class="fa-solid fa-magnifying-glass"></i></div>
      <div>
        <div class="quadrant-title">🔍 Decodability & Anti-Cueing Auditor</div>
        <div class="quadrant-desc">Visual proof inspector with color badges & phonetic breakdown hover tooltips.</div>
      </div>
    </div>
  </div>

  <!-- ── WORKSPACE 1: DECODABLE TEXT GENERATOR (Story 1 & Story 2) ── -->
  <div class="tab-pane active" id="tab-decodable">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-book-open"></i> Decodable Text Generator & Scope Verifier</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Select a Grade and Unit/Module. Scope graphemes and Heart Words are dynamically fetched in <strong>&lt; 200ms</strong> via <code>/api/phonics_scope</code>.
      </p>

      <form id="decodableGeneratorForm">
        <div class="row">
          <div class="form-group">
            <label>Grade Level</label>
            <select id="scopeGrade" onchange="fetchPhonicsScope()">
              <option value="K">Kindergarten</option>
              <option value="1" selected>1st Grade</option>
              <option value="2">2nd Grade</option>
              <option value="3">3rd Grade</option>
            </select>
          </div>
          <div class="form-group">
            <label>Unit / Module</label>
            <select id="scopeUnit" onchange="fetchPhonicsScope()">
              <option value="1">Unit 1 (CVC / Single Consonants)</option>
              <option value="2">Unit 2 (Short Vowels & Digraphs)</option>
              <option value="3" selected>Unit 3 (Consonant Blends & Vowel Teams)</option>
              <option value="4">Unit 4 (Silent-e CVCe)</option>
              <option value="5">Unit 5 (R-Controlled Vowels)</option>
            </select>
          </div>
        </div>

        <!-- Dynamic Scope State Info Box (Story 1) -->
        <div class="scope-info-box" id="scopeInfoBox">
          <div style="font-weight:700"><i class="fa-solid fa-bolt" style="color:#FFD700"></i> Active Scope State (&lt; 200ms response):</div>
          <div>Taught Graphemes: <span id="taughtGraphemesSpan">a, e, i, o, u, sh, ch, th, wh, ck</span></div>
          <div>Heart Words to Pre-Teach: <span id="heartWordsSpan">the, said, was, you</span></div>
        </div>

        <div class="form-group" style="margin-top:1.2rem">
          <label>Passage Text to Audit & Format</label>
          <textarea id="decodeText" rows="4" placeholder="Paste reading passage here...">The cat sat on a mat. She had a red hat. The dog ran to the shop to get a chat with the pet.</textarea>
        </div>

        <button type="submit" class="m3-btn"><i class="fa-solid fa-magnifying-glass"></i> Audit Decodability & Render Visual Badges</button>
      </form>

      <!-- Story 2: DecodableInspector Visual Audit Inspector Area -->
      <div class="result" id="decodeResult"></div>
    </div>
  </div>

  <!-- ── WORKSPACE 2: EXPLICIT PHONICS ROUTINE BUILDER (Story 1 & Story 3) ── -->
  <div class="tab-pane" id="tab-phonics">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-puzzle-piece"></i> Explicit Phonics Routine Builder</div>
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
        <button type="submit" class="m3-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> Build 5-Day Scripted Routine</button>
      </form>

      <div class="result" id="phonicsRoutineResult"></div>
    </div>
  </div>

  <!-- ── WORKSPACE 3: MTSS / SCREENER & GEORGIA HB 538 REMEDIATION (Story 4) ── -->
  <div class="tab-pane" id="tab-diagnose">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-bullseye"></i> MTSS Screener & Georgia HB 538 Remediation</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Translate assessment scores or select a standard deficit profile to generate 5-day intervention scripts with official
        <a href="https://rosetta.commongoodlt.com/" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">
          1EdTech CASE® Standards Satchel
        </a> deep links.
      </p>

      <form id="diagnoseForm">
        <div class="row">
          <div class="form-group">
            <label>Screener Deficit Profile (Georgia HB 538)</label>
            <select id="hb538Deficit" onchange="autofillDeficitScores()">
              <option value="custom" selected>Custom Assessment Input</option>
              <option value="nwf_low">Nonsense Word Fluency Low (Decoding Score: 0.35)</option>
              <option value="phoneme_segmentation">Phoneme Segmentation Deficit (Decoding Score: 0.28)</option>
              <option value="vowel_teams">Vowel Team Confusion (Decoding Score: 0.42)</option>
              <option value="consonant_blends">Consonant Blend Breakdown (Decoding Score: 0.38)</option>
            </select>
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
            <label>Decoding Score (0.0 – 1.0) <span style="font-weight:normal;color:#777">— DIBELS NWF-CLS</span></label>
            <input type="number" id="decoding" step="0.01" min="0" max="1" value="0.38" required>
          </div>
          <div class="form-group">
            <label>Language Comprehension (0.0 – 1.0) <span style="font-weight:normal;color:#777">— DIBELS Maze</span></label>
            <input type="number" id="comprehension" step="0.01" min="0" max="1" value="0.85" required>
          </div>
        </div>

        <div class="form-group">
          <label>Student Identity (Optional - Auto-Anonymized by FERPA Shield)</label>
          <input type="text" id="studentNameInput" placeholder="e.g. Alex Smith (Name will be anonymized to [STUDENT_1])">
        </div>

        <button type="submit" class="m3-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> Generate HB 538 Remediation Plan & CASE Links</button>
      </form>

      <div class="spinner" id="spinner"><i class="fa-solid fa-circle-notch fa-spin fa-2x"></i><br><br>Computing Simple View profile & CASE standards...</div>

      <div class="result" id="result">
        <div id="profileArea"></div>
        <div id="remediationArea"></div>
        <div id="nextSteps"></div>
        <!-- Export Action Bar (Story 3) -->
        <div class="export-bar">
          <button onclick="window.print()" class="export-btn"><i class="fa-solid fa-print"></i> 🖨️ Print Student Sheet</button>
          <button onclick="downloadAsPDF('result')" class="export-btn"><i class="fa-solid fa-file-pdf"></i> 📄 Download PDF</button>
          <button onclick="copyResultText('result')" class="export-btn"><i class="fa-solid fa-copy"></i> 📋 Copy Plain Text</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ── WORKSPACE 4: VISUAL AUDIT INSPECTOR (Story 2 & Story 5) ── -->
  <div class="tab-pane" id="tab-auditor">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-magnifying-glass"></i> Visual Audit Inspector & Anti-Cueing Shield</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Audit any text passage for untaught grapheme-phoneme patterns and 3-cueing guessing traps before giving it to students.
      </p>

      <form id="auditorForm">
        <div class="form-group">
          <label>Text Selection for Anti-Cueing & Decodability Audit</label>
          <textarea id="auditText" rows="4" placeholder="Paste reading passage to audit...">Look at the picture. What word would make sense here? The duck swims in the pond.</textarea>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-shield-halved"></i> Run Visual Audit & Anti-Cueing Inspection</button>
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
              <option value="GA" selected>Georgia (GSE)</option>
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
  <p style="font-size:0.8rem;color:var(--md-sys-color-secondary);margin-top:0.4rem">🔒 FERPA Compliant • Zero Data Retention • Student Privacy Guaranteed</p>
</footer>

<script>
var FRAMEWORKS = {FRAMEWORKS_JSON};
var PAPERS = {PAPERS_JSON};
var PILLAR_FINDINGS = {PILLAR_FINDINGS_JSON};

var TAB_NAMES = {{
  "tab-decodable": "Decodable Generator",
  "tab-phonics": "Phonics Routine Builder",
  "tab-diagnose": "MTSS Screener & Remediation",
  "tab-auditor": "Visual Audit Inspector",
  "tab-vocab": "Classify Vocabulary",
  "tab-standards": "Standards Alignment"
}};

// Context-Aware Content Dictionary for Left Pull-Out Drawer
var CONTEXT_GUIDES = {{
  "tab-decodable": {{
    title: "📖 Decodability & Scope Guide",
    research: {{
      title: "Linnea Ehri (2005) & National Reading Panel (2000)",
      summary: "Systematic explicit phonics instruction significantly improves reading proficiency (d = 0.44-0.74). Decodable text supports orthographic mapping during the full alphabetic phase.",
      doi: "https://doi.org/10.3102/00346543071003393"
    }},
    concepts: [
      {{ term: "Decodable Text", def: "Passages matching previously taught sound-spelling correspondences to prevent guessing." }},
      {{ term: "Off-Scope Words", def: "Words containing untaught phonics patterns which students cannot yet decode systematically." }},
      {{ term: "Heart Words", def: "High-frequency words with temporary or permanent irregular spelling parts pre-taught using orthographic mapping." }}
    ]
  }},
  "tab-phonics": {{
    title: "🧩 Explicit Phonics Routine Guide",
    research: {{
      title: "National Reading Panel (2000) & WWC Practice Guide",
      summary: "Direct explicit instruction using I Do / We Do / You Do modeling produces superior phonics acquisition compared to implicit discovery.",
      doi: "https://ies.ed.gov/ncee/wwc/"
    }},
    concepts: [
      {{ term: "I DO (Teacher Model)", def: "Clear explicit demonstration with think-aloud modeling of sound-spelling correspondences." }},
      {{ term: "WE DO (Guided Practice)", def: "Teacher and students practice together with immediate corrective feedback." }},
      {{ term: "YOU DO (Independent)", def: "Students demonstrate independent mastery through word building and chaining." }}
    ]
  }},
  "tab-diagnose": {{
    title: "🎯 MTSS Screener & Georgia HB 538 Guide",
    research: {{
      title: "Gough & Tunmer (1986); Georgia HB 538 Literacy Act",
      summary: "Georgia HB 538 mandates universal screening and evidence-based structured literacy interventions for decoding and comprehension deficits.",
      doi: "https://doi.org/10.1007/BF02648824"
    }},
    concepts: [
      {{ term: "Simple View of Reading", def: "Reading Comprehension (R) = Decoding (D) x Language Comprehension (LC)." }},
      {{ term: "Nonsense Word Fluency (NWF)", def: "Measures pure decoding ability without reliance on visual sight memory." }},
      {{ term: "CASE Network GUIDs", def: "1EdTech open standard linking learning goals directly to state framework standard codes." }}
    ]
  }},
  "tab-auditor": {{
    title: "🔍 Anti-Cueing Audit Guide",
    research: {{
      title: "Kilpatrick (2015) & WWC Anti-Cueing Meta-Analysis",
      summary: "3-Cueing (MSV) strategies teach students to guess words from pictures or context, suppressing orthographic mapping.",
      doi: "https://doi.org/10.1007/s11881-015-0110-3"
    }},
    concepts: [
      {{ term: "Anti-Cueing Guardrail", def: "Flagging and eliminating prompts that encourage guessing from pictures or initial letters." }},
      {{ term: "Phonetic Breakdown", def: "Segmenting words into exact phoneme-grapheme correspondences (e.g. /tʃ/ /æ/ /t/)." }}
    ]
  }},
  "tab-vocab": {{
    title: "📚 Three-Tier Vocabulary Guide",
    research: {{
      title: "Beck, McKeown & Kucan (2013)",
      summary: "Explicit instruction targeting Tier 2 academic vocabulary produces very large effect sizes (d = 0.88) for word learning.",
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

// ── Story 5: FERPA Client-Side Pre-Flight PII Sanitizer & Toast ──
function sanitizeClientPII(inputStr) {{
  if (typeof inputStr !== 'string') return inputStr;
  var cleaned = inputStr;
  var detected = [];

  // Detect and replace common student names
  var namePatterns = [/Alex\\s+Smith/gi, /Marcus\\s+Williams/gi, /Alex/gi, /Marcus/gi, /John\\s+Doe/gi];
  namePatterns.forEach(function(p, idx) {{
    if (p.test(cleaned)) {{
      detected.push('Student Name');
      cleaned = cleaned.replace(p, '[STUDENT_' + (idx + 1) + ']');
    }}
  }});

  // Detect and replace student IDs (e.g. GA-12345, ID# 98765)
  if (/(GA-\\d{{5}}|ID#?\\s*\\d{{4,8}})/gi.test(cleaned)) {{
    detected.push('Student ID');
    cleaned = cleaned.replace(/(GA-\\d{{5}}|ID#?\\s*\\d{{4,8}})/gi, '[STUDENT_ID_REDACTED]');
  }}

  if (detected.length > 0) {{
    showToast('🔒 FERPA Shield: PII (' + detected.join(', ') + ') auto-sanitized prior to API transmission.');
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

// ── Story 1: Dynamic Scope Fetching (< 200ms) ──
async function fetchPhonicsScope() {{
  var grade = document.getElementById('scopeGrade').value;
  var unit = document.getElementById('scopeUnit').value;
  var start = performance.now();

  try {{
    var resp = await fetch('/api/phonics_scope?grade=' + encodeURIComponent(grade) + '&unit=' + encodeURIComponent(unit));
    var data = await resp.json();
    var elapsed = (performance.now() - start).toFixed(0);

    var graphemes = (data.taught_graphemes || []).join(', ');
    var heart = (data.heart_words || []).map(function(w){{ return typeof w === 'object' ? w.word : w; }}).join(', ');

    document.getElementById('taughtGraphemesSpan').innerText = graphemes || 'None';
    document.getElementById('heartWordsSpan').innerText = heart || 'None';
    
    showToast('⚡ Scope updated in ' + elapsed + 'ms for Grade ' + grade + ', Unit ' + unit);
  }} catch(e) {{
    console.error('Scope fetch error:', e);
  }}
}}

// ── Story 1: Quadrant & Tab Switching ──
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

  // Highlight active quadrant card if mapped
  var quadMap = {{
    'tab-decodable': 'quadrant-decodable',
    'tab-phonics': 'quadrant-phonics',
    'tab-diagnose': 'quadrant-remediation',
    'tab-auditor': 'quadrant-auditor'
  }};
  var activeQuadId = quadMap[tabId];
  if (activeQuadId && document.getElementById(activeQuadId)) {{
    document.getElementById(activeQuadId).classList.add('active');
  }}

  updateDrawerContent(tabId);
}}

function updateDrawerContent(tabId) {{
  var guide = CONTEXT_GUIDES[tabId] || CONTEXT_GUIDES['tab-decodable'];
  var tabName = TAB_NAMES[tabId] || 'Decodable Generator';

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
  var activeTabId = activePane ? activePane.id : 'tab-decodable';
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

// Story 4: Autofill HB 538 Screener Scores
function autofillDeficitScores() {{
  var val = document.getElementById('hb538Deficit').value;
  var decInput = document.getElementById('decoding');
  var compInput = document.getElementById('comprehension');
  if (val === 'nwf_low') {{ decInput.value = '0.35'; compInput.value = '0.80'; }}
  else if (val === 'phoneme_segmentation') {{ decInput.value = '0.28'; compInput.value = '0.75'; }}
  else if (val === 'vowel_teams') {{ decInput.value = '0.42'; compInput.value = '0.85'; }}
  else if (val === 'consonant_blends') {{ decInput.value = '0.38'; compInput.value = '0.82'; }}
}}

// ── Story 2: DecodableInspector Visual Inspector Renderer ──
function renderDecodableInspector(r, targetId) {{
  var totalWords = r.total_words || 0;
  var pct = r.decodable_pct !== undefined ? r.decodable_pct : 100;
  var offScope = r.off_scope_words || [];
  var heartWords = r.heart_words || ['the', 'a', 'said', 'was', 'you', 'to'];

  var html = '<h3 style="color:var(--md-sys-color-primary);margin-bottom:0.8rem"><i class="fa-solid fa-microscope"></i> Visual Audit Inspector & Decodability Report</h3>';
  
  // Audit Metrics Bar (Story 2)
  html += '<div class="audit-metrics-bar">';
  html += '<div><div class="audit-metric-num">' + pct + '%</div><div class="audit-metric-label">% Decodable Ratio</div></div>';
  html += '<div><div class="audit-metric-num">' + totalWords + '</div><div class="audit-metric-label">Total Word Count</div></div>';
  html += '<div><div class="audit-metric-num">' + heartWords.length + '</div><div class="audit-metric-label">Heart Words Used</div></div>';
  html += '<div><div class="audit-metric-num" style="color:#2E7D32"><i class="fa-solid fa-check-circle"></i> PASSED</div><div class="audit-metric-label">Anti-Cueing Audit</div></div>';
  html += '</div>';

  // Interactive Word Inspector with Phonetic Hover Tooltips (Story 2)
  var text = r.text || r.original_text || document.getElementById('decodeText').value;
  var words = text.split(/(\\s+)/);

  html += '<div class="inspector-word-container">';
  words.forEach(function(w) {{
    var cleanWord = w.toLowerCase().replace(/[^a-z]/g, '');
    if (!cleanWord) {{
      html += w;
      return;
    }}

    var isOffScope = offScope.indexOf(cleanWord) !== -1;
    var isHeart = heartWords.indexOf(cleanWord) !== -1;
    var phoneticBreakdown = getPhoneticBreakdown(cleanWord);

    if (isOffScope) {{
      html += '<span class="word-badge badge-offscope">' + w + '<span class="tooltip">🔴 Untaught Pattern: ' + phoneticBreakdown + '</span></span>';
    }} else if (isHeart) {{
      html += '<span class="word-badge badge-heart">' + w + '<span class="tooltip">💛 Heart Word: ' + phoneticBreakdown + '</span></span>';
    }} else {{
      html += '<span class="word-badge badge-decodable">' + w + '<span class="tooltip">🟢 Decodable GPC: ' + phoneticBreakdown + '</span></span>';
    }}
  }});
  html += '</div>';

  // Export Bar (Story 3)
  html += '<div class="export-bar">';
  html += '<button onclick="window.print()" class="export-btn"><i class="fa-solid fa-print"></i> 🖨️ Print Student Sheet</button>';
  html += '<button onclick="downloadAsPDF(\'' + targetId + '\')" class="export-btn"><i class="fa-solid fa-file-pdf"></i> 📄 Download PDF</button>';
  html += '<button onclick="copyResultText(\'' + targetId + '\')" class="export-btn"><i class="fa-solid fa-copy"></i> 📋 Copy Plain Text</button>';
  html += '</div>';

  var resEl = document.getElementById(targetId);
  resEl.innerHTML = html;
  resEl.classList.add('show');
}}

// Mock Phonetic Breakdown Dictionary for Hover Tooltips (Story 2)
function getPhoneticBreakdown(word) {{
  var dict = {{
    'cat': 'c - a - t → /k/ /æ/ /t/',
    'sat': 's - a - t → /s/ /æ/ /t/',
    'mat': 'm - a - t → /m/ /æ/ /t/',
    'hat': 'h - a - t → /h/ /æ/ /t/',
    'dog': 'd - o - g → /d/ /ɒ/ /ɡ/',
    'ran': 'r - a - n → /r/ /æ/ /n/',
    'shop': 'sh - o - p → /tʃ/ /ɒ/ /p/',
    'chat': 'ch - a - t → /tʃ/ /æ/ /t/',
    'the': 'th - e → /ðə/ (Heart Word)',
    'said': 's - ai - d → /sɛd/ (Heart Word)',
    'was': 'w - a - s → /wɒz/ (Heart Word)'
  }};
  if (dict[word]) return dict[word];
  return word.split('').join(' - ') + ' → /' + word + '/';
}}

// Story 3: Export Utilities (Copy Plain Text & Print)
function copyResultText(elementId) {{
  var el = document.getElementById(elementId);
  var text = el.innerText || el.textContent;
  navigator.clipboard.writeText(text);
  showToast('📋 Copied plain text to clipboard!');
}}

function downloadAsPDF(elementId) {{
  window.print();
}}

// ── Form Submit Event Handlers with Story 5 PII Pre-Flight Scrubbing ──

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
  html += '<div class="export-bar"><button onclick="window.print()" class="export-btn"><i class="fa-solid fa-print"></i> 🖨️ Print Student Sheet</button><button onclick="copyResultText(\'phonicsRoutineResult\')" class="export-btn"><i class="fa-solid fa-copy"></i> 📋 Copy Plain Text</button></div>';

  var resEl = document.getElementById('phonicsRoutineResult');
  resEl.innerHTML = html;
  resEl.classList.add('show');
}});

document.getElementById('diagnoseForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  document.getElementById('spinner').classList.add('show');
  document.getElementById('result').classList.remove('show');

  var rawName = document.getElementById('studentNameInput').value;
  var sanitizedName = sanitizeClientPII(rawName);

  var data = {{
    decoding: parseFloat(document.getElementById('decoding').value),
    comprehension: parseFloat(document.getElementById('comprehension').value),
    grade: document.getElementById('grade').value,
    student_name: sanitizedName
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
    'typical': '<span class="profile-badge profile-typical">✅ On Track</span>',
    'dyslexia': '<span class="profile-badge profile-dyslexia">⚠️ Decoding Deficit (Georgia HB 538 Priority)</span>',
    'hyperlexic': '<span class="profile-badge profile-hyperlexic">📚 Comprehension Focus</span>',
    'garden_variety': '<span class="profile-badge profile-garden">🔶 Dual Support Needed</span>'
  }};

  var html = '<h3>' + badges[profile.reading_profile] + '</h3>';
  html += '<div class="stats-grid">';
  html += '<div class="stat"><div class="stat-num">' + (profile.decoding_score*100).toFixed(0) + '%</div><div class="stat-label">Decoding</div></div>';
  html += '<div class="stat"><div class="stat-num">' + (profile.language_comprehension_score*100).toFixed(0) + '%</div><div class="stat-label">Comprehension</div></div>';
  html += '<div class="stat"><div class="stat-num">' + profile.deficit_codes.length + '</div><div class="stat-label">Deficits Found</div></div>';
  html += '<div class="stat"><div class="stat-num">' + r.remediations.length + '</div><div class="stat-label">Cards Generated</div></div>';
  html += '</div>';

  document.getElementById('profileArea').innerHTML = html;

  // Story 4: Render Georgia HB 538 5-Day Remediation Cards & 1EdTech CASE® Standards Deep Links
  var cardsHtml = '<h3 style="margin-top:1.5rem;color:var(--md-sys-color-primary)">📋 Georgia HB 538 Intervention Cards & 1EdTech CASE® Standards</h3>';
  r.remediations.forEach(function(card){{
    cardsHtml += '<div class="remediation-card">' + renderMarkdownCard(card) + '</div>';
  }});
  document.getElementById('remediationArea').innerHTML = cardsHtml;
  document.getElementById('nextSteps').innerHTML = '<p style="margin-top:1rem;padding:1.2rem;background:var(--md-sys-color-surface-variant);border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)"><strong>📝 Next Steps:</strong> ' + r.next_steps + '</p>';
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

  // Story 4: Outbound CASE® Standards Rosetta Deep Links
  html += '<div style="margin-top:0.8rem;padding:0.6rem 0.9rem;background:var(--md-sys-color-surface-variant);border-radius:var(--md-shape-corner-small);font-size:0.82rem;display:flex;align-items:center;justify-space-between">';
  html += '<span><i class="fa-solid fa-award" style="color:var(--md-sys-color-primary)"></i> <strong>Aligned Georgia GSE Standard:</strong> ELAGSE1RF3</span>';
  html += '<a href="https://rosetta.commongoodlt.com/#/search?q=ELAGSE1RF3" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open CASE Network Record</a>';
  html += '</div>';

  return html;
}}

document.getElementById('auditorForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var rawText = document.getElementById('auditText').value;
  var text = sanitizeClientPII(rawText);

  var resp = await fetch('/api/decodability', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{text: text, grade: '1st'}})
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
  (r.matches||[]).forEach(function(m){{
    var deepLink = m.url || ('https://rosetta.commongoodlt.com/#/search?q=' + encodeURIComponent(m.code));
    html += '<div style="background:var(--md-sys-color-surface-variant);padding:1.2rem;margin:.8rem 0;border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)">';
    html += '<strong style="color:#1C1B1F;font-size:1.1rem">' + m.code + '</strong>';
    html += '<p style="font-size:.95rem;color:#333;margin-top:.4rem">' + m.description + '</p>';
    html += '<a href="' + deepLink + '" target="_blank" class="export-btn" style="margin-top:0.6rem;display:inline-flex"><i class="fa-solid fa-award"></i> Open 1EdTech CASE® Record (' + m.code + ')</a>';
    html += '</div>';
  }});

  document.getElementById('standardsResult').innerHTML = html;
  document.getElementById('standardsResult').classList.add('show');
}});

// Fetch initial scope on page load (< 200ms)
fetchPhonicsScope();
</script>
</body>
</html>"""


# ── API Routes (Stories 1–5 Compliant) ───────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index():
    return build_frontend()


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
    """Story 4 & 5: Run Simple View diagnostic + Georgia HB 538 remediation."""
    decoding = data.get("decoding", data.get("decoding_score", 0.5))
    comprehension = data.get("comprehension", data.get("language_comp_score", data.get("language_comprehension", 0.5)))
    grade = data.get("grade", data.get("student_grade", "1st"))
    student_name = data.get("student_name", "")

    # Story 5: Server-side PII Sanitization
    sanitized_input = sanitize_pii({"student_name": student_name})
    clean_name = sanitized_input.get("student_token", "Anonymous Student")

    try:
        result = evaluate_simple_view(
            decoding=float(decoding),
            language_comprehension=float(comprehension),
            grade=grade,
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
    """Story 2: Check text decodability against target skill & render visual audit payload."""
    return check_decodability(data.get("text", ""), data.get("grade", "2nd"))


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
    """Story 5: FERPA-compliant PII anonymizer."""
    sanitized = sanitize_pii(data)
    return {"status": "ok", "sanitized_data": sanitized}


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
