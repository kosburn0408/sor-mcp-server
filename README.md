# Science of Reading MCP Server

[![MCP](https://img.shields.io/badge/MCP-1.26+-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Evidence-based literacy analysis MCP server aligned to the **Science of Reading** research. Provides text analysis tools backed by What Works Clearinghouse, Best Evidence Encyclopedia, and National Reading Panel findings — all embedded in a DuckDB analytical database.

## Theoretical Frameworks

| Framework | Key Insight |
|---|---|
| **Simple View of Reading** (Gough & Tunmer, 1986) | Reading comprehension = Decoding × Linguistic Comprehension |
| **Scarborough's Reading Rope** (2001) | Skilled reading weaves together Word Recognition and Language Comprehension strands |
| **Five Pillars** (NRP, 2000) | Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension |
| **WWC Practice Guides** (2010, 2016) | Evidence-based recommendations for K-3 foundational skills and comprehension |
| **Three-Tier Vocabulary** (Beck, McKeown & Kucan, 2013) | Tier 1 (basic), Tier 2 (academic), Tier 3 (domain-specific) |

## Tools

| Tool | Description |
|---|---|
| `analyze_lexile` | Estimate Lexile score, word count, sentence complexity, grade level |
| `check_decodability` | Calculate % of decodable words for K-3 based on phonics scope & sequence |
| `classify_vocabulary` | Classify text into Tier 1/2/3 with instructional recommendations |
| `match_word` | Single-word lookup in the vocabulary corpus (tier, frequency, decodable) |
| `search_evidence` | Query WWC/BEE/NRP research database by topic with effect sizes |
| `list_frameworks` | Enumerate all theoretical frameworks with descriptions |
| `list_assessments` | Browse evidence-based assessment tools (screener, diagnostic, PM, outcome) |
| `align_standards` | Map text/skills to CCSS, TEKS, B.E.S.T., or NY standards |
| `assess_comprehension` | Evaluate comprehension question types (literal/inferential/evaluative) |

## Quick Start

### Local (Python)

```bash
# Install
pip install -r requirements.txt

# Seed the database
python3 server.py --seed-only

# Run as MCP server (stdio)
python3 server.py
```

### Docker

```bash
# Build and seed
docker compose build
docker compose run --rm sor-seed

# Run SSE/HTTP dev server
docker compose up sor-sse

# Health check
curl http://localhost:8080/sse
```

### Hermes Agent Integration

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  science-of-reading:
    command: "python3"
    args:
      - "/root/agentic-edu/mcp-servers/science-of-reading/server.py"
    env:
      SOR_DB_PATH: "/root/agentic-edu/mcp-servers/science-of-reading/db/sor_evidence.duckdb"
    enabled: true
```

Or via CLI:

```bash
hermes mcp add science-of-reading \
  --command "python3" \
  --args "/root/agentic-edu/mcp-servers/science-of-reading/server.py" \
  --env SOR_DB_PATH=/root/agentic-edu/mcp-servers/science-of-reading/db/sor_evidence.duckdb
```

## Architecture

```
MCP Client (Hermes Agent)
    ↓ stdio (JSON-RPC 2.0)
SoR MCP Server (FastMCP)
    ├── tools/list → 9 tools exposed
    ├── tools/call → execute analysis
    │   ├── analyze_lexile(text)
    │   ├── check_decodability(text, grade)
    │   ├── classify_vocabulary(text, domain)
    │   ├── match_word(word, grade?)
    │   ├── search_evidence(topic)
    │   ├── list_frameworks()
    │   ├── list_assessments(type?)
    │   ├── align_standards(description, state, grade?)
    │   └── assess_comprehension(text, questions, grade)
    └── DuckDB (embedded OLAP)
        ├── research_papers (12 papers, WWC/BEE/NRP)
        ├── vocabulary_corpus (74 words, K-3)
        ├── standards (43 entries, 5 states: CCSS, Georgia GSE, Texas TEKS, Florida B.E.S.T., New York)
        ├── assessments (11 tools)
        └── theoretical_frameworks (6 frameworks)
```

## Database

The embedded DuckDB database includes:

- **12 research papers** with effect sizes (d=0.32 to d=0.75)
- **74 vocabulary words** across grades K-3 with tier classification and decodability
- **43 academic standards** from CCSS, Georgia GSE, Texas TEKS, Florida B.E.S.T., and New York
- **11 evidence-based assessments** (DIBELS, Acadience, MAP, CORE, PAST, QRI-6, etc.)
- **6 theoretical frameworks** with full descriptions and references

## Security

- **Stdio transport** — no network exposure in production mode
- **No hardcoded credentials** — all config via environment variables
- **Non-root user** — Docker container runs as `sor` user
- **Minimal dependencies** — slim Python base image, no unnecessary packages
- **Read-only DB mode** — analytical queries use DuckDB read-only connection

## Directory Structure

```
mcp-servers/science-of-reading/
├── server.py              # Main MCP server (FastMCP)
├── tools/
│   ├── __init__.py
│   ├── lexile.py          # Lexile text analysis
│   ├── decodability.py    # Decodable text checker
│   ├── vocabulary.py      # Tier 1/2/3 classifier
│   └── evidence.py        # WWC/BEE evidence + standards + assessments
├── db/
│   ├── __init__.py
│   ├── schema.sql         # DuckDB schema (5 tables + indexes)
│   ├── database.py        # Connection management
│   └── seed.py            # Seed data population
├── Dockerfile             # Multi-stage secure build
├── docker-compose.yml     # 3 profiles: stdio, sse, seed
├── requirements.txt       # mcp, duckdb, pyyaml
└── README.md              # This file
```

## License

MIT — see [LICENSE](LICENSE) for details.
