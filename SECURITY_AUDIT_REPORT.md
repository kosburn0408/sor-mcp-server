# 🔐 SoR Web Dashboard — Security Audit Report

**Target:** http://10.100.0.35:8093  
**Date:** July 23, 2026  
**Auditor:** Hermes Agent (automated security audit)  
**Scope:** webapp.py, all API endpoints, dependencies, Dockerfile, infrastructure

---

## Executive Summary

The SoR Dashboard is a FastAPI-based web application serving diagnostic/remediation tools for the Science of Reading. The application has **no authentication, no rate limiting, no security headers, and no CORS restrictions**. Any client with network access can query all endpoints and extract the full remediation database. The application also relies on a vulnerable version of Starlette (CVE-2026-54282) and has multiple input validation gaps.

**Overall risk: HIGH** — The lack of authentication combined with the educational data context (even though no real PII hits the webapp) makes this a significant exposure for any production deployment.

---

## Findings by Severity

### 🔴 CRITICAL — No Authentication on Any Endpoint

| Field | Value |
|---|---|
| **Component** | All API routes (`/api/*`, `/health`) |
| **Severity** | Critical |
| **CWE** | CWE-306 (Missing Authentication for Critical Function) |

**Description:** All 7 API endpoints are publicly accessible without any form of authentication — no API key, no JWT, no basic auth, no session token. The `/api/remediations` endpoint exposes all remediation data, and `/api/evidence` exposes research database content. Any network client can enumerate and extract the complete remediation table and research database.

**Evidence:**
```bash
# All work without any auth header:
GET  /health              → 200 OK (version info)
GET  /api/remediations     → 200 OK (full remediation library)
GET  /api/evidence?topic=* → 200 OK (research database)
POST /api/diagnose         → 200 OK (diagnostic engine)
POST /api/decodability     → 200 OK
POST /api/vocabulary       → 200 OK
POST /api/standards        → 200 OK
```

**Remediation:**
1. Add an API key or token-based authentication middleware
2. For a teacher-facing tool, consider simple shared-secret API key:
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != os.environ.get("SOR_API_KEY", "changeme"):
        raise HTTPException(status_code=401, detail="Invalid API key")

app = FastAPI(dependencies=[Depends(verify_api_key)])
```
3. At minimum, protect `/api/remediations` and `/api/evidence` which expose the full curated dataset

---

### 🔴 CRITICAL — No Rate Limiting

| Field | Value |
|---|---|
| **Component** | All API routes |
| **Severity** | Critical |
| **CWE** | CWE-770 (Allocation of Resources Without Limits or Throttling) |

**Description:** No rate limiting is implemented. Rapid-fire testing showed 50 requests to `/health` processed in avg 4ms each, and 20 POST requests to `/api/diagnose` (the most expensive endpoint) all returned 200 without any throttling. An attacker can:
- Hammer `/api/diagnose` to consume CPU (diagnostic evaluation + remediation generation)
- Exfiltrate the full remediation and evidence database through `/api/remediations` and `/api/evidence`
- DoS the server with oversized vocabulary/decodability requests (50,000-word payload accepted instantly)

**Evidence:**
- 50 rapid GET /health → all 200, avg 4ms, no 429s
- 20 rapid POST /api/diagnose → all 200, avg 4ms, no 429s
- POST /api/vocabulary with 50,000 words → accepted and processed immediately

**Remediation:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/diagnose")
@limiter.limit("30/minute")
async def diagnose(data: dict): ...
```

---

### 🔴 CRITICAL — No CORS Configuration (Wide Open)

| Field | Value |
|---|---|
| **Component** | All API routes |
| **Severity** | Critical (combined with no auth) |
| **CWE** | CWE-942 (Permissive Cross-domain Policy) |

**Description:** No CORS middleware is configured. While FastAPI doesn't add CORS headers by default (so browsers will enforce same-origin), the absence of explicit CORS means the server doesn't restrict which origins can access it. Combined with no authentication, any website can make credentialed requests to this API from a user's browser if CORS is later relaxed.

**Evidence:** No `Access-Control-Allow-Origin` header present on any endpoint. OPTIONS requests return 405 (Method Not Allowed) instead of proper CORS preflight responses.

**Remediation:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8093", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

---

### 🔴 HIGH — Starlette CVE-2026-54282 (Path Host Poisoning)

| Field | Value |
|---|---|
| **Component** | Dependency: starlette==1.0.1 |
| **Severity** | High |
| **CWE** | CWE-20 (Improper Input Validation) |
| **CVE** | CVE-2026-54282 |

**Description:** Starlette prior to 1.3.0 has an unvalidated request path that can be concatenated into the URL authority, poisoning `request.url.hostname`. The installed version is 1.0.1, which is vulnerable. CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:L/A:N. EPSS Score: 8.76%.

**Remediation:** Upgrade Starlette to >= 1.3.0:
```bash
pip install --upgrade "starlette>=1.3.0"
```
Or in requirements.txt: `starlette>=1.3.0` (though pinning is preferred).

---

### 🔴 HIGH — No Security Headers

| Field | Value |
|---|---|
| **Component** | All HTTP responses |
| **Severity** | High |
| **CWE** | CWE-693 (Protection Mechanism Failure) |

**Description:** Missing all standard security headers:
- No `Strict-Transport-Security` (HSTS)
- No `Content-Security-Policy` (CSP)
- No `X-Frame-Options` (clickjacking protection)
- No `X-Content-Type-Options: nosniff` (MIME sniffing protection)
- No `Referrer-Policy`
- `Server: uvicorn` header leaks server technology/version

**Evidence:**
```
HTTP/1.1 200 OK
server: uvicorn          ← version disclosure
content-type: application/json
date: Thu, 23 Jul 2026 11:37:22 GMT
content-length: 62
(no security headers present)
```

**Remediation:**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Server"] = ""  # remove version disclosure
        return response
```

---

### 🔴 HIGH — Binds to 0.0.0.0 (All Interfaces)

| Field | Value |
|---|---|
| **Component** | webapp.py line 452 |
| **Severity** | High |
| **CWE** | CWE-668 (Exposure of Resource to Wrong Sphere) |

**Description:** The webapp binds to `0.0.0.0` by default, listening on ALL network interfaces. Combined with no authentication, this means the dashboard is exposed to the entire local network (and potentially the internet if behind a port-forwarding router).

**Evidence (webapp.py line 452):**
```python
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
```

**Remediation:**
```python
parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
```
Use a reverse proxy (nginx/Caddy) for external access with TLS termination.

---

### 🟠 MEDIUM — Input Reflection / Stored XSS Risk in Grade Field

| Field | Value |
|---|---|
| **Component** | `/api/diagnose` → remediation card rendering |
| **Severity** | Medium |
| **CWE** | CWE-79 (Improper Neutralization of Input During Web Page Generation) |

**Description:** The `grade` parameter is accepted without validation and reflected directly into the markdown remediation card output. Attack strings like `"__proto__"` and `"1st'; DROP TABLE students; --"` are blindly embedded in the output. While the frontend renders via `innerHTML` with markdown conversion, the raw API JSON response contains unescaped attacker-controlled content that could be stored and rendered unsafely by other consumers.

**Evidence:**
```
POST /api/diagnose {"decoding":0.5,"comprehension":0.5,"grade":"__proto__"}
→ Remediation card: "**Grade:** __proto__"
```

**Remediation:**
```python
VALID_GRADES = {"K", "1st", "2nd", "3rd", "4th", "5th"}
if grade not in VALID_GRADES:
    raise HTTPException(status_code=400, detail=f"Invalid grade. Must be one of: {', '.join(sorted(VALID_GRADES))}")
```

---

### 🟠 MEDIUM — Error Messages Leak Implementation Details

| Field | Value |
|---|---|
| **Component** | `/api/diagnose` error handling |
| **Severity** | Medium |
| **CWE** | CWE-209 (Generation of Error Message Containing Sensitive Information) |

**Description:** Python type conversion errors are returned verbatim, exposing internal implementation details. This includes the exact Python exception message and data types.

**Evidence:**
```
POST {"decoding":"<script>alert(1)</script>",...}
→ {"error": "could not convert string to float: '<script>alert(1)</script>'"}

POST {"decoding":null,...}
→ {"error": "float() argument must be a string or a real number, not 'NoneType'"}
```

**Remediation:**
```python
except (ValueError, TypeError) as e:
    return JSONResponse(
        {"error": "Invalid input: scores must be numbers between 0.0 and 1.0"},
        status_code=400
    )
```

---

### 🟠 MEDIUM — No Request Size Limits

| Field | Value |
|---|---|
| **Component** | All POST endpoints |
| **Severity** | Medium |
| **CWE** | CWE-770 (Allocation of Resources Without Limits) |

**Description:** No request body size limits are enforced. A 50,000-word vocabulary request (~500KB) was processed instantly without any size check. An attacker could send multi-megabyte payloads to `/api/vocabulary` or `/api/decodability` causing memory exhaustion.

**Evidence:** POST to `/api/vocabulary` with `"word ".repeat(50000)` → accepted and fully processed (50,000 tokens).

**Remediation:**
```python
from starlette.middleware.base import BaseHTTPMiddleware

class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.headers.get("content-length"):
            size = int(request.headers["content-length"])
            if size > 1_000_000:  # 1MB
                return JSONResponse({"error": "Request too large"}, status_code=413)
        return await call_next(request)
```

---

### 🟠 MEDIUM — Unpinned Dependencies

| Field | Value |
|---|---|
| **Component** | requirements.txt |
| **Severity** | Medium |
| **CWE** | CWE-1104 (Use of Unmaintained Third-Party Components) |

**Description:** All dependencies use `>=` (minimum version) without upper bounds. This means any build could pull in breaking or vulnerable versions. The `Dockerfile` uses `python:3.11-slim-bookworm` (float tag) without a digest pin, so image contents vary over time.

**Evidence (requirements.txt):**
```
mcp>=1.0.0
duckdb>=0.10.0
pyyaml>=6.0
pydantic>=2.0
pytest>=7.0
```

**Remediation:** Pin all versions:
```
mcp==1.0.0
duckdb==1.5.4
pyyaml==6.0.2
pydantic==2.10.0
fastapi==0.133.1
uvicorn==0.41.0
starlette==1.3.0  # upgrade required for CVE-2026-54282
```
Pin Dockerfile base image to digest:
```
FROM python:3.11-slim-bookworm@sha256:...
```

---

### 🟡 LOW — Grade Format Inconsistency (Frontend vs Backend)

| Field | Value |
|---|---|
| **Component** | `/api/decodability` |
| **Severity** | Low |

**Description:** The frontend sends grade as "1st" but the decodability backend expects "1". This causes the decodability endpoint to return an error when used from the UI form. The diagnostic endpoint handles "1st" correctly, creating an inconsistent API contract.

**Evidence:** Frontend sends `grade: "1st"` → Backend returns `"error": "Invalid grade '1ST'. Use K, 1, 2, or 3."`

**Remediation:** Standardize grade format across all endpoints. Either accept both formats with normalization:
```python
GRADE_MAP = {"K": "K", "1ST": "1", "1": "1", "2ND": "2", "2": "2", ...}
normalized = GRADE_MAP.get(grade.upper(), grade)
```

---

### 🟡 LOW — OPTIONS Method Returns 405

| Field | Value |
|---|---|
| **Component** | All API routes |
| **Severity** | Low |

**Description:** OPTIONS requests return 405 (Method Not Allowed) instead of proper CORS preflight responses with `Access-Control-*` headers. While this doesn't create a vulnerability by itself, it means the API doesn't properly participate in the CORS protocol.

**Evidence:** `OPTIONS /api/diagnose` → 405 with `allow: POST` header only.

**Remediation:** Add a CORS middleware (see Critical finding above). The middleware will automatically handle OPTIONS preflight requests.

---

### 🟢 INFO — Dockerfile Security: Good Practices Observed

| Field | Value |
|---|---|
| **Component** | Dockerfile |
| **Severity** | Info (Positive) |

**Positive findings in the Dockerfile:**
- ✅ Multi-stage build reduces attack surface (no gcc in final image)
- ✅ Non-root user (`sor`) created and used
- ✅ `USER sor` drops privileges before runtime
- ✅ `--no-install-recommends` for apt
- ✅ `--no-cache-dir` for pip
- ✅ Health check configured
- ✅ `PYTHONUNBUFFERED=1` set

**Minor improvement:** Consider adding `read_only: true` to the filesystem and `no-new-privileges: true` in docker-compose.

---

### 🟢 INFO — No Hardcoded Credentials or eval()/exec() Found

**Checked:** All `.py` files in the repository.  
**Result:** No hardcoded passwords, API keys, tokens, or credentials found. No `eval()`, `exec()`, `os.system()`, or `subprocess` calls in application code. The `_eval` reference in server.py is a function alias (`evaluate_simple_view as _eval`), not Python's `eval()`.

---

### 🟢 INFO — SQL Injection: Parameterized Queries Used

**Checked:** `tools/evidence.py`, `src/tools/diagnostics.py`, `src/tools/remediation.py`  
**Result:** All database queries use parameterized statements (`?` placeholders). No string interpolation in SQL queries. The SQL injection test (`DROP TABLE`) was handled safely — the malicious string was treated as a search term, not executed.

---

### 🟢 INFO — Path Traversal: Not Applicable

**Checked:** All endpoints that accept user input.  
**Result:** No file system access from user input. The application processes data entirely in-memory or via parameterized database queries. Path traversal strings like `../../../etc/passwd` are handled as plain text strings with no filesystem side effects.

---

## Summary Table

| # | Severity | Finding | Endpoint/Component |
|---|----------|---------|--------------------|
| 1 | 🔴 Critical | No authentication | All endpoints |
| 2 | 🔴 Critical | No rate limiting | All endpoints |
| 3 | 🔴 Critical | No CORS configuration | All endpoints |
| 4 | 🟠 High | Starlette CVE-2026-54282 | starlette==1.0.1 |
| 5 | 🟠 High | Missing security headers | All responses |
| 6 | 🟠 High | Binds to 0.0.0.0 | webapp.py |
| 7 | 🟡 Medium | Grade field XSS/reflection | /api/diagnose |
| 8 | 🟡 Medium | Error messages leak internals | /api/diagnose |
| 9 | 🟡 Medium | No request size limits | All POST endpoints |
| 10 | 🟡 Medium | Unpinned dependencies | requirements.txt |
| 11 | 🔵 Low | Grade format mismatch | /api/decodability |
| 12 | 🔵 Low | OPTIONS returns 405 | All endpoints |
| 13 | 🟢 Info | Dockerfile security: good | Dockerfile |
| 14 | 🟢 Info | No credentials/eval found | All source |
| 15 | 🟢 Info | SQLi: parameterized queries | evidence.py |
| 16 | 🟢 Info | Path traversal: N/A | All endpoints |

---

## Remediation Priority

### Phase 0 — Immediate (today)
1. **Bind to 127.0.0.1** — one-line change, blocks network exposure
2. **Add API key authentication** — protect all endpoints
3. **Add rate limiting** — prevent abuse and DoS

### Phase 1 — This Week
4. **Upgrade Starlette to >= 1.3.0** — fix CVE-2026-54282
5. **Add security headers** — CSP, HSTS, X-Frame-Options, etc.
6. **Add CORS middleware** — restrict origins
7. **Validate grade input** — whitelist allowed values

### Phase 2 — This Sprint
8. **Add request size limits** — prevent memory exhaustion
9. **Sanitize error messages** — don't leak Python internals
10. **Pin all dependencies** — in requirements.txt and Dockerfile
11. **Fix grade format inconsistency** — standardize across endpoints
