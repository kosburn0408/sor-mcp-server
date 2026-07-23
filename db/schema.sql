-- Science of Reading DuckDB Schema
-- Embedded analytical database for SoR MCP server

CREATE TABLE IF NOT EXISTS research_papers (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER NOT NULL,
    framework TEXT NOT NULL,  -- 'phonemic_awareness', 'phonics', 'fluency', 'vocabulary', 'comprehension', 'simple_view', 'rope'
    finding TEXT NOT NULL,
    effect_size FLOAT,
    source TEXT NOT NULL,  -- 'WWC', 'BEE', 'NRP', 'Other'
    url TEXT
);

CREATE TABLE IF NOT EXISTS vocabulary_corpus (
    word TEXT NOT NULL,
    grade INTEGER NOT NULL,  -- K=0, 1-12
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
    frequency INTEGER,
    decodable BOOLEAN NOT NULL DEFAULT FALSE,
    phoneme_pattern TEXT,
    PRIMARY KEY (word, grade)
);

CREATE TABLE IF NOT EXISTS standards (
    state TEXT NOT NULL,
    grade TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT 'ELA',
    code TEXT NOT NULL,
    description TEXT NOT NULL,
    framework TEXT NOT NULL,  -- pillar mapping
    PRIMARY KEY (state, grade, code)
);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'screener', 'diagnostic', 'progress_monitoring', 'outcome'
    grade_range TEXT,
    skills_assessed TEXT,  -- comma-separated pillars
    administration TEXT,
    scoring TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS theoretical_frameworks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    authors TEXT,
    year INTEGER,
    description TEXT NOT NULL,
    components TEXT,
    url TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_papers_framework ON research_papers(framework);
CREATE INDEX IF NOT EXISTS idx_papers_source ON research_papers(source);
CREATE INDEX IF NOT EXISTS idx_vocab_grade_tier ON vocabulary_corpus(grade, tier);
CREATE INDEX IF NOT EXISTS idx_vocab_decodable ON vocabulary_corpus(decodable, grade);
CREATE INDEX IF NOT EXISTS idx_standards_framework ON standards(framework);
CREATE INDEX IF NOT EXISTS idx_standards_state ON standards(state, grade);
CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(type);
