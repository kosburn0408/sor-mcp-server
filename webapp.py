"""SoR Web Dashboard — Teacher-friendly interface for the Science of Reading MCP server.

Single-file FastAPI app with embedded frontend. No command line needed.
Usage: python3 webapp.py  (runs on localhost:8093 by default)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import SoR tools directly — no MCP protocol overhead
from src.tools.diagnostics import evaluate_simple_view
from src.tools.remediation import get_instructional_remediation, list_available_remediations
from tools.evidence import search_evidence
from tools.vocabulary import classify_text

app = FastAPI(title="SoR Dashboard", version="2.0")

# ── Frontend HTML ───────────────────────────────────────────────────────────

FRONTEND = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SoR Dashboard — Science of Reading Tools</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f5f2ed;color:#2d1f0e;line-height:1.6}
header{background:linear-gradient(135deg,#1a1a3e,#2D2366);color:#fff;padding:1.5rem 2rem;text-align:center}
header h1{font-size:1.6rem;font-weight:800;margin-bottom:.25rem}
header p{color:#b0aec8;font-size:.9rem}
.container{max-width:800px;margin:0 auto;padding:1.5rem}
.card{background:#fff;border-radius:12px;padding:1.5rem;margin-bottom:1rem;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.card h2{font-size:1.2rem;color:#2D2366;margin-bottom:1rem;padding-bottom:.5rem;border-bottom:2px solid #FFD700}
.form-group{margin-bottom:1rem}
label{display:block;font-weight:600;margin-bottom:.3rem;color:#555;font-size:.85rem}
input,select{width:100%;padding:.7rem;border:2px solid #e0dcd0;border-radius:8px;font-size:1rem;font-family:inherit;transition:border-color .2s}
input:focus,select:focus{border-color:#FF6B35;outline:none}
.row{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:500px){.row{grid-template-columns:1fr}}
button{background:linear-gradient(135deg,#FF6B35,#e05a2a);color:#fff;border:none;padding:.8rem 2rem;border-radius:50px;font-size:1rem;font-weight:700;cursor:pointer;width:100%;transition:transform .15s,box-shadow .15s}
button:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(255,107,53,.3)}
button:disabled{opacity:.5;cursor:not-allowed}
.result{display:none;margin-top:1.5rem}
.result.show{display:block}
.profile-badge{display:inline-block;padding:.25rem .75rem;border-radius:20px;font-weight:700;font-size:.8rem;margin-right:.5rem}
.profile-dyslexia{background:#ffe0e0;color:#c0392b}
.profile-typical{background:#e0f0e0;color:#27ae60}
.profile-hyperlexic{background:#e0e8ff;color:#2c3e99}
.profile-garden{background:#fff3e0;color:#e67e22}
.remediation-card{background:#fffdf7;border:1px solid #e8ddd0;border-radius:8px;padding:1.5rem;margin:1rem 0;page-break-inside:avoid}
.remediation-card h3{color:#2D2366;font-size:1.1rem;margin-bottom:.5rem}
.remediation-card .section{margin:.8rem 0;padding-left:1rem;border-left:3px solid #FFD700}
.remediation-card .script-line{margin:.3rem 0;font-size:.9rem}
.script-i{color:#2D2366}
.script-we{color:#d4722a}
.script-you{color:#27ae60}
.word-chain{font-family:monospace;background:#f8f6f0;padding:.5rem 1rem;border-radius:6px;font-size:.95rem}
.feedback{padding:.5rem 1rem;border-radius:6px;margin:.5rem 0;font-size:.9rem}
.feedback-error{background:#fff0f0;border-left:3px solid #e74c3c}
.feedback-praise{background:#f0fff0;border-left:3px solid #27ae60}
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin:1rem 0}
.stat{text-align:center;padding:.8rem;background:#f8f6f0;border-radius:8px}
.stat-num{font-size:1.5rem;font-weight:800;color:#FF6B35}
.stat-label{font-size:.7rem;color:#999;text-transform:uppercase;letter-spacing:.05em}
.spinner{display:none;text-align:center;padding:2rem}
.spinner.show{display:block}
footer{text-align:center;padding:2rem;color:#999;font-size:.8rem}
.print-btn{background:#2D2366;margin-top:.5rem}
@media print{
  header,footer,.card:not(.result),button{display:none}
  .result{display:block!important}
  .remediation-card{box-shadow:none;border:none}
}
</style>
</head>
<body>
<header>
  <h1>📖 SoR Dashboard</h1>
  <p>Science of Reading — Diagnostic & Remediation Tools</p>
</header>

<div class="container">

  <!-- DIAGNOSE CARD -->
  <div class="card">
    <h2>🔍 Diagnose a Student</h2>
    <form id="diagnoseForm">
      <div class="row">
        <div class="form-group">
          <label>Decoding Score (0.0 – 1.0)</label>
          <input type="number" id="decoding" step="0.01" min="0" max="1" placeholder="e.g. 0.38" required>
        </div>
        <div class="form-group">
          <label>Language Comprehension (0.0 – 1.0)</label>
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
      <button type="submit">🔍 Diagnose Student</button>
    </form>

    <div class="spinner" id="spinner">Analyzing... <br><small>Running Simple View of Reading diagnostic</small></div>

    <div class="result" id="result">
      <div id="profileArea"></div>
      <div id="remediationArea"></div>
      <div id="nextSteps"></div>
      <button class="print-btn" onclick="window.print()">🖨️ Print Remediation Cards</button>
    </div>
  </div>

  <!-- QUICK TOOLS CARD -->
  <div class="card">
    <h2>⚡ Quick Tools</h2>
    <p style="color:#999;font-size:.85rem;margin-bottom:1rem">Additional tools for text analysis, evidence search, and standards alignment.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.5rem">
      <button onclick="window.open('https://github.com/kosburn0408/sor-mcp-server/blob/main/USER_GUIDE.md')" style="background:#2D2366">📖 Full User Guide</button>
      <button onclick="window.open('https://github.com/kosburn0408/sor-mcp-server/blob/main/examples/README.md')" style="background:#2D2366">📋 Example Workflows</button>
    </div>
  </div>

</div>

<footer>
  <p>Science of Reading MCP Server v2.0 • MIT Licensed • <a href="https://github.com/kosburn0408/sor-mcp-server" style="color:#FF6B35">GitHub</a></p>
  <p style="font-size:.7rem;color:#bbb;margin-top:.5rem">🔒 FERPA Compliant • Student data never leaves this server</p>
</footer>

<script>
document.getElementById('diagnoseForm').addEventListener('submit', async function(e){
  e.preventDefault();
  document.getElementById('spinner').classList.add('show');
  document.getElementById('result').classList.remove('show');

  var data = {
    decoding: parseFloat(document.getElementById('decoding').value),
    comprehension: parseFloat(document.getElementById('comprehension').value),
    grade: document.getElementById('grade').value
  };

  try {
    var resp = await fetch('/api/diagnose', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    var result = await resp.json();

    if (result.error) {
      alert('Error: ' + result.error);
      return;
    }

    renderResult(result);
  } catch(err) {
    alert('Connection error. Is the server running? ' + err.message);
  } finally {
    document.getElementById('spinner').classList.remove('show');
  }
});

function renderResult(r) {
  var profile = r.diagnostic;
  var badges = {
    'typical': '<span class="profile-badge profile-typical">✅ On Track</span>',
    'dyslexia': '<span class="profile-badge profile-dyslexia">⚠️ Decoding Deficit</span>',
    'hyperlexic': '<span class="profile-badge profile-hyperlexic">📚 Comprehension Focus</span>',
    'garden_variety': '<span class="profile-badge profile-garden">🔶 Dual Support Needed</span>'
  };

  var html = '<h3>' + badges[profile.reading_profile] + '</h3>';
  html += '<div class="stats-grid">';
  html += '<div class="stat"><div class="stat-num">' + (profile.decoding_score*100).toFixed(0) + '%</div><div class="stat-label">Decoding</div></div>';
  html += '<div class="stat"><div class="stat-num">' + (profile.language_comprehension_score*100).toFixed(0) + '%</div><div class="stat-label">Comprehension</div></div>';
  html += '<div class="stat"><div class="stat-num">' + profile.deficit_codes.length + '</div><div class="stat-label">Deficits Found</div></div>';
  html += '<div class="stat"><div class="stat-num">' + r.remediations.length + '</div><div class="stat-label">Cards Generated</div></div>';
  html += '</div>';

  document.getElementById('profileArea').innerHTML = html;

  // Render remediation cards as HTML (they come as markdown)
  var cardsHtml = '<h3 style="margin-top:1.5rem">📋 Remediation Cards</h3>';
  r.remediations.forEach(function(card, i){
    cardsHtml += '<div class="remediation-card">' + renderMarkdownCard(card) + '</div>';
  });
  document.getElementById('remediationArea').innerHTML = cardsHtml;

  // Next steps
  document.getElementById('nextSteps').innerHTML = '<p style="margin-top:1rem;padding:1rem;background:#f0f4ff;border-radius:8px"><strong>📝 Next Steps:</strong> ' + r.next_steps + '</p>';

  document.getElementById('result').classList.add('show');
  document.getElementById('result').scrollIntoView({behavior: 'smooth'});
}

function renderMarkdownCard(card) {
  // The server returns markdown — do basic HTML conversion
  var md = typeof card === 'string' ? card : card.markdown || JSON.stringify(card);
  var html = md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^> (.+)$/gm, '<blockquote style="color:#888;font-style:italic;border-left:3px solid #FFD700;padding-left:1rem;margin:.5rem 0">$1</blockquote>')
    .replace(/^🔵 (.+)$/gm, '<div class="script-line script-i">🔵 <strong>I DO:</strong> $1</div>')
    .replace(/^🟡 (.+)$/gm, '<div class="script-line script-we">🟡 <strong>WE DO:</strong> $1</div>')
    .replace(/^🟢 (.+)$/gm, '<div class="script-line script-you">🟢 <strong>YOU DO:</strong> $1</div>')
    .replace(/^❌ (.+)$/gm, '<div class="feedback feedback-error">❌ $1</div>')
    .replace(/^✅ (.+)$/gm, '<div class="feedback feedback-praise">✅ $1</div>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');

  // Convert word chains: "word1, word2, word3" → styled span
  html = html.replace(/([a-z]+)\s*→\s*([a-z]+)(\s*→\s*[a-z]+)*/gi, function(match){
    return '<span class="word-chain">' + match + '</span>';
  });

  return html;
}
</script>
</body>
</html>"""


# ── API Routes ──────────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index():
    return FRONTEND


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
    """List all available remediation deficit codes."""
    return list_available_remediations()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "sor-dashboard", "version": "2.0"}


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SoR Web Dashboard")
    parser.add_argument("--port", type=int, default=8093, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    args = parser.parse_args()

    print(f"📖 SoR Dashboard → http://localhost:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
