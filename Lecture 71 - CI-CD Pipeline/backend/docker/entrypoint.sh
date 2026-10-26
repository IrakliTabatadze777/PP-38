#!/bin/sh
set -e

echo "Applying migrations..."
alembic upgrade head

echo "Seeding mock data if the database is empty..."
python scripts/seed.py --if-empty

if [ -n "$GEMINI_API_KEY" ]; then
    echo "Ingesting the knowledge base..."
    python scripts/ingest.py
else
    echo "GEMINI_API_KEY is not set: skipping ingestion, and the assistant will be disabled."
fi

exec "$@"
