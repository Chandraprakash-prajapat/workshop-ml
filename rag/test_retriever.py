import sys

from rag.pdf_test import load_pdf_config
from rag.retriever import Retriever
from src.exception import CustomException
from src.logger import get_logger

logger = get_logger(__name__)

QUESTIONS = [
    "What are the gym opening hours?",
    "How much does the Premium plan cost?",
    "Can I freeze my membership?",
    "Who won the cricket world cup?",
    "How many visitors came in June?",
    "Which month had the highest visitors?",
]


def main():
    try:
        retriever = Retriever(load_pdf_config())
        for question in QUESTIONS:
            results = retriever.retrieve(question) or []
            logger.info(f"test_retriever | q={question!r} | chunks={len(results)}")
            print("\nQ:", question)
            if not results:
                print("   (Chunk not found )")
            for r in results:
                print(f"   [{r['score']}] chunk_id={r['chunk_id']} | {r['text'][:120].replace(chr(10), ' ')}")
    except Exception as e:
        raise CustomException(e, sys)


if __name__ == "__main__":
    main()