"""SoR Web Dashboard — Teacher-friendly interface for the Science of Reading MCP server.

Single-file FastAPI app with embedded frontend. No command line needed.
Usage: python3 webapp.py  (runs on localhost:8093 by default)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import time, uvicorn

app = FastAPI(title="SoR Dashboard", version="3.7")

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
<title>Science of Reading — Teacher Workspace</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
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

/* ── Top App Bar ── */
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

.hub-btn {{
  background: var(--md-sys-color-secondary-container);
  color: #1D192B;
  border: none;
  padding: 0.5rem 1.1rem;
  border-radius: var(--md-shape-corner-full);
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
  text-decoration: none;
}}
.hub-btn:hover {{
  background: #D8CEE8;
  transform: translateY(-1px);
}}

/* ── M3 Segmented Navigation Bar ── */
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
  max-width: 1050px;
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
.m3-tab-btn i {{
  font-size: 1.05rem;
}}

/* ── Container & Layout ── */
.container {{
  max-width: 1050px;
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
  transition: box-shadow 0.25s ease;
}}
.m3-card:hover {{
  box-shadow: var(--md-elevation-3);
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
.m3-card-title i {{
  color: var(--md-sys-color-tertiary);
}}

/* ── Hero Banners ── */
.hero-card {{
  background: linear-gradient(135deg, #4A3E7D 0%, #6750A4 100%);
  color: #fff;
  border-radius: var(--md-shape-corner-large);
  padding: 0;
  overflow: hidden;
  margin-bottom: 1.8rem;
  box-shadow: var(--md-elevation-3);
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  align-items: center;
}}
@media(max-width: 768px) {{
  .hero-card {{ grid-template-columns: 1fr; }}
  .hero-img-col {{ height: 220px; }}
}}
.hero-text-col {{
  padding: 2.2rem;
}}
.hero-tag {{
  display: inline-block;
  background: var(--md-sys-color-tertiary-container);
  color: #7A2813;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.8rem;
  border-radius: var(--md-shape-corner-full);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.8rem;
}}
.hero-title {{
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.25;
  margin-bottom: 0.8rem;
}}
.hero-desc {{
  color: #E8DEF8;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 1.2rem;
}}
.hero-img-col img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}}

/* ── Form Controls ── */
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

/* M3 Filled Button */
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
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}}
.m3-btn:hover {{
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(103, 80, 164, 0.4);
}}
.m3-btn:active {{
  transform: translateY(0);
}}

/* ── Collapsible Accordion (M3 Style) ── */
.m3-accordion {{
  background: var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-medium);
  margin-bottom: 0.8rem;
  overflow: hidden;
  border: 1px solid rgba(121, 116, 126, 0.12);
  transition: background 0.2s ease;
}}
.m3-accordion-header {{
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1.1rem 1.4rem;
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 1rem;
  color: var(--md-sys-color-primary);
  user-select: none;
}}
.m3-accordion-header i.step-icon {{
  width: 32px;
  height: 32px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
}}
.m3-accordion-header .chevron {{
  margin-left: auto;
  transition: transform 0.3s ease;
  color: var(--md-sys-color-outline);
}}
.m3-accordion.open .m3-accordion-header .chevron {{
  transform: rotate(180deg);
  color: var(--md-sys-color-primary);
}}
.m3-accordion-body {{
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--md-sys-color-surface);
}}
.m3-accordion.open .m3-accordion-body {{
  max-height: 1200px;
  padding: 1.4rem;
  border-top: 1px solid var(--md-sys-color-surface-variant);
}}

/* ── Results Area & Remediation Cards ── */
.result {{ display: none; margin-top: 1.8rem; padding-top: 1.8rem; border-top: 2px dashed var(--md-sys-color-outline-variant); }}
.result.show {{ display: block; }}

.profile-badge {{
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 1.1rem;
  border-radius: var(--md-shape-corner-full);
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 0.9rem;
}}
.profile-dyslexia {{ background: #FFDBCF; color: #7A2813; }}
.profile-typical {{ background: #C8E6C9; color: #1B5E20; }}
.profile-hyperlexic {{ background: #EADDFF; color: #21005D; }}
.profile-garden {{ background: #FFE0B2; color: #E65100; }}

.remediation-card {{
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-medium);
  padding: 1.6rem;
  margin: 1.4rem 0;
  box-shadow: var(--md-elevation-1);
}}
.remediation-card h3 {{
  color: var(--md-sys-color-primary);
  font-size: 1.25rem;
  margin-bottom: 0.8rem;
}}

.script-line {{
  margin: 0.5rem 0;
  padding: 0.6rem 1rem;
  border-radius: var(--md-shape-corner-small);
  font-size: 0.95rem;
}}
.script-i {{ background: #F3EDF7; color: #21005D; border-left: 4px solid var(--md-sys-color-primary); }}
.script-we {{ background: #FFF3E0; color: #E65100; border-left: 4px solid #F57C00; }}
.script-you {{ background: #E8F5E9; color: #1B5E20; border-left: 4px solid #388E3C; }}

.word-chain {{
  font-family: monospace;
  background: #F4EFF4;
  padding: 0.6rem 1.2rem;
  border-radius: var(--md-shape-corner-small);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--md-sys-color-primary);
  display: inline-block;
}}
.feedback {{
  padding: 0.7rem 1.1rem;
  border-radius: var(--md-shape-corner-small);
  margin: 0.6rem 0;
  font-size: 0.92rem;
}}
.feedback-error {{ background: #FFEDEA; border-left: 4px solid #D32F2F; color: #B71C1C; }}
.feedback-praise {{ background: #E8F5E9; border-left: 4px solid #388E3C; color: #1B5E20; }}

.stats-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 1rem;
  margin: 1.2rem 0;
}}
.stat {{
  text-align: center;
  padding: 1.2rem 0.8rem;
  background: var(--md-sys-color-surface-variant);
  border-radius: var(--md-shape-corner-medium);
}}
.stat-num {{
  font-family: 'Outfit', sans-serif;
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--md-sys-color-primary);
  line-height: 1.1;
}}
.stat-label {{
  font-size: 0.72rem;
  color: var(--md-sys-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: 0.3rem;
  font-weight: 700;
}}
.spinner {{ display: none; text-align: center; padding: 2rem; color: var(--md-sys-color-primary); font-weight: 600; }}
.spinner.show {{ display: block; }}

/* ── Context-Aware Pull-Out Left Drawer ── */
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

footer {{
  text-align: center;
  padding: 3rem 1rem;
  color: var(--md-sys-color-secondary);
  font-size: 0.88rem;
  border-top: 1px solid var(--md-sys-color-surface-variant);
  margin-top: 3rem;
}}

@media print {{
  .sidebar, .sidebar-backdrop, .app-bar, .m3-tab-bar-container, footer, .m3-card:not(.result-card), .m3-btn {{ display: none !important; }}
  .tab-pane {{ display: block !important; }}
  .result {{ display: block !important; }}
  .remediation-card {{ box-shadow: none; border: 1px solid #ccc; }}
}}
</style>
</head>
<body>

<!-- Sidebar Backdrop -->
<div class="sidebar-backdrop" id="sidebarBackdrop"></div>

<!-- Context-Aware Dynamic Pull-Out Left Drawer -->
<aside class="sidebar" id="sidebar">
  <div style="padding:1.4rem;border-bottom:1px solid var(--md-sys-color-surface-variant);background:var(--md-sys-color-primary-container);display:flex;align-items:center;justify-content:space-between">
    <div>
      <h2 style="color:var(--md-sys-color-on-primary-container);font-size:1.15rem;font-weight:700" id="drawerTitle">🔬 Topic & Research Guide</h2>
      <div style="font-size:0.75rem;color:var(--md-sys-color-secondary);margin-top:0.15rem">Contextual Science of Reading Research & Concepts</div>
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
      <div class="app-bar-subtitle">Science of Reading Teacher Workspace</div>
    </div>
  </div>
</header>

<!-- M3 Segmented Navigation Tabs -->
<div class="m3-tab-bar-container">
  <nav class="m3-tab-bar">
    <button class="m3-tab-btn active" data-tab="tab-diagnose" onclick="switchTab('tab-diagnose')">
      <i class="fa-solid fa-user-doctor"></i> Diagnose Student
    </button>
    <button class="m3-tab-btn" data-tab="tab-decodable" onclick="switchTab('tab-decodable')">
      <i class="fa-solid fa-book-open"></i> Check Decodability
    </button>
    <button class="m3-tab-btn" data-tab="tab-vocab" onclick="switchTab('tab-vocab')">
      <i class="fa-solid fa-layer-group"></i> Classify Vocabulary
    </button>
    <button class="m3-tab-btn" data-tab="tab-evidence" onclick="switchTab('tab-evidence')">
      <i class="fa-solid fa-microscope"></i> Evidence Search
    </button>
    <button class="m3-tab-btn" data-tab="tab-standards" onclick="switchTab('tab-standards')">
      <i class="fa-solid fa-award"></i> Standards Alignment
    </button>
    <button class="m3-tab-btn" data-tab="tab-guide" onclick="switchTab('tab-guide')">
      <i class="fa-solid fa-circle-question"></i> Teacher Guide
    </button>
  </nav>
</div>

<!-- Main Container -->
<div class="container">

  <!-- ── TAB 1: DIAGNOSE STUDENT ── -->
  <div class="tab-pane active" id="tab-diagnose">
    <div class="hero-card">
      <div class="hero-text-col">
        <span class="hero-tag">Simple View of Reading Diagnostic</span>
        <h1 class="hero-title">Turn Benchmark Scores into Lesson Plans</h1>
        <p class="hero-desc">Input DIBELS, Acadience, or MAP scores to generate printable remediation cards with explicit I Do / We Do / You Do small-group scripts.</p>
        <button onclick="tryExample()" style="background:rgba(255,255,255,0.2);color:#fff;border:1px solid rgba(255,255,255,0.4);padding:0.6rem 1.4rem;border-radius:28px;font-family:'Outfit',sans-serif;font-weight:700;font-size:0.9rem;cursor:pointer;display:inline-flex;align-items:center;gap:0.5rem">
          <i class="fa-solid fa-wand-magic-sparkles" style="color:#FFD700"></i> Try Demo Student (DIBELS 0.38)
        </button>
      </div>
      <div class="hero-img-col">
        <img src="/static/teacher_reading_hero.jpg" alt="Teacher Reading Small Group Instruction">
      </div>
    </div>

    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-stethoscope"></i> Assessment Score Diagnostic</div>
      <form id="diagnoseForm">
        <div class="row">
          <div class="form-group">
            <label>Decoding Score (0.0 – 1.0) <span style="font-weight:normal;color:#777">— DIBELS NWF-CLS or Acadience</span></label>
            <input type="number" id="decoding" step="0.01" min="0" max="1" placeholder="e.g. 0.38" required>
          </div>
          <div class="form-group">
            <label>Language Comprehension (0.0 – 1.0) <span style="font-weight:normal;color:#777">— DIBELS Maze or MAP</span></label>
            <input type="number" id="comprehension" step="0.01" min="0" max="1" placeholder="e.g. 0.85" required>
          </div>
        </div>
        <div class="form-group">
          <label>Grade Level</label>
          <select id="grade">
            <option value="K">Kindergarten</option>
            <option value="1st" selected>1st Grade</option>
            <option value="2nd">2nd Grade</option>
            <option value="3rd">3rd Grade</option>
            <option value="4th">4th Grade</option>
            <option value="5th">5th Grade</option>
          </select>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-wand-magic-sparkles"></i> Generate Remediation Plan</button>
      </form>

      <div class="spinner" id="spinner"><i class="fa-solid fa-circle-notch fa-spin fa-2x"></i><br><br>Computing Simple View profile...</div>

      <div class="result" id="result">
        <div id="profileArea"></div>
        <div id="remediationArea"></div>
        <div id="nextSteps"></div>
        <div style="text-align:center;margin-top:1.5rem">
          <button onclick="window.print()" class="m3-btn" style="width:auto;padding:0.7rem 1.8rem"><i class="fa-solid fa-print"></i> Print Remediation Cards</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ── TAB 2: CHECK DECODABILITY ── -->
  <div class="tab-pane" id="tab-decodable">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-book-open"></i> Decodability & Scope Verifier</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">Paste text from a book or passage to check which words use untaught phonics patterns and flag "Heart Words" to pre-teach.</p>
      <form id="decodabilityForm">
        <div class="form-group">
          <label>Passage Text</label>
          <textarea id="decodeText" rows="4" placeholder="Paste reading passage here..."></textarea>
        </div>
        <div class="row">
          <div class="form-group">
            <label>Grade Level</label>
            <select id="decodeGrade">
              <option value="K">Kindergarten</option>
              <option value="1st">1st Grade</option>
              <option value="2nd" selected>2nd Grade</option>
              <option value="3rd">3rd Grade</option>
            </select>
          </div>
          <div class="form-group">
            <label>Target Phonics Skill</label>
            <select id="decodeSkill">
              <option value="cvc_mixed">CVC Short Vowels</option>
              <option value="consonant_blends">Consonant Blends</option>
              <option value="cvce_silent_e">Silent-e (CVCe)</option>
              <option value="consonant_digraphs">Consonant Digraphs (sh, ch, th)</option>
              <option value="vowel_teams">Vowel Teams (ai, ee, oa)</option>
              <option value="r_controlled">R-Controlled (ar, or, er)</option>
            </select>
          </div>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-magnifying-glass"></i> Check Decodability</button>
      </form>
      <div class="result" id="decodeResult"></div>
    </div>
  </div>

  <!-- ── TAB 3: CLASSIFY VOCABULARY ── -->
  <div class="tab-pane" id="tab-vocab">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-layer-group"></i> Three-Tier Vocabulary Classifier</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">Analyze text passages using Beck's 3-Tier vocabulary framework to highlight high-utility Tier 2 academic words for explicit pre-teaching.</p>
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

  <!-- ── TAB 4: EVIDENCE SEARCH ── -->
  <div class="tab-pane" id="tab-evidence">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-microscope"></i> Evidence & Research Search</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">Query What Works Clearinghouse (WWC) and Best Evidence Encyclopedia (BEE) meta-analyses for literacy interventions and effect sizes with direct links to full research papers.</p>
      <form id="evidenceForm">
        <div class="form-group">
          <label>Topic or Skill Area</label>
          <input type="text" id="evidenceTopic" placeholder="e.g. phonics, fluency, vocabulary, comprehension, phonemic awareness..." required>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-magnifying-glass"></i> Search Research Evidence</button>
      </form>
      <div class="result" id="evidenceResult"></div>
    </div>
  </div>

  <!-- ── TAB 5: STANDARDS ALIGNMENT (STANDARDS SATCHEL / SATCHEL ROSETTA CASE®) ── -->
  <div class="tab-pane" id="tab-standards">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-award"></i> State Standards Alignment Lookup</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.2rem">
        Find academic standards across <strong>all 50 U.S. states</strong> powered by
        <a href="https://rosetta.commongoodlt.com/" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">
          <i class="fa-solid fa-arrow-up-right-from-square"></i> Common Good Learning Tools' Standards Satchel
        </a> (CASE® Exchange).
      </p>
      <form id="standardsForm">
        <div class="row">
          <div class="form-group">
            <label>Learning Goal / Skill</label>
            <input type="text" id="standardsSkill" placeholder="e.g. decode words with silent e..." required>
          </div>
          <div class="form-group">
            <label>State Framework (Standards Satchel CASE® Network)</label>
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
              <option value="IL">Illinois (CCSS-IL)</option>
              <option value="CCSS">Common Core (CCSS)</option>
              <option value="AL">Alabama (ALCOS)</option>
              <option value="AK">Alaska (AKSS)</option>
              <option value="AZ">Arizona (AZSS)</option>
              <option value="AR">Arkansas (AR-ELA)</option>
              <option value="CO">Colorado (CAS)</option>
              <option value="CT">Connecticut (CT-CCSS)</option>
              <option value="DE">Delaware (DE-CCSS)</option>
              <option value="HI">Hawaii (HCPS)</option>
              <option value="ID">Idaho (ISCS)</option>
              <option value="IN">Indiana (IAS)</option>
              <option value="IA">Iowa (Iowa Core)</option>
              <option value="KS">Kansas (KCAS)</option>
              <option value="KY">Kentucky (KAS)</option>
              <option value="LA">Louisiana (K-12 Student Standards)</option>
              <option value="ME">Maine (MLR)</option>
              <option value="MD">Maryland (MCCRS)</option>
              <option value="MA">Massachusetts (Curriculum Framework)</option>
              <option value="MI">Michigan (MITECS)</option>
              <option value="MN">Minnesota (MN Academic Standards)</option>
              <option value="MS">Mississippi (CCR-ELA)</option>
              <option value="MO">Missouri (MLS)</option>
              <option value="MT">Montana (MT Content Standards)</option>
              <option value="NE">Nebraska (NSCAS)</option>
              <option value="NV">Nevada (NVACS)</option>
              <option value="NH">New Hampshire (NH CCRS)</option>
              <option value="NJ">New Jersey (NJSLS)</option>
              <option value="NM">New Mexico (NM CCSS)</option>
              <option value="ND">North Dakota (ND Content Standards)</option>
              <option value="OK">Oklahoma (OAS)</option>
              <option value="OR">Oregon (OAR)</option>
              <option value="RI">Rhode Island (RI-CCSS)</option>
              <option value="SC">South Carolina (SCCCR)</option>
              <option value="SD">South Dakota (SD Content Standards)</option>
              <option value="TN">Tennessee (TN Academic Standards)</option>
              <option value="UT">Utah (Core Standards)</option>
              <option value="VT">Vermont (VT-CCSS)</option>
              <option value="WA">Washington (WMLS)</option>
              <option value="WV">West Virginia (WV College & Career Readiness)</option>
              <option value="WI">Wisconsin (Wisconsin Standards for ELA)</option>
              <option value="WY">Wyoming (WyCPS)</option>
            </select>
          </div>
        </div>
        <button type="submit" class="m3-btn"><i class="fa-solid fa-award"></i> Find Standards (Standards Satchel)</button>
      </form>
      <div class="result" id="standardsResult"></div>
    </div>
  </div>

  <!-- ── TAB 6: TEACHER GUIDE (ACCORDION & IMAGERY) ── -->
  <div class="tab-pane" id="tab-guide">
    <div class="m3-card">
      <div class="m3-card-title"><i class="fa-solid fa-graduation-cap"></i> Teacher Guide: Science of Reading Tools</div>
      <p style="color:var(--md-sys-color-secondary);margin-bottom:1.5rem">Step-by-step instructions on how to use each tool in your classroom reading routines.</p>

      <!-- Reading Rope Image Card -->
      <div style="margin-bottom:1.8rem;border-radius:var(--md-shape-corner-medium);overflow:hidden;box-shadow:var(--md-elevation-1)">
        <img src="/static/sor_reading_rope.jpg" alt="Scarborough's Reading Rope" style="width:100%;max-height:360px;object-fit:cover;display:block">
        <div style="padding:1rem;background:var(--md-sys-color-surface-variant);font-size:0.85rem;color:var(--md-sys-color-secondary)">
          <strong>The Theoretical Basis:</strong> Reading comprehension is the product of Word Recognition (decoding, phonological awareness, sight recognition) and Language Comprehension (vocabulary, background knowledge, verbal reasoning).
        </div>
      </div>

      <!-- Accordion Step 1 -->
      <div class="m3-accordion open" id="guide-step-1">
        <div class="m3-accordion-header" onclick="toggleGuide('guide-step-1')">
          <i class="fa-solid fa-user-doctor step-icon"></i>
          <span>1. How to Diagnose a Student & Print Remediation Cards</span>
          <i class="fa-solid fa-chevron-down chevron"></i>
        </div>
        <div class="m3-accordion-body">
          <p style="margin-bottom:0.8rem"><strong>Goal:</strong> Translate DIBELS, Acadience, or MAP scores into a targeted small-group intervention script.</p>
          <ol style="padding-left:1.4rem;line-height:1.7;color:#333">
            <li>Click the <strong>Diagnose Student</strong> tab.</li>
            <li>Input the student's <strong>Decoding Score</strong> (0.0 to 1.0, where 0.38 = Below Benchmark).</li>
            <li>Input the student's <strong>Language Comprehension Score</strong> (0.0 to 1.0).</li>
            <li>Select the target <strong>Grade Level</strong> and click <strong>Generate Remediation Plan</strong>.</li>
            <li>Review the generated <strong>Simple View Profile</strong> and click <strong>Print Remediation Cards</strong> to take small-group scripts to your teacher table.</li>
          </ol>
        </div>
      </div>

      <!-- Accordion Step 2 -->
      <div class="m3-accordion" id="guide-step-2">
        <div class="m3-accordion-header" onclick="toggleGuide('guide-step-2')">
          <i class="fa-solid fa-book-open step-icon"></i>
          <span>2. How to Check Text Decodability & Target Phonics Scope</span>
          <i class="fa-solid fa-chevron-down chevron"></i>
        </div>
        <div class="m3-accordion-body">
          <p style="margin-bottom:0.8rem"><strong>Goal:</strong> Ensure students are only reading text with phonics patterns they have been explicitly taught.</p>
          <ol style="padding-left:1.4rem;line-height:1.7;color:#333">
            <li>Click the <strong>Check Decodability</strong> tab.</li>
            <li>Select your target <strong>Grade Level</strong> and <strong>Phonics Skill</strong> (e.g. Silent-e, Blends, Digraphs).</li>
            <li>Paste any story or decodable passage.</li>
            <li>Click <strong>Check Decodability</strong> to view the percentage of decodable words, off-scope words, and high-frequency "Heart Words" to pre-teach.</li>
          </ol>
        </div>
      </div>

      <!-- Accordion Step 3 -->
      <div class="m3-accordion" id="guide-step-3">
        <div class="m3-accordion-header" onclick="toggleGuide('guide-step-3')">
          <i class="fa-solid fa-layer-group step-icon"></i>
          <span>3. How to Classify Vocabulary Tiers (Beck's Model)</span>
          <i class="fa-solid fa-chevron-down chevron"></i>
        </div>
        <div class="m3-accordion-body">
          <p style="margin-bottom:0.8rem"><strong>Goal:</strong> Select high-impact Tier 2 academic words to pre-teach prior to reading.</p>
          <ol style="padding-left:1.4rem;line-height:1.7;color:#333">
            <li>Click the <strong>Classify Vocabulary</strong> tab.</li>
            <li>Paste a selection from your read-aloud or guided reading book.</li>
            <li>Click <strong>Classify Vocabulary Tiers</strong>.</li>
            <li>Use the resulting breakdown to focus explicit vocabulary routines on <strong>Tier 2 (High-Utility Academic)</strong> words.</li>
          </ol>
        </div>
      </div>

      <!-- Accordion Step 4 -->
      <div class="m3-accordion" id="guide-step-4">
        <div class="m3-accordion-header" onclick="toggleGuide('guide-step-4')">
          <i class="fa-solid fa-microscope step-icon"></i>
          <span>4. How to Search Evidence & Effect Sizes</span>
          <i class="fa-solid fa-chevron-down chevron"></i>
        </div>
        <div class="m3-accordion-body">
          <p style="margin-bottom:0.8rem"><strong>Goal:</strong> Validate intervention choices with meta-analytic research from What Works Clearinghouse (WWC) and Best Evidence Encyclopedia (BEE).</p>
          <ol style="padding-left:1.4rem;line-height:1.7;color:#333">
            <li>Click the <strong>Evidence Search</strong> tab.</li>
            <li>Type any skill area such as <code>phonemic awareness</code>, <code>fluency</code>, <code>phonics</code>, or <code>comprehension</code>.</li>
            <li>Review effect sizes ($d$), source studies, and click <strong>Read Full Paper / Study</strong> to view the original study or IES practice guide.</li>
          </ol>
        </div>
      </div>

      <!-- Accordion Step 5 -->
      <div class="m3-accordion" id="guide-step-5">
        <div class="m3-accordion-header" onclick="toggleGuide('guide-step-5')">
          <i class="fa-solid fa-award step-icon"></i>
          <span>5. How to Lookup State Standards (Standards Satchel — CGLT)</span>
          <i class="fa-solid fa-chevron-down chevron"></i>
        </div>
        <div class="m3-accordion-body">
          <p style="margin-bottom:0.8rem">
            <strong>Goal:</strong> Attach official state framework standard codes to your reading intervention plans using
            <a href="https://rosetta.commongoodlt.com/" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">Standards Satchel (https://rosetta.commongoodlt.com/)</a>
            by Common Good Learning Tools.
          </p>
          <ol style="padding-left:1.4rem;line-height:1.7;color:#333">
            <li>Click the <strong>Standards Alignment</strong> tab.</li>
            <li>Enter your reading goal or skill (e.g. <em>decode words with silent e</em>).</li>
            <li>Select your state framework from all 50 U.S. states (Georgia GSE, California CCSS-CA, Texas TEKS, Florida B.E.S.T., NY, NC, OH, PA, VA, etc.).</li>
            <li>Click the direct <strong>Open Standard Deep Link</strong> or <strong>CASE API Endpoint</strong> to copy standard URLs directly into Google Classroom.</li>
          </ol>
        </div>
      </div>

    </div>
  </div>

</div><!-- /container -->

<footer>
  <p>© 2026 EdTech Labs • Science of Reading Teacher Workspace</p>
  <p style="font-size:0.8rem;color:var(--md-sys-color-secondary);margin-top:0.4rem">🔒 FERPA Compliant • Zero Data Retention • Student Privacy Guaranteed</p>
</footer>

<script>
var FRAMEWORKS = {FRAMEWORKS_JSON};
var PAPERS = {PAPERS_JSON};
var PILLAR_FINDINGS = {PILLAR_FINDINGS_JSON};

// Context-Aware Content Dictionary for Left Pull-Out Drawer
var CONTEXT_GUIDES = {{
  'tab-diagnose': {{
    title: '🩺 Simple View & Student Diagnostic Guide',
    research: {{
      title: 'Gough & Tunmer (1986); Hoover & Gough (1990)',
      summary: 'The Simple View of Reading states that Reading Comprehension (R) is the product of Decoding (D) and Language Comprehension (LC): R = D x LC. Both components are required for reading competence.',
      doi: 'https://doi.org/10.1007/BF02648824'
    }},
    concepts: [
      {{ term: 'Decoding Score (D)', def: 'Measures pseudoword and word reading accuracy (e.g. DIBELS NWF-CLS or Acadience). Range: 0.0 to 1.0.' }},
      {{ term: 'Language Comprehension (LC)', def: 'Measures listening comprehension or cloze maze performance (e.g. DIBELS Maze or MAP). Range: 0.0 to 1.0.' }},
      {{ term: 'Dyslexia / Decoding Deficit', def: 'Weak decoding (D < 0.6) with strong listening comprehension (LC >= 0.6). Requires explicit phonics & orthographic mapping.' }},
      {{ term: 'Hyperlexia / Specific Comprehension Deficit', def: 'Strong decoding (D >= 0.6) with weak listening comprehension (LC < 0.6). Requires vocabulary & syntax support.' }},
      {{ term: 'Garden-Variety / Dual Deficit', def: 'Weaknesses in both decoding and comprehension. Requires multi-component tier 2/3 intervention.' }},
      {{ term: 'Scripted I Do / We Do / You Do', def: 'Gradual release framework ensuring teacher modeling, guided practice, and independent application.' }}
    ]
  }},
  'tab-decodable': {{
    title: '📖 Decodability & Phonics Scope Guide',
    research: {{
      title: 'Linnea Ehri (2005) & National Reading Panel (2000)',
      summary: 'Systematic explicit phonics instruction significantly improves reading proficiency (d = 0.44-0.74). Decodable text supports orthographic mapping during the full alphabetic phase.',
      doi: 'https://doi.org/10.3102/00346543071003393'
    }},
    concepts: [
      {{ term: 'Decodable Text', def: 'Reading passages carefully matched to previously taught sound-spelling correspondences to prevent guessing.' }},
      {{ term: 'Target Phonics Skill', def: 'The explicit grapheme-phoneme pattern currently being taught (e.g. Silent-e, Consonant Blends, Vowel Teams).' }},
      {{ term: 'Off-Scope Words', def: 'Words in the text that contain untaught phonics patterns which students cannot yet decode systematically.' }},
      {{ term: 'Heart Words', def: 'High-frequency words with temporary or permanent irregular spelling parts pre-taught using orthographic mapping.' }},
      {{ term: 'Orthographic Mapping', def: 'The cognitive process of bonding spellings to pronunciations and meanings in memory.' }}
    ]
  }},
  'tab-vocab': {{
    title: '📚 Three-Tier Vocabulary Guide',
    research: {{
      title: 'Beck, McKeown & Kucan (2013); Marulis & Neuman (2010)',
      summary: 'Explicit instruction targeting Tier 2 academic vocabulary produces very large effect sizes (d = 0.88) for word learning and text comprehension across disciplines.',
      doi: 'https://doi.org/10.3102/0034654310377077'
    }},
    concepts: [
      {{ term: 'Tier 1 (Basic Words)', def: 'High-frequency conversational words acquired naturally through oral language (e.g. clock, happy, run).' }},
      {{ term: 'Tier 2 (High-Utility Academic)', def: 'Cross-domain academic words critical for written text comprehension (e.g. analyze, contrast, evidence, structure).' }},
      {{ term: 'Tier 3 (Domain-Specific)', def: 'Low-frequency technical terms specific to content areas (e.g. photosynthesis, isotope, stanza).' }},
      {{ term: 'Instructional Leverage', def: 'Pre-teaching Tier 2 words yields the highest transfer of comprehension skills across grade levels.' }}
    ]
  }},
  'tab-evidence': {{
    title: '🔬 Evidence & Effect Sizes Guide',
    research: {{
      title: 'What Works Clearinghouse (WWC) & Best Evidence Encyclopedia',
      summary: 'Meta-analyses evaluate intervention efficacy using standardized effect sizes (Cohen\'s d) across randomized controlled trials (RCTs).',
      doi: 'https://ies.ed.gov/ncee/wwc/'
    }},
    concepts: [
      {{ term: 'Effect Size (Cohen\'s d)', def: 'Quantifies intervention impact: d < 0.20 (small), d = 0.40 (1 yr growth hinge point), d >= 0.50 (large), d >= 0.80 (very large).' }},
      {{ term: 'Randomized Controlled Trial (RCT)', def: 'Experimental design randomly assigning students to control vs intervention groups.' }},
      {{ term: 'WWC Practice Guides', def: 'Consensus panel recommendations synthesized from high-tier empirical research.' }}
    ]
  }},
  'tab-standards': {{
    title: '🏛️ State Standards & CASE® Network Guide',
    research: {{
      title: '1EdTech CASE® Specification & Standards Satchel (CGLT)',
      summary: 'Machine-readable standards enable seamless alignment between literacy tools, state frameworks, and district LMS platforms.',
      doi: 'https://rosetta.commongoodlt.com/'
    }},
    concepts: [
      {{ term: 'Standards Satchel (Rosetta)', def: 'Machine-readable framework portal hosted by Common Good Learning Tools.' }},
      {{ term: 'CASE® Format', def: 'Competencies & Academic Standards Exchange open standard for interoperable learning objectives.' }},
      {{ term: 'Crosswalk Mapping', def: 'Algorithmic alignment connecting state frameworks (GSE, TEKS, B.E.S.T.) to Common Core (CCSS).' }},
      {{ term: 'Deep-Linking URIs', def: 'Direct URLs targeting specific standard GUID items for Google Classroom & lesson plan export.' }}
    ]
  }},
  'tab-guide': {{
    title: '🎓 Science of Reading Implementation Guide',
    research: {{
      title: 'Scarborough\'s Reading Rope (2001) & MTSS Framework',
      summary: 'Reading proficiency requires weaving together Word Recognition (automaticity) and Language Comprehension (strategic processing).',
      doi: 'https://doi.org/10.1598/0872075028'
    }},
    concepts: [
      {{ term: 'Word Recognition Strands', def: 'Phonological awareness, decoding, sight recognition (become increasingly automatic).' }},
      {{ term: 'Language Comprehension Strands', def: 'Background knowledge, vocabulary, syntax, verbal reasoning, literacy knowledge (become strategic).' }},
      {{ term: 'MTSS Tier 1 / 2 / 3', def: 'Universal core instruction (Tier 1), targeted small groups (Tier 2), and intensive diagnostic intervention (Tier 3).' }}
    ]
  }}
}};

function updateDrawerContent(tabId) {{
  var guide = CONTEXT_GUIDES[tabId] || CONTEXT_GUIDES['tab-diagnose'];
  document.getElementById('drawerTitle').innerText = guide.title;

  var html = '';
  // Section 1: Research Basis
  html += '<div class="drawer-section">';
  html += '<div class="drawer-section-title"><i class="fa-solid fa-flask"></i> Theoretical & Research Basis</div>';
  html += '<strong style="font-size:0.9rem;color:#1C1B1F">' + guide.research.title + '</strong>';
  html += '<p style="font-size:0.86rem;color:#444;margin-top:0.3rem">' + guide.research.summary + '</p>';
  if (guide.research.doi) {{
    html += '<a href="' + guide.research.doi + '" target="_blank" style="display:inline-flex;align-items:center;gap:0.4rem;font-size:0.78rem;color:var(--md-sys-color-primary);font-weight:700;margin-top:0.5rem;text-decoration:underline"><i class="fa-solid fa-arrow-up-right-from-square"></i> Read Original Citation / Research Source</a>';
  }}
  html += '</div>';

  // Section 2: Concepts & Tool Vocabulary
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

function switchTab(tabId) {{
  var tabs = document.querySelectorAll('.m3-tab-btn');
  var panes = document.querySelectorAll('.tab-pane');
  tabs.forEach(function(t) {{ t.classList.remove('active'); }});
  panes.forEach(function(p) {{ p.classList.remove('active'); }});

  var selectedTab = document.querySelector('.m3-tab-btn[data-tab="' + tabId + '"]');
  var selectedPane = document.getElementById(tabId);
  if (selectedTab && selectedPane) {{
    selectedTab.classList.add('active');
    selectedPane.classList.add('active');
  }}
  updateDrawerContent(tabId);
}}

function toggleGuide(id) {{
  var el = document.getElementById(id);
  el.classList.toggle('open');
}}

var sidebar = document.getElementById('sidebar');
var backdrop = document.getElementById('sidebarBackdrop');
var toggle = document.getElementById('sidebarToggle');
var isOpen = false;

function openSidebar() {{
  isOpen = true;
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
document.addEventListener('keydown', function(e) {{
  if(e.key === 'Escape' && isOpen) closeSidebar();
}});

// Initialize drawer content with default active tab
updateDrawerContent('tab-diagnose');

function tryExample() {{
  switchTab('tab-diagnose');
  document.getElementById('decoding').value = '0.38';
  document.getElementById('comprehension').value = '0.85';
  document.getElementById('grade').value = '2nd';
  document.getElementById('diagnoseForm').dispatchEvent(new Event('submit'));
}}

// ── Form Handlers ──
document.getElementById('diagnoseForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  document.getElementById('spinner').classList.add('show');
  document.getElementById('result').classList.remove('show');

  var data = {{
    decoding: parseFloat(document.getElementById('decoding').value),
    comprehension: parseFloat(document.getElementById('comprehension').value),
    grade: document.getElementById('grade').value
  }};

  try {{
    var resp = await fetch('/api/diagnose', {{
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
    'dyslexia': '<span class="profile-badge profile-dyslexia">⚠️ Decoding Deficit</span>',
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

  var cardsHtml = '<h3 style="margin-top:1.5rem;color:var(--md-sys-color-primary)">📋 Remediation Cards</h3>';
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
  html = html.replace(/([a-z]+)\\s*→\\s*([a-z]+)(\\s*→\\s*[a-z]+)*/gi, function(m){{
    return '<span class="word-chain">' + m + '</span>';
  }});
  return html;
}}

document.getElementById('decodabilityForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var data = {{text: document.getElementById('decodeText').value, grade: document.getElementById('decodeGrade').value, skill: document.getElementById('decodeSkill').value}};
  if(!data.text.trim()) return alert('Please paste a passage to check.');
  var resp = await fetch('/api/decodability', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var r = await resp.json();
  if(r.error_code || r.error) {{
    alert('Analysis Error: ' + (r.error_message || r.error || r.message));
    return;
  }}
  var totalWords = r.total_words || 0;
  var pct = r.decodable_pct !== undefined ? r.decodable_pct : 0;
  var offScope = r.off_scope_words || [];
  var heartWords = r.heart_words || [];

  var html = '<h3 style="margin-top:1rem;color:var(--md-sys-color-primary)">📊 Decodability Report</h3>';
  html += '<div class="stats-grid"><div class="stat"><div class="stat-num">' + totalWords + '</div><div class="stat-label">Total Words</div></div>';
  html += '<div class="stat"><div class="stat-num">' + pct + '%</div><div class="stat-label">Decodable</div></div>';
  html += '<div class="stat"><div class="stat-num">' + offScope.length + '</div><div class="stat-label">Off-Scope</div></div>';
  html += '<div class="stat"><div class="stat-num">' + heartWords.length + '</div><div class="stat-label">Heart Words</div></div></div>';
  if(offScope.length) html += '<p style="color:#D32F2F;margin-top:.8rem"><strong>⚠️ Off-scope words:</strong> ' + offScope.join(', ') + '</p>';
  if(heartWords.length) html += '<p style="color:#E65100;margin-top:.4rem"><strong>💛 Heart words to pre-teach:</strong> ' + heartWords.join(', ') + '</p>';
  document.getElementById('decodeResult').innerHTML = html;
  document.getElementById('decodeResult').classList.add('show');
}});

document.getElementById('vocabForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var data = {{text: document.getElementById('vocabText').value}};
  if(!data.text.trim()) return alert('Please paste some text.');
  var resp = await fetch('/api/vocabulary', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var r = await resp.json();

  if (r.error) {{
    alert('Vocabulary Analysis Error: ' + r.error);
    return;
  }}

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
  }} else {{
    html += '<p style="color:var(--md-sys-color-secondary);margin-top:0.8rem;padding:0.9rem;background:var(--md-sys-color-surface-variant);border-radius:var(--md-shape-corner-medium)">ℹ️ No Tier 2 academic words found in this passage. Most words are conversational (Tier 1) or specific terms (Tier 3).</p>';
  }}

  if (r.tier_3_words && r.tier_3_words.length > 0) {{
    var t3List = r.tier_3_words.map(function(w){{ return '<em>' + w.word + '</em>'; }}).join(', ');
    html += '<p style="color:var(--md-sys-color-tertiary);margin-top:0.6rem"><strong>🏷️ Tier 3 (Domain / Content) Words:</strong> ' + t3List + '</p>';
  }}

  var rec = r.recommendation || r.instructional_recommendation;
  if (rec) {{
    html += '<p style="margin-top:.8rem;padding:1.2rem;background:var(--md-sys-color-surface-variant);border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)"><strong>📝 Recommendation:</strong> ' + rec + '</p>';
  }}

  var resultEl = document.getElementById('vocabResult');
  resultEl.innerHTML = html;
  resultEl.classList.add('show');
}});

document.getElementById('evidenceForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var topic = document.getElementById('evidenceTopic').value;
  var resp = await fetch('/api/evidence?topic=' + encodeURIComponent(topic));
  var r = await resp.json();

  var html = '<h3 style="margin-top:1rem;color:var(--md-sys-color-primary)">🔬 Research Evidence for "' + r.topic + '"</h3>';
  html += '<p style="color:var(--md-sys-color-secondary);margin-bottom:1rem">' + r.total_papers + ' studies found' + (r.average_effect_size ? ' • Average effect size: d=' + r.average_effect_size : '') + '</p>';

  (r.papers||[]).forEach(function(p){{
    html += '<div style="background:var(--md-sys-color-surface-variant);padding:1.2rem;margin:.8rem 0;border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.6rem">';
    html += '<div><strong style="color:#1C1B1F;font-size:1.05rem">' + p.title + '</strong> <span style="color:var(--md-sys-color-secondary);font-size:0.85rem">(' + p.authors + ', ' + p.year + ')</span></div>';
    if (p.url) {{
      html += '<a href="' + p.url + '" target="_blank" class="hub-btn" style="padding:0.4rem 0.9rem;font-size:0.78rem;background:var(--md-sys-color-primary);color:#fff;font-weight:700" title="Open full research paper / study document"><i class="fa-solid fa-arrow-up-right-from-square"></i> Read Full Study (' + p.source + ')</a>';
    }}
    html += '</div>';

    if (p.effect_size) {{
      html += '<div style="margin-top:0.5rem"><span class="profile-badge profile-typical" style="font-size:0.75rem;padding:0.15rem 0.6rem"><i class="fa-solid fa-chart-line"></i> Effect Size d = ' + p.effect_size + '</span> <span style="color:var(--md-sys-color-primary);font-weight:600;font-size:0.85rem;margin-left:0.4rem">' + p.source + '</span></div>';
    }}

    html += '<p style="font-size:.95rem;color:#333;margin-top:.6rem">' + (p.finding||'') + '</p>';

    if (p.url) {{
      html += '<div style="font-size:0.78rem;color:var(--md-sys-color-secondary);margin-top:0.6rem;display:flex;align-items:center;gap:0.6rem"><i class="fa-solid fa-file-pdf" style="color:var(--md-sys-color-primary)"></i> <span>Direct Publication Link: <a href="' + p.url + '" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">' + p.url + '</a></span></div>';
    }}
    html += '</div>';
  }});

  document.getElementById('evidenceResult').innerHTML = html;
  document.getElementById('evidenceResult').classList.add('show');
}});

document.getElementById('standardsForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var data = {{description: document.getElementById('standardsSkill').value, state: document.getElementById('standardsState').value}};
  var resp = await fetch('/api/standards', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var r = await resp.json();

  var html = '<h3 style="margin-top:1rem;color:var(--md-sys-color-primary)">🏛️ Standards Matches for ' + r.state + ' (' + r.total_matches + ')</h3>';
  html += '<p style="color:var(--md-sys-color-secondary);font-size:0.9rem;margin-bottom:1rem"><a href="https://rosetta.commongoodlt.com/" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline"><i class="fa-solid fa-arrow-up-right-from-square"></i> Standards Satchel Portal (rosetta.commongoodlt.com)</a> — Common Good Learning Tools CASE® Exchange</p>';

  (r.matches||[]).forEach(function(m){{
    var deepLink = m.url || ('https://rosetta.commongoodlt.com/#/search?q=' + encodeURIComponent(m.code));
    var caseApiLink = m.case_api_uri || ('https://rosetta.commongoodlt.com/ims/case/v1p1/CFItems/' + encodeURIComponent(m.code));

    html += '<div style="background:var(--md-sys-color-surface-variant);padding:1.2rem;margin:.8rem 0;border-radius:var(--md-shape-corner-medium);border-left:4px solid var(--md-sys-color-primary)">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.6rem">';
    html += '<div><strong style="color:#1C1B1F;font-size:1.1rem">' + m.code + '</strong> <span class="profile-badge profile-hyperlexic" style="font-size:0.72rem;padding:0.15rem 0.5rem;margin-left:.5rem"><i class="fa-solid fa-network-wired"></i> Standards Satchel CASE®</span> <span style="color:var(--md-sys-color-secondary);font-size:0.85rem;margin-left:.5rem">' + m.state + ' Grade ' + m.grade + '</span></div>';
    html += '<div style="display:flex;gap:0.4rem;flex-wrap:wrap">';
    html += '<a href="' + deepLink + '" target="_blank" class="hub-btn" style="padding:0.4rem 0.9rem;font-size:0.78rem;background:var(--md-sys-color-primary);color:#fff;font-weight:700" title="Open direct deep link to this standard in Standards Satchel"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open Standard Deep Link</a>';
    html += '<a href="' + caseApiLink + '" target="_blank" class="hub-btn" style="padding:0.4rem 0.9rem;font-size:0.78rem;background:var(--md-sys-color-secondary-container);color:#1D192B" title="View CASE v1.1 REST API Endpoint"><i class="fa-solid fa-code"></i> CASE API Endpoint</a>';
    html += '</div></div>';
    html += '<p style="font-size:.95rem;color:#333;margin-top:.6rem">' + m.description + '</p>';
    html += '<div style="font-size:0.78rem;color:var(--md-sys-color-secondary);margin-top:0.6rem;display:flex;align-items:center;gap:0.6rem"><i class="fa-solid fa-link" style="color:var(--md-sys-color-primary)"></i> <span>Direct URI: <a href="' + deepLink + '" target="_blank" style="color:var(--md-sys-color-primary);font-weight:700;text-decoration:underline">' + deepLink + '</a></span></div>';
    html += '</div>';
  }});

  document.getElementById('standardsResult').innerHTML = html;
  document.getElementById('standardsResult').classList.add('show');
}});
</script>
</body>
</html>"""


# ── API Routes ──────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index():
    return build_frontend()


@app.post("/api/diagnose")
async def diagnose(data: dict):
    """Run Simple View diagnostic + generate remediation cards."""
    decoding = data.get("decoding", 0.5)
    comprehension = data.get("comprehension", 0.5)
    grade = data.get("grade", "1st")

    try:
        result = evaluate_simple_view(
            decoding=float(decoding),
            language_comprehension=float(comprehension),
            grade=grade,
        )
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/remediations")
async def list_remediations():
    return list_available_remediations()

@app.post("/api/decodability")
async def check_decodability_route(data: dict):
    """Check text decodability against a target skill."""
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
    """Find standards matching a skill description."""
    return align_standards(data.get("description", ""), data.get("state", "GA"))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sor-dashboard", "version": "3.7"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SoR Web Dashboard")
    parser.add_argument("--port", type=int, default=8093, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    args = parser.parse_args()

    print(f"📖 SoR Dashboard → http://localhost:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
