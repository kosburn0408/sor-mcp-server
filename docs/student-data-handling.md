# Student Data Handling: Science of Reading Teacher Workspace

**Draft for privacy review — prepared from the application source code**
System: Science of Reading Teacher Workspace (sor.edtechlabs.dev), part of the sor-mcp-server project
Sources: `src/tools/privacy.py`, the browser-side scrubber `sanitizeClientPII` in `webapp.py`, and the project README's "Limitations" section. This document describes what the code does. It is not a compliance determination.

## What data the application accepts

The workspace is a teacher-facing tool for analyzing reading instruction materials and student reading performance. It accepts:

- **Free text for analysis** — passages a teacher pastes in to check decodability, vocabulary, or readability, and free-text notes submitted with analysis requests.
- **Student record fields** (via the server's `sanitize_pii` function) — a defined set of fields in two classes:
  - *Identifier fields:* first/last/full/student name, state student ID (SSID), email, date of birth, address, city, ZIP, phone, guardian/parent name.
  - *Academic fields, which are retained for processing:* grade level, age, decoding and language-comprehension scores, fluency rate, accuracy, phonics error patterns, mastered skills, assessment scores, CASE competency IDs, intervention tier, attendance percentage.

## What is removed before processing, and how

Removal happens in two layers — in the teacher's browser before anything is sent, and again on the server before data is passed to a language model.

**Browser layer (`sanitizeClientPII`).** Before form text is sent, the page scans it and replaces:

- Email addresses → `[EMAIL_REDACTED]`
- Phone-number patterns → `[PHONE_REDACTED]`
- Date patterns (e.g. 12/31/2026) → `[DATE_REDACTED]`
- ID-shaped strings (2–3 letters followed by 4+ digits) and **digit runs of six or more** — the shape of Georgia GTIDs → `[ID_REDACTED]`
- The parts of the student name entered in the form's name field → `[STUDENT]`

When anything is removed, the page shows the teacher a notice naming the categories removed ("Removed before sending: …").

**Server layer (`src/tools/privacy.py`).** Identifier fields are dropped from the record entirely. In their place the record carries a **pseudonymous token**: an HMAC-SHA256 of the name/ID, keyed with a **per-process secret key** (32 random bytes generated when the process starts, held only in memory). Because the key exists only for the life of the process, tokens cannot be recomputed from a class roster and do not survive a restart. Free-text fields are then scrubbed of the student's name parts and of the same pattern classes as the browser layer (emails, phones, dates, ID-shaped strings, digit runs of 6+).

## Storage

- **Nothing is stored.** Identity mappings, if a session uses them, live only in process memory and are purged when the session is destroyed. The privacy audit log is an in-memory list (capped at 1,000 events) that records event types and redaction categories — not the redacted values. The server's privacy status endpoint reports `pii_on_disk: false` and `pii_in_logs: false`.

## Known limits (from the code and README)

- Pattern scrubbing **can miss identifiers**: a classmate's name typed into a note, a name the teacher never entered into the name field, or an ID in an unusual format will not necessarily be caught. The scrubber reduces risk; it does not eliminate it.
- The project **has not been independently audited**.
- The scrubbing does **not by itself make a deployment compliant** with FERPA, COPPA, or any other law. As the code's own documentation states, districts remain responsible for their own privacy review and data agreements.

## Open questions for the reviewer

1. In a district deployment, which components (browser, web app, MCP server, any connected language model) does submitted text transit, and are data-processing agreements needed for each?
2. What host-level logging (web server, reverse proxy, systemd journal) exists outside the application's own in-memory audit log, and what is its retention?
3. Who operates the hosting environment, and what access controls and authentication protect the workspace itself?
4. Should district guidance simply prohibit entering student names at all, treating the scrubber as a safety net rather than a control?
5. What breach/incident-notification terms would apply to the operator?

*This draft makes no claim of compliance with FERPA, COPPA, or Georgia student-data law. It is a description of current behavior to support the reviewer's own determination.*
