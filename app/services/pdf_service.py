from fastapi import UploadFile
from pypdf import PdfReader

from app.config import CHUNK_SIZE, CHUNK_OVERLAP

from pathlib import Path
import re
import hashlib
from typing import List

from pypdf import PdfReader

from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def fix_spaced_characters(text: str) -> str:
    fixed_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped:
            fixed_lines.append("")
            continue

        tokens = stripped.split()

        if not tokens:
            fixed_lines.append("")
            continue

        one_char_tokens = [
            token for token in tokens
            if len(token) == 1
        ]

        if len(tokens) >= 4 and len(one_char_tokens) / len(tokens) >= 0.65:
            fixed_line = "".join(tokens)
            fixed_line = fixed_line.replace(",", ", ")
            fixed_line = re.sub(r"\s+", " ", fixed_line)
            fixed_lines.append(fixed_line.strip())
        else:
            fixed_lines.append(stripped)

    return "\n".join(fixed_lines)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(r"-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    text = fix_spaced_characters(text)

    return text.strip()


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        target_end = start + chunk_size

        if target_end >= len(text):
            chunk = text[start:].strip()

            if chunk:
                chunks.append(chunk)

            break

        boundary_candidates = [
            text.rfind("\n", start, target_end),
            text.rfind(". ", start, target_end),
            text.rfind("; ", start, target_end),
            text.rfind(" ", start, target_end),
        ]

        boundary = max(boundary_candidates)

        if boundary <= start:
            boundary = target_end

        chunk = text[start:boundary].strip()

        if chunk:
            chunks.append(chunk)

        start = max(boundary - chunk_overlap, start + 1)

    return chunks


def make_safe_id(source_name: str, page_number: int, chunk_index: int, chunk_text_value: str) -> str:
    source_stem = Path(source_name).stem.lower()
    source_stem = re.sub(r"[^a-z0-9]+", "_", source_stem).strip("_")

    chunk_hash = hashlib.md5(
        chunk_text_value.encode("utf-8")
    ).hexdigest()[:10]

    return f"{source_stem}_p{page_number}_c{chunk_index}_{chunk_hash}"



def build_chunks_from_uploaded_pdf(file: UploadFile, source_name: str):
    file.file.seek(0)
    
    reader = PdfReader(file.file)

    all_chunks = []
    metadatas = []
    ids = []

    global_chunk_index = 0

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        page_text = clean_text(page_text)

        if not page_text:
            continue

        page_chunks = chunk_text(
            text=page_text,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        for page_chunk_index, chunk in enumerate(page_chunks):
            all_chunks.append(chunk)

            metadatas.append(
                {
                    "source": source_name,
                    "page_number": page_number,
                    "chunk_index": page_chunk_index,
                    "chunk_size": CHUNK_SIZE,
                    "chunk_overlap": CHUNK_OVERLAP
                }
            )

            ids.append(
                make_safe_id(
                    source_name=source_name,
                    page_number=page_number,
                    chunk_index=global_chunk_index,
                    chunk_text_value=chunk
                )
            )

            global_chunk_index += 1

    if not all_chunks:
        raise ValueError(
            "No text was extracted from this PDF. It may be scanned/image-based or protected."
        )

    return all_chunks, metadatas, ids