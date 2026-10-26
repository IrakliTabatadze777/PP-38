import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.rag.store import KnowledgeBase

CHUNK_SIZE = 700
CHUNK_OVERLAP = 80
REQUIRED_FRONT_MATTER = ("title", "category", "last_updated")
SOURCE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\.(md|txt)")

_FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]


class InvalidDocument(ValueError): ...


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: dict[str, Any]


def chunk_id(source: str, index: int) -> str:
    return hashlib.sha1(f"{source}:{index}".encode()).hexdigest()


def validate_source_name(source: str) -> None:
    if not SOURCE_NAME.fullmatch(source):
        raise InvalidDocument("File name must be a plain .md or .txt name (letters, digits, _ - .)")


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = _FRONT_MATTER.match(text)
    if not match:
        raise InvalidDocument("Missing front matter (title, category, last_updated)")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise InvalidDocument("Front matter is not valid YAML") from exc
    if not isinstance(data, dict):
        raise InvalidDocument("Front matter must be a list of key: value lines")
    missing = [key for key in REQUIRED_FRONT_MATTER if not data.get(key)]
    if missing:
        raise InvalidDocument(f"Front matter is missing: {', '.join(missing)}")
    return {key: str(data[key]) for key in REQUIRED_FRONT_MATTER}, text[match.end() :]


def chunk_document(source: str, text: str) -> list[Chunk]:
    validate_source_name(source)
    front, body = parse_front_matter(text)
    sections = MarkdownHeaderTextSplitter(_HEADERS, strip_headers=True).split_text(body)
    pieces = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    ).split_documents(sections)

    chunks: list[Chunk] = []
    for piece in pieces:
        section = piece.metadata.get("h3") or piece.metadata.get("h2") or front["title"]
        chunks.append(
            Chunk(
                id=chunk_id(source, len(chunks)),
                text=f"{section}\n{piece.page_content}",
                metadata={
                    "source": source,
                    "section": section,
                    "category": front["category"],
                    "last_updated": front["last_updated"],
                },
            )
        )
    if not chunks:
        raise InvalidDocument("The document has no content")
    return chunks


async def ingest_document(kb: KnowledgeBase, source: str, text: str) -> int:
    chunks = chunk_document(source, text)
    await kb.replace_source(
        source,
        [Document(page_content=c.text, metadata=c.metadata) for c in chunks],
        [c.id for c in chunks],
    )
    return len(chunks)


def read_documents(directory: Path) -> dict[str, str]:
    return {
        path.name: path.read_text("utf-8")
        for path in sorted(directory.iterdir())
        if path.suffix in {".md", ".txt"}
    }


async def ingest_directory(kb: KnowledgeBase, directory: Path) -> dict[str, int]:
    return {
        source: await ingest_document(kb, source, text)
        for source, text in read_documents(directory).items()
    }
