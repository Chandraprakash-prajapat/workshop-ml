import sys

import yaml

from rag.pdf_loader import build_chunks
from rag.vector_store import VectorStore
from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)

PDF_CONFIG_PATH = "rag/config/pdf_rag_config.yaml"


def load_pdf_config(path=PDF_CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    try:
        config = load_pdf_config()
        kb = config["knowledge_base"]
        logger.info("PDF RAG: index building starting..")
        chunks = build_chunks(kb["source_dir"], kb["chunk_size"], kb["chunk_overlap"])   # PDF -> chunks
        VectorStore(config).build(chunks)                                                 # chunks -> embeddings -> FAISS
        logger.info("PDF RAG: index building completed")
    except Exception as e:
        raise CustomException(e, sys)


if __name__ == "__main__":
    main()