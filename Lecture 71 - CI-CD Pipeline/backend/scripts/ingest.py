import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import settings
from app.rag.embeddings import EmbeddingsNotConfigured, make_embeddings
from app.rag.ingest import ingest_directory
from app.rag.store import KnowledgeBase

DEFAULT_DIRECTORY = Path(__file__).resolve().parent.parent / "data" / "kb"


async def main(directory: Path) -> None:
    try:
        embeddings = make_embeddings(settings)
    except EmbeddingsNotConfigured as exc:
        sys.exit(f"Cannot ingest: {exc}")
    kb = KnowledgeBase(embeddings, settings.database_url)
    try:
        counts = await ingest_directory(kb, directory)
    finally:
        await kb.aclose()
    for source, chunks in counts.items():
        print(f"{source}: {chunks} chunks")
    print(f"Ingested {len(counts)} documents, {sum(counts.values())} chunks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=DEFAULT_DIRECTORY)
    asyncio.run(main(parser.parse_args().directory))
