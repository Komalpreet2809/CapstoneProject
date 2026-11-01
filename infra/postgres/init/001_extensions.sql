-- Runs once, when the Postgres volume is first created.
-- pgvector stores rulebook embeddings next to the Mini UMS data (decision D-008).
CREATE EXTENSION IF NOT EXISTS vector;
