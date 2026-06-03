from pathlib import Path
import re
import hashlib

from pypdf import PdfReader
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


PDF_PATH = "offer_letter/Amey Resume.pdf"

DB_PATH = "./chroma_db"
COLLECTION_NAME = "test_data"
MODEL_NAME = "all-mpnet-base-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

REPLACE_EXISTING_SOURCE = True


def fix_spaced_characters(text):
    """
    Fixes PDF text extraction like:

    P R O J E C T S  -> PROJECTS
    H T M L , C S S , J S -> HTML, CSS, JS
    T e c h : -> Tech:

    This usually happens in resumes created using Canva, Figma,
    resume builders, or design-heavy PDF templates.
    """
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

        # If most tokens are single characters, the line is probably wrongly spaced.
        if len(tokens) >= 4 and len(one_char_tokens) / len(tokens) >= 0.65:
            fixed_line = "".join(tokens)

            # Make comma-separated tech lists more readable:
            # HTML,CSS,JS -> HTML, CSS, JS
            fixed_line = fixed_line.replace(",", ", ")

            # Remove extra spaces accidentally created
            fixed_line = re.sub(r"\s+", " ", fixed_line)

            fixed_lines.append(fixed_line.strip())
        else:
            fixed_lines.append(stripped)

    return "\n".join(fixed_lines)


def clean_text(text):
    """
    Basic PDF text cleaning before chunking.
    """
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Fix broken hyphenated words:
    # develop-\nment -> development
    text = re.sub(r"-\n(?=\w)", "", text)

    # Normalize spaces but keep line breaks
    text = re.sub(r"[ \t]+", " ", text)

    # Remove too many blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix P R O J E C T S style extraction
    text = fix_spaced_characters(text)

    return text.strip()


def chunk_text(text, chunk_size=500, chunk_overlap=100):
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

        # Try to end chunk at a better boundary
        boundary_candidates = [
            text.rfind("\n", start, target_end),
            text.rfind(". ", start, target_end),
            text.rfind("; ", start, target_end),
            text.rfind(" ", start, target_end),
        ]

        boundary = max(boundary_candidates)

        # If no good boundary found, use hard cut
        if boundary <= start:
            boundary = target_end

        chunk = text[start:boundary].strip()

        if chunk:
            chunks.append(chunk)

        # Move forward with overlap
        start = max(boundary - chunk_overlap, start + 1)

    return chunks


def make_safe_id(source_name, page_number, chunk_index, chunk_text):
    """
    Creates unique chunk IDs.

    Example:
    amey_resume_p1_c0_a1b2c3d4
    """
    source_stem = Path(source_name).stem.lower()
    source_stem = re.sub(r"[^a-z0-9]+", "_", source_stem).strip("_")

    chunk_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()[:10]

    return f"{source_stem}_p{page_number}_c{chunk_index}_{chunk_hash}"


pdf_path = Path(PDF_PATH)
source_name = pdf_path.name

reader = PdfReader(str(pdf_path))

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
                chunk_text=chunk
            )
        )

        global_chunk_index += 1


if not all_chunks:
    raise ValueError(
        "No text was extracted from this PDF. "
        "It may be scanned/image-based or protected."
    )


print("PDF source:", source_name)
print("Chunks created:", len(all_chunks))

print("\nFirst chunk preview:")
print(all_chunks[0][:1000])

print("\nFirst chunk metadata:")
print(metadatas[0])


# Creating Chroma client
client = chromadb.PersistentClient(
    path=DB_PATH
)


# Model selection for embeddings of chunks
sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME,
    device="cpu",
    normalize_embeddings=True
)


collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=sentence_transformer_ef
)


# Delete old chunks from the same PDF before adding again.
# This prevents duplicate / outdated chunks when you rerun build_rag.py.
if REPLACE_EXISTING_SOURCE:
    existing = collection.get(
        where={
            "source": source_name
        },
        include=["metadatas"]
    )

    if existing["ids"]:
        collection.delete(
            ids=existing["ids"]
        )

        print("\nDeleted old chunks for source:", source_name)


collection.add(
    documents=all_chunks,
    metadatas=metadatas,
    ids=ids
)


print("\nPDF added successfully.")
print("Source:", source_name)
print("Chunks inserted:", len(all_chunks))
print("Total chunks in DB:", collection.count())