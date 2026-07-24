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
from starlette.middleware.base import BaseHTTPMiddleware
import time, uvicorn

app = FastAPI(title="SoR Dashboard", version="2.5")

# ── Security Middleware ─────────────────────────────────────────────────────

# CORS — restrict to known domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://edtechlabs.dev", "https://sor.edtechlabs.dev", "http://localhost:8093"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Rate limiting — 60 requests per minute per IP
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
        if window["count"] > 60:  # Burst: 60/min
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
    """Load user guide, examples, and DuckDB research into JSON-safe dicts."""
    base = Path(__file__).resolve().parent

    # User guide
    ug_path = base / "USER_GUIDE.md"
    user_guide = ug_path.read_text() if ug_path.exists() else ""

    # Examples
    ex_path = base / "examples" / "README.md"
    examples_md = ex_path.read_text() if ex_path.exists() else ""

    examples = _parse_examples(examples_md)
    frameworks, papers = _query_research(base)
    pillar_findings = _build_pillar_findings(papers)

    return {
        "user_guide": user_guide,
        "examples": examples,
        "frameworks": frameworks,
        "papers": papers,
        "pillar_findings": pillar_findings,
    }


def _parse_examples(md_text: str):
    """Parse the examples README into individual workflow blocks."""
    import re
    examples = []
    blocks = re.split(r'\n## (\d+)\.\s', md_text)
    if len(blocks) > 1:
        for i in range(1, len(blocks), 2):
            title = blocks[i].strip()
            body = blocks[i + 1].strip() if i + 1 < len(blocks) else ""
            desc_match = re.match(r'^>?\s*(.+?)(?:\n|$)', body)
            description = desc_match.group(1).strip() if desc_match else ""
            body_short = re.sub(r'```.*?```', '```python\n# (code block)\n```', body, flags=re.DOTALL)
            examples.append({
                "num": i // 2 + 1,
                "title": title,
                "description": description,
                "body": body_short,
            })
    return examples


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
            "SELECT id, title, authors, year, framework, effect_size, source, finding "
            "FROM research_papers ORDER BY id"
        ).fetchall():
            papers.append({
                "id": row[0],
                "title": row[1],
                "authors": row[2] or "",
                "year": row[3],
                "framework": row[4],
                "effect_size": round(row[5], 2) if row[5] else None,
                "source": row[6],
                "finding": row[7] or "",
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
            "finding": p["finding"][:200] if p["finding"] else "",
        })
    return findings


# ── Build Frontend ───────────────────────────────────────────────────────────

def build_frontend() -> str:
    """Build the tabbed HTML frontend with embedded sidebar data."""
    data = _load_sidebar_data()

    USER_GUIDE_JSON = json.dumps(data["user_guide"])
    EXAMPLES_JSON = json.dumps(data["examples"])
    FRAMEWORKS_JSON = json.dumps(data["frameworks"])
    PAPERS_JSON = json.dumps(data["papers"])
    PILLAR_FINDINGS_JSON = json.dumps(data["pillar_findings"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EdTech Labs — Science of Reading Teacher Workspace</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='6' fill='%232D2366'/><text x='16' y='23' text-anchor='middle' font-size='20'>🧠</text></svg>">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Inter',sans-serif;background:#f5f2ed;color:#2d1f0e;line-height:1.6;overflow-x:hidden}}

/* ── Header ── */
.header{{background:linear-gradient(135deg,#1a1a3e,#2D2366);color:#fff;padding:1rem 1.5rem;display:flex;align-items:center;gap:1rem;position:sticky;top:0;z-index:500;box-shadow:0 4px 12px rgba(0,0,0,.15)}}
.header-title{{display:flex;align-items:center;gap:.6rem;flex:1}}
.header h1{{font-size:1.3rem;font-weight:800;margin:0;letter-spacing:-0.02em;color:#fff}}
.header .badge{{background:linear-gradient(135deg,#FF6B35,#e05a2a);color:#fff;font-size:.65rem;font-weight:700;padding:.2rem .6rem;border-radius:20px;text-transform:uppercase;letter-spacing:.05em}}

/* ── Sidebar Toggle ── */
.sidebar-toggle{{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#fff;font-size:1.1rem;cursor:pointer;padding:.4rem .8rem;border-radius:8px;display:flex;align-items:center;gap:.5rem;transition:all .2s}}
.sidebar-toggle:hover{{background:rgba(255,255,255,.2);transform:none}}

/* ── Sidebar Backdrop & Panel ── */
.sidebar-backdrop{{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:800;opacity:0;pointer-events:none;transition:opacity .3s}}
.sidebar-backdrop.open{{opacity:1;pointer-events:auto}}

.sidebar{{position:fixed;top:0;left:0;height:100vh;width:340px;max-width:85vw;background:linear-gradient(180deg,#1a1a3e 0%,#2D2366 100%);color:#e0ddf0;z-index:900;overflow-y:auto;transform:translateX(-100%);transition:transform .3s cubic-bezier(.4,0,.2,1);box-shadow:4px 0 24px rgba(0,0,0,.3)}}
.sidebar.open{{transform:translateX(0)}}
.sidebar::-webkit-scrollbar{{width:4px}}
.sidebar::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.2);border-radius:4px}}
.sidebar-header{{padding:1.5rem;border-bottom:1px solid rgba(255,255,255,.1);text-align:center}}
.sidebar-header h2{{font-size:1.1rem;font-weight:700;color:#FFD700;margin-bottom:.3rem}}
.sidebar-header .brand{{font-size:.75rem;color:#b0aec8}}

/* ── Accordion Sections ── */
.sidebar-section{{border-bottom:1px solid rgba(255,255,255,.08)}}
.sidebar-section-header{{display:flex;align-items:center;gap:.6rem;padding:.9rem 1.2rem;cursor:pointer;font-weight:600;font-size:.9rem;color:#d0cce8;transition:background .2s;user-select:none}}
.sidebar-section-header:hover{{background:rgba(255,255,255,.05)}}
.sidebar-section-header i{{width:1.2rem;text-align:center;color:#FFD700;font-size:.85rem}}
.sidebar-section-header .chevron{{margin-left:auto;transition:transform .3s;font-size:.7rem;opacity:.6}}
.sidebar-section.open .sidebar-section-header .chevron{{transform:rotate(180deg);opacity:1}}
.sidebar-section-body{{max-height:0;overflow:hidden;transition:max-height .35s ease}}
.sidebar-section.open .sidebar-section-body{{max-height:2000px;overflow-y:auto}}
.sidebar-section-inner{{padding:0 1.2rem 1rem}}
.sidebar h3{{color:#FFD700;font-size:.85rem;margin:1rem 0 .5rem;font-weight:700}}
.sidebar h4{{color:#c8c0e8;font-size:.8rem;margin:.8rem 0 .4rem;font-weight:600}}
.sidebar p,.sidebar li{{font-size:.78rem;line-height:1.55;color:#c0bae0;margin:.3rem 0}}
.sidebar ul{{list-style:none;padding-left:.2rem}}
.sidebar li::before{{content:"•";color:#FFD700;margin-right:.5rem}}
.sidebar a{{color:#FF6B35;text-decoration:none}}
.sidebar a:hover{{text-decoration:underline}}

.research-card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:.7rem;margin:.5rem 0}}
.research-card .rc-title{{font-weight:600;font-size:.78rem;color:#e0ddf0}}
.research-card .rc-meta{{font-size:.7rem;color:#9088b8;margin:.2rem 0}}
.research-card .rc-finding{{font-size:.72rem;color:#b0a8d0;margin-top:.3rem;font-style:italic}}
.effect-badge{{display:inline-block;background:rgba(255,107,53,.2);color:#FF6B35;font-size:.65rem;padding:.1rem .4rem;border-radius:4px;font-weight:700;margin-left:.3rem}}
.source-badge{{display:inline-block;background:rgba(255,215,0,.15);color:#FFD700;font-size:.6rem;padding:.1rem .35rem;border-radius:3px;font-weight:600;margin-left:.3rem}}
.pillar-group{{margin:.5rem 0;padding:.5rem;background:rgba(255,255,255,.04);border-radius:6px}}
.pillar-group h5{{color:#FFD700;font-size:.75rem;margin-bottom:.3rem;font-weight:700}}
.pillar-item{{font-size:.7rem;color:#c0bae0;padding:.2rem 0;border-bottom:1px solid rgba(255,255,255,.05);display:flex;align-items:baseline;gap:.3rem}}

.example-card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:8px;margin:.5rem 0;overflow:hidden}}
.example-card-header{{display:flex;align-items:center;gap:.5rem;padding:.6rem .7rem;cursor:pointer;font-size:.78rem;font-weight:600;color:#e0ddf0;transition:background .2s}}
.example-card-header:hover{{background:rgba(255,255,255,.05)}}
.example-card-header .ec-num{{background:#FF6B35;color:#fff;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:800;flex-shrink:0}}
.example-card-body{{max-height:0;overflow:hidden;transition:max-height .35s ease}}
.example-card.open .example-card-body{{max-height:600px;overflow-y:auto}}
.example-card-inner{{padding:.5rem .7rem .7rem 2rem;font-size:.7rem}}
.example-card-inner pre{{background:rgba(0,0,0,.3);padding:.5rem;border-radius:4px;overflow-x:auto;font-size:.65rem;line-height:1.4;margin:.3rem 0;color:#b0a8d0}}

/* ── Main Content & Layout ── */
.main-content{{transition:margin-left .3s cubic-bezier(.4,0,.2,1)}}
@media(min-width:1024px){{.main-content.shifted{{margin-left:340px}}}}
.container{{max-width:960px;margin:0 auto;padding:1.5rem}}

/* ── TAB BAR NAVIGATION ── */
.tab-nav-container{{background:#fff;border-bottom:1px solid #e2ddd5;position:sticky;top:62px;z-index:400;box-shadow:0 2px 8px rgba(0,0,0,.04)}}
.tab-nav{{display:flex;gap:.5rem;max-width:960px;margin:0 auto;padding:0 1rem;overflow-x:auto;scrollbar-width:none}}
.tab-nav::-webkit-scrollbar{{display:none}}
.tab-btn{{background:none;border:none;padding:.9rem 1.1rem;font-size:.9rem;font-weight:600;color:#665e52;cursor:pointer;display:flex;align-items:center;gap:.5rem;white-space:nowrap;border-bottom:3px solid transparent;transition:all .2s;outline:none}}
.tab-btn:hover{{color:#2D2366;background:rgba(45,35,102,.03)}}
.tab-btn.active{{color:#FF6B35;border-bottom-color:#FF6B35;font-weight:700}}
.tab-btn i{{font-size:1rem}}

/* ── TAB PANES ── */
.tab-pane{{display:none;animation:fadeIn .25s ease-in-out}}
.tab-pane.active{{display:block}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:translateY(0)}}}}

/* ── Card Components ── */
.card{{background:#fff;border-radius:14px;padding:1.8rem;margin-bottom:1.2rem;box-shadow:0 4px 16px rgba(0,0,0,.04);border:1px solid #eae5dc}}
.card h2{{font-size:1.25rem;color:#2D2366;margin-bottom:1rem;padding-bottom:.6rem;border-bottom:2px solid #FFD700;display:flex;align-items:center;gap:.6rem}}
.form-group{{margin-bottom:1.1rem}}
label{{display:block;font-weight:600;margin-bottom:.4rem;color:#4a4237;font-size:.88rem}}
input,select,textarea{{width:100%;padding:.75rem;border:2px solid #e0dcd0;border-radius:10px;font-size:.95rem;font-family:inherit;transition:all .2s;background:#fff}}
input:focus,select:focus,textarea:focus{{border-color:#FF6B35;outline:none;box-shadow:0 0 0 3px rgba(255,107,53,.15)}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem}}
@media(max-width:600px){{.row{{grid-template-columns:1fr}}}}

button.action-btn{{background:linear-gradient(135deg,#FF6B35,#e05a2a);color:#fff;border:none;padding:.85rem 2rem;border-radius:50px;font-size:1rem;font-weight:700;cursor:pointer;width:100%;transition:all .2s;box-shadow:0 4px 12px rgba(255,107,53,.25);display:flex;align-items:center;justify-content:center;gap:.5rem}}
button.action-btn:hover{{transform:translateY(-1px);box-shadow:0 6px 16px rgba(255,107,53,.35)}}
button.action-btn:active{{transform:translateY(0)}}
button:disabled{{opacity:.5;cursor:not-allowed}}

.help-icon{{display:inline-flex;align-items:center;justify-content:center;cursor:help;color:#888;font-size:.8rem;margin-left:.3rem;width:18px;height:18px;border-radius:50%;background:#f0ede6}}
.help-icon:hover{{color:#FF6B35;background:#ffe8e0}}

/* ── RESULTS AREA ── */
.result{{display:none;margin-top:1.5rem;padding-top:1.5rem;border-top:2px dashed #eae5dc}}
.result.show{{display:block}}
.profile-badge{{display:inline-flex;align-items:center;gap:.4rem;padding:.3rem .9rem;border-radius:20px;font-weight:700;font-size:.85rem}}
.profile-dyslexia{{background:#ffe6e6;color:#c0392b}}
.profile-typical{{background:#e6f9e6;color:#27ae60}}
.profile-hyperlexic{{background:#e6ecff;color:#2c3e99}}
.profile-garden{{background:#fff3e0;color:#e67e22}}

.remediation-card{{background:#fffdf7;border:1px solid #e8ddd0;border-radius:12px;padding:1.5rem;margin:1.2rem 0;page-break-inside:avoid;box-shadow:0 2px 8px rgba(0,0,0,.03)}}
.remediation-card h3{{color:#2D2366;font-size:1.15rem;margin-bottom:.6rem;display:flex;align-items:center;gap:.5rem}}
.remediation-card .section{{margin:.8rem 0;padding-left:1rem;border-left:3px solid #FFD700}}
.script-line{{margin:.4rem 0;font-size:.92rem;padding:.4rem .8rem;border-radius:6px}}
.script-i{{background:rgba(45,35,102,.05);color:#2D2366;border-left:3px solid #2D2366}}
.script-we{{background:rgba(212,114,42,.05);color:#d4722a;border-left:3px solid #d4722a}}
.script-you{{background:rgba(39,174,96,.05);color:#27ae60;border-left:3px solid #27ae60}}

.word-chain{{font-family:monospace;background:#f8f6f0;padding:.6rem 1rem;border-radius:8px;font-size:1rem;font-weight:700;color:#2D2366;display:inline-block}}
.feedback{{padding:.6rem 1rem;border-radius:8px;margin:.6rem 0;font-size:.9rem}}
.feedback-error{{background:#fff0f0;border-left:4px solid #e74c3c;color:#c0392b}}
.feedback-praise{{background:#f0fff0;border-left:4px solid #27ae60;color:#27ae60}}

.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.8rem;margin:1rem 0}}
.stat{{text-align:center;padding:1rem .8rem;background:#f8f6f0;border-radius:10px;border:1px solid #ece7de}}
.stat-num{{font-size:1.6rem;font-weight:800;color:#FF6B35;line-height:1.2}}
.stat-label{{font-size:.7rem;color:#777;text-transform:uppercase;letter-spacing:.05em;margin-top:.2rem;font-weight:600}}
.spinner{{display:none;text-align:center;padding:2rem;color:#2D2366;font-weight:600}}
.spinner.show{{display:block}}

footer{{text-align:center;padding:2.5rem 1rem;color:#888;font-size:.85rem;border-top:1px solid #eae5dc;margin-top:2rem}}
.print-btn{{background:#2D2366;color:#fff;margin-top:1rem;padding:.75rem 1.8rem;border-radius:50px;font-weight:700;border:none;cursor:pointer;display:inline-flex;align-items:center;gap:.5rem}}
.print-btn:hover{{background:#1a1a3e}}

@media print{{
  .sidebar,.sidebar-backdrop,.sidebar-toggle,.header,.tab-nav-container,footer,.card:not(.result-card),button.action-btn{{display:none!important}}
  .main-content{{margin-left:0!important}}
  .tab-pane{{display:block!important}}
  .result{{display:block!important}}
  .remediation-card{{box-shadow:none;border:1px solid #ccc}}
}}
</style>
</head>
<body>

<!-- Sidebar Backdrop -->
<div class="sidebar-backdrop" id="sidebarBackdrop"></div>

<!-- Sidebar Panel -->
<aside class="sidebar" id="sidebar">
  <div class="sidebar-header">
    <h2>🧠 SoR Resource Hub</h2>
    <div class="brand">EdTech Labs — Science of Reading</div>
  </div>

  <div class="sidebar-section open" id="sec-guide">
    <div class="sidebar-section-header" onclick="toggleSection('sec-guide')">
      <i class="fa-solid fa-book"></i> User Guide
      <i class="fa-solid fa-chevron-down chevron"></i>
    </div>
    <div class="sidebar-section-body">
      <div class="sidebar-section-inner" id="userGuideContent"></div>
    </div>
  </div>

  <div class="sidebar-section" id="sec-examples">
    <div class="sidebar-section-header" onclick="toggleSection('sec-examples')">
      <i class="fa-solid fa-code"></i> Example Workflows
      <i class="fa-solid fa-chevron-down chevron"></i>
    </div>
    <div class="sidebar-section-body">
      <div class="sidebar-section-inner" id="examplesContent"></div>
    </div>
  </div>

  <div class="sidebar-section" id="sec-research">
    <div class="sidebar-section-header" onclick="toggleSection('sec-research')">
      <i class="fa-solid fa-flask"></i> SoR Research
      <i class="fa-solid fa-chevron-down chevron"></i>
    </div>
    <div class="sidebar-section-body">
      <div class="sidebar-section-inner" id="researchContent"></div>
    </div>
  </div>

  <div style="padding:1.2rem;text-align:center;border-top:1px solid rgba(255,255,255,.08);margin-top:.5rem">
    <p style="font-size:.65rem;color:#7870a8">© 2026 EdTech Labs<br>FERPA Compliant • v2.5</p>
  </div>
</aside>

<!-- Header -->
<header class="header">
  <div class="header-title">
    <h1>🧠 EdTech Labs</h1>
    <span class="badge">Science of Reading</span>
  </div>
  <button class="sidebar-toggle" id="sidebarToggle" title="Open resource hub & research">
    <i class="fa-solid fa-book-open"></i>
    <span style="font-size:.8rem;font-weight:600">Resource Hub</span>
  </button>
</header>

<!-- TAB NAVIGATION -->
<div class="tab-nav-container">
  <nav class="tab-nav">
    <button class="tab-btn active" data-tab="tab-diagnose" onclick="switchTab('tab-diagnose')">
      <i class="fa-solid fa-user-check"></i> Diagnose Student
    </button>
    <button class="tab-btn" data-tab="tab-decodable" onclick="switchTab('tab-decodable')">
      <i class="fa-solid fa-book-reader"></i> Check Decodability
    </button>
    <button class="tab-btn" data-tab="tab-vocab" onclick="switchTab('tab-vocab')">
      <i class="fa-solid fa-layer-group"></i> Classify Vocabulary
    </button>
    <button class="tab-btn" data-tab="tab-evidence" onclick="switchTab('tab-evidence')">
      <i class="fa-solid fa-microscope"></i> Evidence Search
    </button>
    <button class="tab-btn" data-tab="tab-standards" onclick="switchTab('tab-standards')">
      <i class="fa-solid fa-graduation-cap"></i> Standards Alignment
    </button>
  </nav>
</div>

<!-- Main Content -->
<div class="main-content" id="mainContent">
<div class="container">

  <!-- ── TAB 1: DIAGNOSE STUDENT ── -->
  <div class="tab-pane active" id="tab-diagnose">
    <!-- Hero Banner -->
    <div class="card" style="background:linear-gradient(135deg,#1a1a3e,#2D2366);color:#fff;padding:1.8rem">
      <p style="color:#FFD700;font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.4rem;font-weight:700">Simple View of Reading Diagnostic</p>
      <h2 style="color:#fff;font-size:1.35rem;border:none;margin-bottom:.4rem;padding:0">Turn Assessment Scores into Actionable Lesson Plans</h2>
      <p style="color:#b0aec8;font-size:.88rem;max-width:650px;margin-bottom:1rem">Enter DIBELS, Acadience, or MAP Reading scores to generate printable, evidence-aligned remediation cards complete with I Do / We Do / You Do explicit teaching scripts.</p>
      <button onclick="tryExample()" style="background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.3);width:auto;font-size:.82rem;padding:.5rem 1.2rem;border-radius:30px;cursor:pointer;display:inline-flex;align-items:center;gap:.4rem;font-weight:600">
        <i class="fa-solid fa-wand-magic-sparkles" style="color:#FFD700"></i> Try Example Student (DIBELS NWF 0.38)
      </button>
    </div>

    <div class="card">
      <h2><i class="fa-solid fa-stethoscope" style="color:#FF6B35"></i> Student Assessment Scores</h2>
      <form id="diagnoseForm">
        <div class="row">
          <div class="form-group">
            <label>Decoding Score (0.0 – 1.0)
              <span class="help-icon" title="Decoding accuracy from DIBELS NWF-CLS, Acadience, or CORE Phonics. e.g., 0.38 = Below Benchmark.">ⓘ</span>
            </label>
            <input type="number" id="decoding" step="0.01" min="0" max="1" placeholder="e.g. 0.38" required>
          </div>
          <div class="form-group">
            <label>Language Comprehension (0.0 – 1.0)
              <span class="help-icon" title="Listening comprehension or vocabulary score from DIBELS Maze or MAP Reading. e.g., 0.85 = Proficient.">ⓘ</span>
            </label>
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
        <button type="submit" class="action-btn"><i class="fa-solid fa-magnifying-glass"></i> Generate Diagnostic & Remediation Cards</button>
      </form>

      <div class="spinner" id="spinner"><i class="fa-solid fa-circle-notch fa-spin fa-2x"></i><br><br>Analyzing scores against Simple View of Reading...</div>

      <div class="result" id="result">
        <div id="profileArea"></div>
        <div id="remediationArea"></div>
        <div id="nextSteps"></div>
        <div style="text-align:center">
          <button class="print-btn" onclick="window.print()"><i class="fa-solid fa-print"></i> Print Remediation Cards</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ── TAB 2: CHECK DECODABILITY ── -->
  <div class="tab-pane" id="tab-decodable">
    <div class="card">
      <h2><i class="fa-solid fa-book-open-reader" style="color:#FF6B35"></i> Decodability & Phonics Scope Checker</h2>
      <p style="color:#666;font-size:.88rem;margin-bottom:1.2rem">Paste a story or passage to verify if it aligns with taught phonics patterns and spot untaught "heart words" to pre-teach.</p>
      <form id="decodabilityForm">
        <div class="form-group">
          <label>Passage Text</label>
          <textarea id="decodeText" rows="4" placeholder="Paste a story or decodable text passage here..."></textarea>
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
        <button type="submit" class="action-btn"><i class="fa-solid fa-check-double"></i> Check Text Decodability</button>
      </form>
      <div class="result" id="decodeResult"></div>
    </div>
  </div>

  <!-- ── TAB 3: CLASSIFY VOCABULARY ── -->
  <div class="tab-pane" id="tab-vocab">
    <div class="card">
      <h2><i class="fa-solid fa-spell-check" style="color:#FF6B35"></i> Beck's Three-Tier Vocabulary Analyzer</h2>
      <p style="color:#666;font-size:.88rem;margin-bottom:1.2rem">Identify Tier 1 (Everyday), Tier 2 (High-Utility Academic), and Tier 3 (Domain-Specific) words in any classroom reading text.</p>
      <form id="vocabForm">
        <div class="form-group">
          <label>Reading Text</label>
          <textarea id="vocabText" rows="4" placeholder="Paste a reading selection to classify vocabulary..."></textarea>
        </div>
        <button type="submit" class="action-btn"><i class="fa-solid fa-filter"></i> Classify Tier 1, 2, and 3 Words</button>
      </form>
      <div class="result" id="vocabResult"></div>
    </div>
  </div>

  <!-- ── TAB 4: EVIDENCE SEARCH ── -->
  <div class="tab-pane" id="tab-evidence">
    <div class="card">
      <h2><i class="fa-solid fa-microscope" style="color:#FF6B35"></i> Science of Reading Research Engine</h2>
      <p style="color:#666;font-size:.88rem;margin-bottom:1.2rem">Search What Works Clearinghouse (WWC) and Best Evidence Encyclopedia (BEE) meta-analyses for literacy interventions.</p>
      <form id="evidenceForm">
        <div class="form-group">
          <label>Literacy Topic or Intervention</label>
          <input type="text" id="evidenceTopic" placeholder="e.g. phonics, fluency, vocabulary, comprehension, phonemic awareness..." required>
        </div>
        <button type="submit" class="action-btn"><i class="fa-solid fa-magnifying-glass"></i> Search Research Evidence</button>
      </form>
      <div class="result" id="evidenceResult"></div>
    </div>
  </div>

  <!-- ── TAB 5: STANDARDS ALIGNMENT ── -->
  <div class="tab-pane" id="tab-standards">
    <div class="card">
      <h2><i class="fa-solid fa-graduation-cap" style="color:#FF6B35"></i> State Standards Alignment Lookup</h2>
      <p style="color:#666;font-size:.88rem;margin-bottom:1.2rem">Match classroom reading activities and skills to state English Language Arts standards.</p>
      <form id="standardsForm">
        <div class="row">
          <div class="form-group">
            <label>Target Skill or Learning Goal</label>
            <input type="text" id="standardsSkill" placeholder="e.g. decode words with silent e, blend onset and rime..." required>
          </div>
          <div class="form-group">
            <label>State Framework</label>
            <select id="standardsState">
              <option value="GEORGIA" selected>Georgia GSE</option>
              <option value="CCSS">Common Core (CCSS)</option>
              <option value="TEXAS">Texas TEKS</option>
              <option value="FLORIDA">Florida B.E.S.T.</option>
            </select>
          </div>
        </div>
        <button type="submit" class="action-btn"><i class="fa-solid fa-award"></i> Find Matching Standards</button>
      </form>
      <div class="result" id="standardsResult"></div>
    </div>
  </div>

</div><!-- /container -->

<footer>
  <p>© 2026 EdTech Labs • Science of Reading MCP Server • <a href="https://github.com/kosburn0408/sor-mcp-server" style="color:#FF6B35" target="_blank">GitHub Repository</a></p>
  <p style="font-size:.75rem;color:#888;margin-top:.4rem">🔒 FERPA Compliant • Student data never leaves your server</p>
  <p style="font-size:.7rem;color:#999;margin-top:.3rem">
    <a href="#" onclick="showPrivacy();return false" style="color:#777">Privacy Policy</a> • 
    <a href="#" onclick="showAbout();return false" style="color:#777">About Science of Reading</a>
  </p>
</footer>

<!-- Privacy Policy Modal -->
<div id="privacyModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;align-items:center;justify-content:center" onclick="this.style.display='none'">
  <div style="background:#fff;max-width:550px;width:90%;padding:2rem;border-radius:12px;max-height:80vh;overflow-y:auto" onclick="event.stopPropagation()">
    <h3 style="color:#2D2366;margin-bottom:1rem">🔒 FERPA & Privacy Guarantee</h3>
    <p style="font-size:.9rem;color:#555;line-height:1.6">The SoR Dashboard does <strong>not</strong> collect, store, or transmit any personally identifiable information (PII).</p>
    <p style="font-size:.9rem;color:#555;line-height:1.6">Scores are evaluated in memory and discarded immediately after generating remediation cards. No names, IDs, or records are retained.</p>
    <button onclick="document.getElementById('privacyModal').style.display='none'" style="width:auto;margin-top:1rem;padding:.5rem 1.2rem">Close</button>
  </div>
</div>

<!-- About Modal -->
<div id="aboutModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;align-items:center;justify-content:center" onclick="this.style.display='none'">
  <div style="background:#fff;max-width:550px;width:90%;padding:2rem;border-radius:12px;max-height:80vh;overflow-y:auto" onclick="event.stopPropagation()">
    <h3 style="color:#2D2366;margin-bottom:1rem">📖 About Science of Reading Tools</h3>
    <p style="font-size:.9rem;color:#555;line-height:1.6">Ground in the Simple View of Reading (Gough & Tunmer, 1986), Scarborough's Reading Rope (2001), and National Reading Panel meta-analyses.</p>
    <p style="font-size:.9rem;color:#555;line-height:1.6">Created by <strong>EdTech Labs</strong> — Open Source under Global MCP Hackathon 2026.</p>
    <button onclick="document.getElementById('aboutModal').style.display='none'" style="width:auto;margin-top:1rem;padding:.5rem 1.2rem">Close</button>
  </div>
</div>

<script>
function showPrivacy(){{ document.getElementById('privacyModal').style.display='flex'; }}
function showAbout(){{ document.getElementById('aboutModal').style.display='flex'; }}
</script>

</div><!-- /main-content -->

<script>
// ── Embedded Sidebar Data ──
var USER_GUIDE_MD = {USER_GUIDE_JSON};
var EXAMPLES_DATA = {EXAMPLES_JSON};
var FRAMEWORKS = {FRAMEWORKS_JSON};
var PAPERS = {PAPERS_JSON};
var PILLAR_FINDINGS = {PILLAR_FINDINGS_JSON};

// ── Tab Switching Logic ──
function switchTab(tabId) {{
  var tabs = document.querySelectorAll('.tab-btn');
  var panes = document.querySelectorAll('.tab-pane');
  tabs.forEach(function(t) {{ t.classList.remove('active'); }});
  panes.forEach(function(p) {{ p.classList.remove('active'); }});

  var selectedTab = document.querySelector('.tab-btn[data-tab="' + tabId + '"]');
  var selectedPane = document.getElementById(tabId);

  if (selectedTab && selectedPane) {{
    selectedTab.classList.add('active');
    selectedPane.classList.add('active');
  }}
}}

// ── Sidebar Logic ──
var sidebar = document.getElementById('sidebar');
var backdrop = document.getElementById('sidebarBackdrop');
var toggle = document.getElementById('sidebarToggle');
var mainContent = document.getElementById('mainContent');
var isOpen = false;

function openSidebar() {{
  isOpen = true;
  sidebar.classList.add('open');
  backdrop.classList.add('open');
  if(window.innerWidth >= 1024) mainContent.classList.add('shifted');
  document.body.style.overflow = 'hidden';
}}

function closeSidebar() {{
  isOpen = false;
  sidebar.classList.remove('open');
  backdrop.classList.remove('open');
  mainContent.classList.remove('shifted');
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

function toggleSection(id) {{
  var sec = document.getElementById(id);
  sec.classList.toggle('open');
}}

function toggleExample(idx) {{
  var card = document.getElementById('example-' + idx);
  card.classList.toggle('open');
}}

function renderSidebarContent() {{
  var ugHtml = renderMarkdownSidebar(USER_GUIDE_MD);
  document.getElementById('userGuideContent').innerHTML = ugHtml;

  var exHtml = '<p style="font-size:.75rem;color:#9088b8;margin-bottom:.5rem">Click a workflow to expand:</p>';
  EXAMPLES_DATA.forEach(function(ex, i) {{
    var body = ex.body
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,.3);padding:1px 4px;border-radius:3px">$1</code>');
    exHtml += '<div class="example-card" id="example-' + i + '">';
    exHtml += '<div class="example-card-header" onclick="toggleExample(' + i + ')">';
    exHtml += '<span class="ec-num">' + ex.num + '</span>';
    exHtml += '<span>' + ex.title + '</span>';
    exHtml += '<i class="fa-solid fa-chevron-down" style="margin-left:auto;font-size:.6rem;opacity:.5"></i>';
    exHtml += '</div>';
    exHtml += '<div class="example-card-body"><div class="example-card-inner">';
    exHtml += '<p style="margin-bottom:.4rem;font-style:italic">' + ex.description + '</p>';
    exHtml += body;
    exHtml += '</div></div></div>';
  }});
  document.getElementById('examplesContent').innerHTML = exHtml;

  var resHtml = '';
  resHtml += '<h3><i class="fa-solid fa-lightbulb"></i> Theoretical Frameworks</h3>';
  FRAMEWORKS.forEach(function(f) {{
    resHtml += '<div class="research-card">';
    resHtml += '<div class="rc-title">' + f.name + '</div>';
    resHtml += '<div class="rc-meta">' + f.authors + ' (' + f.year + ')</div>';
    resHtml += '<div class="rc-finding">' + f.description.substring(0, 200) + '...</div>';
    resHtml += '</div>';
  }});

  resHtml += '<h3><i class="fa-solid fa-file-lines"></i> Key Research Papers</h3>';
  PAPERS.forEach(function(p) {{
    resHtml += '<div class="research-card">';
    resHtml += '<div class="rc-title">' + p.title + '</div>';
    resHtml += '<div class="rc-meta">' + p.authors + ' (' + p.year + ')';
    if(p.effect_size) resHtml += '<span class="effect-badge">d=' + p.effect_size.toFixed(2) + '</span>';
    resHtml += '<span class="source-badge">' + p.source + '</span>';
    resHtml += '</div>';
    resHtml += '<div class="rc-finding">' + (p.finding || '').substring(0, 180) + '...</div>';
    resHtml += '</div>';
  }});

  resHtml += '<h3><i class="fa-solid fa-magnifying-glass-chart"></i> What the Research Says</h3>';
  var pillarOrder = ['🔤 Phonemic Awareness','📖 Phonics','📈 Fluency','📚 Vocabulary','🧠 Comprehension'];
  pillarOrder.forEach(function(name) {{
    var items = PILLAR_FINDINGS[name];
    if(!items || !items.length) return;
    resHtml += '<div class="pillar-group"><h5>' + name + '</h5>';
    items.slice(0, 3).forEach(function(item) {{
      resHtml += '<div class="pillar-item">';
      resHtml += '<span style="flex-shrink:0;min-width:38px">';
      if(item.effect_size) resHtml += '<span class="effect-badge">d=' + item.effect_size.toFixed(2) + '</span>';
      resHtml += '</span>';
      resHtml += '<span>' + item.finding.substring(0, 120) + '</span>';
      resHtml += '</div>';
    }});
    resHtml += '</div>';
  }});

  document.getElementById('researchContent').innerHTML = resHtml;
}}

function renderMarkdownSidebar(md) {{
  var lines = md.split('\\n');
  var html = '';
  var inTable = false;
  var inCode = false;
  var tableHtml = '';
  for(var i=0; i<Math.min(lines.length, 280); i++) {{
    var line = lines[i];
    if(line.startsWith('```')) {{
      if(inCode) {{ inCode = false; continue; }}
      inCode = true; continue;
    }}
    if(inCode) continue;

    if(line.startsWith('|') && line.endsWith('|')) {{
      if(line.indexOf('---') > -1) continue;
      if(!inTable) {{ inTable = true; tableHtml = '<table style="width:100%;font-size:.65rem;border-collapse:collapse;margin:.4rem 0">'; }}
      var cells = line.split('|').filter(function(c){{return c.trim().length>0}});
      tableHtml += '<tr style="border-bottom:1px solid rgba(255,255,255,.1)">';
      var tag = i < 6 ? 'th' : 'td';
      cells.forEach(function(c) {{
        tableHtml += '<'+tag+' style="padding:.2rem .4rem;color:#d0cce8">' + c.trim() + '</'+tag+'>';
      }});
      tableHtml += '</tr>';
      continue;
    }} else if(inTable) {{
      html += tableHtml + '</table>';
      inTable = false;
      tableHtml = '';
    }}

    if(line.startsWith('### ')) html += '<h3>' + line.slice(4) + '</h3>';
    else if(line.startsWith('## ')) html += '<h3>' + line.slice(3) + '</h3>';
    else if(line.startsWith('# ')) html += '<h3>' + line.slice(2) + '</h3>';
    else if(line.startsWith('**') && line.endsWith('**')) html += '<h4>' + line.slice(2, -2) + '</h4>';
    else if(line.match(/^\\s*-\\s/)) {{
      var text = line.replace(/^\\s*-\\s+/, '');
      text = text.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
      text = text.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
      text = text.replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,.3);padding:1px 4px;border-radius:3px">$1</code>');
      html += '<li>' + text + '</li>';
    }}
    else if(line.startsWith('> ')) html += '<p style="border-left:2px solid #FF6B35;padding-left:.5rem;font-style:italic;opacity:.85">' + line.slice(2) + '</p>';
    else if(line.match(/^---+$/)) html += '<hr style="border:0;border-top:1px solid rgba(255,255,255,.1);margin:.5rem 0">';
    else if(line.trim().length > 0) {{
      var text = line.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
      text = text.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
      text = text.replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,.3);padding:1px 4px;border-radius:3px">$1</code>');
      html += '<p>' + text + '</p>';
    }}
  }}
  html += '<p style="text-align:center;margin-top:.8rem"><a href="https://github.com/kosburn0408/sor-mcp-server/blob/main/USER_GUIDE.md" target="_blank">📖 View Full User Guide →</a></p>';
  return html;
}}

renderSidebarContent();

function tryExample(){{
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

  var cardsHtml = '<h3 style="margin-top:1.5rem;color:#2D2366">📋 Remediation Cards</h3>';
  r.remediations.forEach(function(card){{
    cardsHtml += '<div class="remediation-card">' + renderMarkdownCard(card) + '</div>';
  }});
  document.getElementById('remediationArea').innerHTML = cardsHtml;
  document.getElementById('nextSteps').innerHTML = '<p style="margin-top:1rem;padding:1rem;background:#f0f4ff;border-radius:8px;border-left:4px solid #2D2366"><strong>📝 Next Steps:</strong> ' + r.next_steps + '</p>';
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
    .replace(/^> (.+)$/gm, '<blockquote style="color:#666;font-style:italic;border-left:3px solid #FFD700;padding-left:1rem;margin:.5rem 0">$1</blockquote>')
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
  var html = '<h3 style="margin-top:1rem;color:#2D2366">📊 Decodability Report</h3>';
  html += '<div class="stats-grid"><div class="stat"><div class="stat-num">' + r.total_words + '</div><div class="stat-label">Total Words</div></div>';
  html += '<div class="stat"><div class="stat-num">' + r.decodable_pct + '%</div><div class="stat-label">Decodable</div></div>';
  html += '<div class="stat"><div class="stat-num">' + (r.off_scope_words||[]).length + '</div><div class="stat-label">Off-Scope</div></div>';
  html += '<div class="stat"><div class="stat-num">' + (r.heart_words||[]).length + '</div><div class="stat-label">Heart Words</div></div></div>';
  if(r.off_scope_words && r.off_scope_words.length) html += '<p style="color:#e74c3c;margin-top:.8rem"><strong>⚠️ Off-scope words:</strong> ' + r.off_scope_words.join(', ') + '</p>';
  if(r.heart_words && r.heart_words.length) html += '<p style="color:#e67e22;margin-top:.4rem"><strong>💛 Heart words to pre-teach:</strong> ' + r.heart_words.join(', ') + '</p>';
  document.getElementById('decodeResult').innerHTML = html;
  document.getElementById('decodeResult').classList.add('show');
}});

document.getElementById('vocabForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var data = {{text: document.getElementById('vocabText').value}};
  if(!data.text.trim()) return alert('Please paste some text.');
  var resp = await fetch('/api/vocabulary', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var r = await resp.json();
  var html = '<h3 style="margin-top:1rem;color:#2D2366">📚 Vocabulary Breakdown</h3>';
  var tiers = r.tier_counts || {{}};
  html += '<div class="stats-grid"><div class="stat"><div class="stat-num">'+(tiers.tier_1||0)+'</div><div class="stat-label">Tier 1 (Basic)</div></div><div class="stat"><div class="stat-num">'+(tiers.tier_2||0)+'</div><div class="stat-label">Tier 2 (Academic)</div></div><div class="stat"><div class="stat-num">'+(tiers.tier_3||0)+'</div><div class="stat-label">Tier 3 (Domain)</div></div><div class="stat"><div class="stat-num">'+r.total_words+'</div><div class="stat-label">Total Words</div></div></div>';
  if(r.recommendation) html += '<p style="margin-top:.8rem;padding:1rem;background:#f0f4ff;border-radius:10px;border-left:4px solid #2D2366"><strong>📝 Recommendation:</strong> ' + r.recommendation + '</p>';
  document.getElementById('vocabResult').innerHTML = html;
  document.getElementById('vocabResult').classList.add('show');
}});

document.getElementById('evidenceForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var topic = document.getElementById('evidenceTopic').value;
  var resp = await fetch('/api/evidence?topic=' + encodeURIComponent(topic));
  var r = await resp.json();
  var html = '<h3 style="margin-top:1rem;color:#2D2366">🔬 Research Evidence for "' + r.topic + '"</h3>';
  html += '<p style="color:#666;margin-bottom:1rem">' + r.total_papers + ' studies found' + (r.average_effect_size ? ' • Average effect size: d=' + r.average_effect_size : '') + '</p>';
  (r.papers||[]).forEach(function(p){{
    html += '<div style="background:#fafaf7;padding:1rem;margin:.6rem 0;border-radius:10px;border-left:4px solid #FFD700;box-shadow:0 2px 6px rgba(0,0,0,.02)"><strong style="color:#2D2366;font-size:1rem">' + p.title + '</strong> (' + p.year + ')<br><span style="color:#FF6B35;font-weight:700">Effect Size d=' + p.effect_size + '</span> — <span style="color:#2D2366;font-weight:600">' + p.source + '</span><br><p style="font-size:.88rem;color:#555;margin-top:.4rem">' + (p.finding||'') + '</p></div>';
  }});
  document.getElementById('evidenceResult').innerHTML = html;
  document.getElementById('evidenceResult').classList.add('show');
}});

document.getElementById('standardsForm').addEventListener('submit', async function(e){{
  e.preventDefault();
  var data = {{description: document.getElementById('standardsSkill').value, state: document.getElementById('standardsState').value}};
  var resp = await fetch('/api/standards', {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});
  var r = await resp.json();
  var html = '<h3 style="margin-top:1rem;color:#2D2366">🏛️ Standards Matches (' + r.total_matches + ')</h3>';
  (r.matches||[]).forEach(function(m){{
    html += '<div style="background:#fafaf7;padding:1rem;margin:.6rem 0;border-radius:10px;border-left:4px solid #2D2366;box-shadow:0 2px 6px rgba(0,0,0,.02)"><strong style="color:#2D2366;font-size:1rem">' + m.code + '</strong> <span style="color:#777;font-size:.85rem;margin-left:.5rem">' + m.state + ' Grade ' + m.grade + '</span><br><p style="font-size:.9rem;color:#444;margin-top:.3rem">' + m.description + '</p></div>';
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
    return align_standards(data.get("description", ""), data.get("state", "GEORGIA"))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sor-dashboard", "version": "2.5"}


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SoR Web Dashboard")
    parser.add_argument("--port", type=int, default=8093, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    args = parser.parse_args()

    print(f"📖 SoR Dashboard → http://localhost:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
