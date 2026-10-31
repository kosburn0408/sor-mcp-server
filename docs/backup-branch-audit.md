# Backup branch audit

Audit of the two pre-deploy backup branches, compared against main of their own repo.
Method: full tree comparison (git ls-tree) plus blob-level history check (git rev-list --objects main);
for agentic-edu-skills, every differing blob was also checked for existence anywhere in
kosburn0408/sor-mcp-server, because that repo is where the vendored copy came from.
Classifications: (a) older version of something already in main; (b) genuinely unique work
not in main; (c) generated/cache files. Report only: neither branch is deleted and nothing
was copied into main.

## Category (b): genuinely unique work not in main

**None.** No genuinely unique work exists on either branch. Every differing or branch-only
file content was found in main history of its own repo or, for the vendored copy, in
kosburn0408/sor-mcp-server.

## sor-mcp-server: hermes-production-wip vs main

| Path | Status | Class |
|---|---|---|
| evidence.py | branch-only | (a) |
| tools/__init__.py | branch-only | (a) |
| tools/__pycache__/__init__.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/decodability.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/evidence.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/lexile.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/privacy_sanitizer.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/remediation.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/schemas.cpython-311.pyc | branch-only | (c) |
| tools/__pycache__/vocabulary.cpython-311.pyc | branch-only | (c) |
| tools/decodability.py | branch-only | (a) |
| tools/decodable_resources.py | branch-only | (a) |
| tools/evidence.py | branch-only | (a) |
| tools/lexile.py | branch-only | (a) |
| tools/privacy_sanitizer.py | branch-only | (a) |
| tools/remediation.py | branch-only | (a) |
| tools/schemas.py | branch-only | (a) |
| tools/vocabulary.py | branch-only | (a) |
| vocabulary.py | branch-only | (a) |
| .gitignore | differs | (a) |
| Dockerfile | differs | (a) |
| README.md | differs | (a) |
| USER_GUIDE.md | differs | (a) |
| db/seed.py | differs | (a) |
| db/sor_evidence.duckdb | differs | (c) |
| pyproject.toml | differs | (a) |
| requirements.txt | differs | (a) |
| server.py | differs | (a) |
| src/prompts/decodable.py | differs | (a) |
| src/prompts/explicit_phonics.py | differs | (a) |
| src/prompts/multisyllabic.py | differs | (a) |
| src/resources/frameworks.py | differs | (a) |
| src/resources/word_lists.py | differs | (a) |
| src/schemas/remediation.py | differs | (a) |
| src/tools/__init__.py | differs | (a) |
| src/tools/decodability.py | differs | (a) |
| src/tools/diagnostics.py | differs | (a) |
| src/tools/evidence.py | differs | (a) |
| src/tools/orthography.py | differs | (a) |
| src/tools/phonics.py | differs | (a) |
| src/tools/privacy.py | differs | (a) |
| src/tools/remediation.py | differs | (a) |
| tests/conftest.py | differs | (a) |
| tests/test_decodability.py | differs | (a) |
| tests/test_epic_sor_01.py | differs | (a) |
| tests/test_privacy.py | differs | (a) |
| tests/test_prompts.py | differs | (a) |
| tests/test_tools.py | differs | (a) |
| webapp.py | differs | (a) |

### Attention list (sor-mcp-server)

- src/routes/google_classroom.py: identical
- src/client/google_classroom.py: identical
- src/frontend/components/GoogleClassroomExportModal.jsx: identical
- src/tools/vocabulary.py: identical
- evidence.py: branch-only
- vocabulary.py: branch-only
- .gitignore: DIFFERS
- docker-compose.yml: identical
- mcp.json: identical
- static/sor_reading_rope.jpg: identical
- static/teacher_reading_hero.jpg: identical

## agentic-edu-skills: hermes-vendored-wip vs main

Vendored-copy blobs were cross-checked against sor-mcp-server (last column).

| Path | Status | Class | Blob exists in sor-mcp-server |
|---|---|---|---|
| mcp-servers/science-of-reading/.gitignore | branch-only | (b) | yes |
| mcp-servers/science-of-reading/decodability.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/evidence.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/examples/README.md | branch-only | (b) | yes |
| mcp-servers/science-of-reading/mcp.json | branch-only | (b) | yes |
| mcp-servers/science-of-reading/pyproject.toml | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/client/__init__.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/client/cache.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/client/google_classroom.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/client/sor_client.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/config.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/core/__init__.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/core/errors.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/core/router.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/errors.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/frontend/components/GoogleClassroomExportModal.jsx | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/__init__.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/decodable.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/decodable_passage.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/explicit_phonics.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/multisyllabic.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/phonics.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/standards.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/prompts/vocabulary.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/resources/__init__.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/resources/frameworks.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/resources/word_lists.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/routes/google_classroom.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/__init__.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/api.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/curriculum.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/decodability.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/phonics.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/prompts.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/remediation.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/schemas/standards.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/__init__.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/decodability.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/diagnostics.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/evidence.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/orthography.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/phonics.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/privacy.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/remediation.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/standards.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/src/tools/vocabulary.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/static/sor_reading_rope.jpg | branch-only | (b) | yes |
| mcp-servers/science-of-reading/static/teacher_reading_hero.jpg | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/conftest.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/fixtures/sample_scope.json | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/test_client.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/test_decodability.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/test_epic_sor_01.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/test_prompts.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/test_router.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/tests/test_tools.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/vocabulary.py | branch-only | (b) | yes |
| mcp-servers/science-of-reading/webapp.py | branch-only | (b) | yes |
| README.md | differs | (a) | yes |
| mcp-servers/science-of-reading/Dockerfile | differs | (b) | yes |
| mcp-servers/science-of-reading/README.md | differs | (b) | yes |
| mcp-servers/science-of-reading/USER_GUIDE.md | differs | (b) | yes |
| mcp-servers/science-of-reading/db/seed.py | differs | (b) | yes |
| mcp-servers/science-of-reading/db/sor_evidence.duckdb | differs | (c) | yes |
| mcp-servers/science-of-reading/docker-compose.yml | differs | (b) | yes |
| mcp-servers/science-of-reading/requirements.txt | differs | (b) | yes |
| mcp-servers/science-of-reading/server.py | differs | (b) | yes |
| mcp-servers/science-of-reading/tests/test_privacy.py | differs | (b) | yes |
| skills/science-of-reading/SKILL.md | differs | (a) | yes |

