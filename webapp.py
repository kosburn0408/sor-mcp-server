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

  <!-- TOOL 2: Check Decodability -->
  <div class="card">
    <h2>📖 Check Decodability</h2>
    <p style="color:#999;font-size:.85rem;margin-bottom:1rem">Paste text from a book and check which words use untaught phonics patterns.</p>
    <form id="decodabilityForm">
      <div class="form-group">
        <label>Text to check</label>
        <textarea id="decodeText" rows="3" style="width:100%;padding:.7rem;border:2px solid #e0dcd0;border-radius:8px;font-family:inherit;font-size:.9rem" placeholder="Paste a short passage here..."></textarea>
      </div>
      <div class="row">
        <div class="form-group">
          <label>Grade Level</label>
          <select id="decodeGrade"><option value="K">K</option><option value="1st">1st</option><option value="2nd" selected>2nd</option><option value="3rd">3rd</option></select>
        </div>
        <div class="form-group">
          <label>Target Skill</label>
          <select id="decodeSkill">
            <option value="cvc_mixed">CVC Short Vowels</option>
            <option value="consonant_blends">Consonant Blends</option>
            <option value="cvce_silent_e">Silent-e (CVCe)</option>
            <option value="consonant_digraphs">Consonant Digraphs (sh,ch,th)</option>
            <option value="vowel_teams">Vowel Teams (ai,ee,oa)</option>
            <option value="r_controlled">R-Controlled (ar,or,er)</option>
          </select>
        </div>
      </div>
      <button type="submit">🔍 Check Decodability</button>
    </form>
    <div class="result" id="decodeResult"></div>
  </div>

  <!-- TOOL 3: Vocabulary Classifier -->
  <div class="card">
    <h2>📚 Classify Vocabulary</h2>
    <p style="color:#999;font-size:.85rem;margin-bottom:1rem">Paste a passage and get a Tier 1/2/3 word breakdown for pre-teaching.</p>
    <form id="vocabForm">
      <div class="form-group">
        <label>Text to classify</label>
        <textarea id="vocabText" rows="3" style="width:100%;padding:.7rem;border:2px solid #e0dcd0;border-radius:8px;font-family:inherit;font-size:.9rem" placeholder="Paste a passage for vocabulary analysis..."></textarea>
      </div>
      <button type="submit">📊 Classify Words</button>
    </form>
    <div class="result" id="vocabResult"></div>
  </div>

  <!-- TOOL 4: Evidence Search -->
  <div class="card">
    <h2>🔬 Evidence Search</h2>
    <p style="color:#999;font-size:.85rem;margin-bottom:1rem">Search WWC and BEE research for evidence on reading topics.</p>
    <form id="evidenceForm">
      <div class="form-group">
        <label>Topic</label>
        <input type="text" id="evidenceTopic" placeholder="e.g. phonics, fluency, vocabulary, comprehension..." required>
      </div>
      <button type="submit">🔍 Search Evidence</button>
    </form>
    <div class="result" id="evidenceResult"></div>
  </div>

  <!-- TOOL 5: Standards Alignment -->
  <div class="card">
    <h2>🏛️ Standards Alignment</h2>
    <p style="color:#999;font-size:.85rem;margin-bottom:1rem">Find Georgia GSE or CCSS standards for a reading skill.</p>
    <form id="standardsForm">
      <div class="row">
        <div class="form-group">
          <label>Skill Description</label>
          <input type="text" id="standardsSkill" placeholder="e.g. decode words with consonant blends" required>
        </div>
        <div class="form-group">
          <label>State</label>
          <select id="standardsState">
            <option value="GEORGIA" selected>Georgia GSE</option>
            <option value="CCSS">Common Core</option>
            <option value="TEXAS">Texas TEKS</option>
            <option value="FLORIDA">Florida B.E.S.T.</option>
          </select>
        </div>
      </div>
      <button type="submit">🔍 Find Standards</button>
    </form>
    <div class="result" id="standardsResult"></div>
  </div>

  <!-- HELP LINKS -->
  <div class="card">
    <h2>📋 Resources</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.5rem">
      <button onclick="window.open('https://github.com/kosburn0408/sor-mcp-server/blob/main/USER_GUIDE.md')" style="background:#2D2366;font-size:.85rem">📖 Full User Guide</button>
      <button onclick="window.open('https://github.com/kosburn0408/sor-mcp-server/blob/main/examples/README.md')" style="background:#2D2366;font-size:.85rem">📋 Example Workflows</button>
      <button onclick="window.open('https://github.com/kosburn0408/sor-mcp-server')" style="background:#2D2366;font-size:.85rem">💻 GitHub Repo</button>
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
    html = html.replace(/([a-z]+)\s*→\s*([a-z]+)(\s*→\s*[a-z]+)*/gi, function(m){
      return '<span class="word-chain">' + m + '</span>';
    });
    return html;
  }

  // ── Tool 2: Check Decodability ──
  document.getElementById('decodabilityForm').addEventListener('submit', async function(e){
    e.preventDefault();
    var data = {text: document.getElementById('decodeText').value, grade: document.getElementById('decodeGrade').value, skill: document.getElementById('decodeSkill').value};
    if(!data.text.trim()) return alert('Please paste some text to check.');
    var resp = await fetch('/api/decodability', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    var r = await resp.json();
    var html = '<h3 style="margin-top:1rem">📊 Decodability Report</h3>';
    html += '<div class="stats-grid"><div class="stat"><div class="stat-num">' + r.total_words + '</div><div class="stat-label">Total Words</div></div>';
    html += '<div class="stat"><div class="stat-num">' + r.decodable_pct + '%</div><div class="stat-label">Decodable</div></div>';
    html += '<div class="stat"><div class="stat-num">' + (r.off_scope_words||[]).length + '</div><div class="stat-label">Off-Scope</div></div>';
    html += '<div class="stat"><div class="stat-num">' + (r.heart_words||[]).length + '</div><div class="stat-label">Heart Words</div></div></div>';
    if(r.off_scope_words && r.off_scope_words.length) html += '<p style="color:#e74c3c"><strong>⚠️ Off-scope words:</strong> ' + r.off_scope_words.join(', ') + '</p>';
    if(r.heart_words && r.heart_words.length) html += '<p style="color:#e67e22"><strong>💛 Heart words to pre-teach:</strong> ' + r.heart_words.join(', ') + '</p>';
    document.getElementById('decodeResult').innerHTML = html;
    document.getElementById('decodeResult').classList.add('show');
  });

  // ── Tool 3: Vocabulary Classifier ──
  document.getElementById('vocabForm').addEventListener('submit', async function(e){
    e.preventDefault();
    var data = {text: document.getElementById('vocabText').value};
    if(!data.text.trim()) return alert('Please paste some text.');
    var resp = await fetch('/api/vocabulary', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    var r = await resp.json();
    var html = '<h3 style="margin-top:1rem">📚 Vocabulary Breakdown</h3>';
    var tiers = r.tier_counts || {};
    html += '<div class="stats-grid"><div class="stat"><div class="stat-num">'+(tiers.tier_1||0)+'</div><div class="stat-label">Tier 1 (Basic)</div></div><div class="stat"><div class="stat-num">'+(tiers.tier_2||0)+'</div><div class="stat-label">Tier 2 (Academic)</div></div><div class="stat"><div class="stat-num">'+(tiers.tier_3||0)+'</div><div class="stat-label">Tier 3 (Domain)</div></div><div class="stat"><div class="stat-num">'+r.total_words+'</div><div class="stat-label">Total Words</div></div></div>';
    if(r.recommendation) html += '<p style="margin-top:.5rem;padding:.8rem;background:#f0f4ff;border-radius:8px"><strong>📝 Recommendation:</strong> ' + r.recommendation + '</p>';
    document.getElementById('vocabResult').innerHTML = html;
    document.getElementById('vocabResult').classList.add('show');
  });

  // ── Tool 4: Evidence Search ──
  document.getElementById('evidenceForm').addEventListener('submit', async function(e){
    e.preventDefault();
    var topic = document.getElementById('evidenceTopic').value;
    var resp = await fetch('/api/evidence?topic=' + encodeURIComponent(topic));
    var r = await resp.json();
    var html = '<h3 style="margin-top:1rem">🔬 Research on "' + r.topic + '"</h3>';
    html += '<p style="color:#888">' + r.total_papers + ' papers found' + (r.average_effect_size ? ' • Average effect size: d=' + r.average_effect_size : '') + '</p>';
    (r.papers||[]).forEach(function(p){
      html += '<div style="background:#fafaf7;padding:.8rem;margin:.5rem 0;border-radius:8px;border-left:3px solid #FFD700;padding-left:1rem"><strong>' + p.title + '</strong> (' + p.year + ')<br><span style="color:#FF6B35;font-weight:700">d=' + p.effect_size + '</span> — ' + p.source + '<br><span style="font-size:.85rem;color:#666">' + (p.finding||'').substring(0,150) + '...</span></div>';
    });
    document.getElementById('evidenceResult').innerHTML = html;
    document.getElementById('evidenceResult').classList.add('show');
  });

  // ── Tool 5: Standards Alignment ──
  document.getElementById('standardsForm').addEventListener('submit', async function(e){
    e.preventDefault();
    var data = {description: document.getElementById('standardsSkill').value, state: document.getElementById('standardsState').value};
    var resp = await fetch('/api/standards', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    var r = await resp.json();
    var html = '<h3 style="margin-top:1rem">🏛️ Standards Matches (' + r.total_matches + ')</h3>';
    (r.matches||[]).forEach(function(m){
      html += '<div style="background:#fafaf7;padding:.8rem;margin:.5rem 0;border-radius:8px;border-left:3px solid #2D2366;padding-left:1rem"><strong style="color:#2D2366">' + m.code + '</strong> <span style="color:#999;font-size:.8rem">' + m.state + ' Grade ' + m.grade + '</span><br>' + m.description + '</div>';
    });
    document.getElementById('standardsResult').innerHTML = html;
    document.getElementById('standardsResult').classList.add('show');
  });
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
    return list_available_remediations()

@app.post("/api/decodability")
async def check_decodability(data: dict):
    """Check text decodability against a target skill."""
    from tools.decodability import check_decodability
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
    from tools.evidence import align_standards
    return align_standards(data.get("description", ""), data.get("state", "GEORGIA"))


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
