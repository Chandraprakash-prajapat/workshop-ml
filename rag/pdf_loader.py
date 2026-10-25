import os
import sys
import pdfplumber
from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)


def load_documents(source_dir: str):    # open every pdf and extract text
    try:
        documents = []
        for filename in sorted(os.listdir(source_dir)):
            if filename.endswith(".pdf"):
                filepath = os.path.join(source_dir, filename)
                pages = []
                with pdfplumber.open(filepath) as pdf:
                    for page_no, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text() or ""
                        logger.info(f"{filename} | page {page_no}: {len(text)} characters, "
                                    f"{len(page.find_tables())} table(s), {len(page.images)} image(s)")
                        pages.append(text)
                documents.append({"source": filename, "text": "\n".join(pages)})
        logger.info(f"Loaded {len(documents)} documents from {source_dir}")
        return documents
    except Exception as e:
        raise CustomException(e, sys)


def chunk_text(text: str, chunk_size: int, chunk_overlap: int):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += ('\n' if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            overlap_text = current_chunk[-chunk_overlap:] if current_chunk else ""
            current_chunk = (overlap_text + "\n" + para).strip()

    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def build_chunks(source_dir: str, chunk_size: int, chunk_overlap: int):
    try:
        documents = load_documents(source_dir)
        all_chunks = []
        for doc in documents:
            doc_chunks = chunk_text(doc['text'], chunk_size, chunk_overlap)
            for i, chunk in enumerate(doc_chunks):
                all_chunks.append({
                    "source": doc['source'],
                    "chunk_id": i,
                    "text": chunk
                })

        logger.info(f"Built {len(all_chunks)} chunks from {len(documents)} documents.")
        return all_chunks

    except Exception as e:
        raise CustomException(e, sys)

