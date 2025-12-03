# rag/qa_service.py

from typing import List
import os

from rag.retriever_llama import LlamaQdrantRetriever
from gemini_client import ask_gemini


class QAService:
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "openedx_courses",
        top_k: int = 5,
        embedding_backend: str | None = None,  # "fastembed" / "huggingface" / None
    ):
        # main retriever
        self._retriever = LlamaQdrantRetriever(
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            collection_name=collection_name,
            default_top_k=top_k,
            embedding_backend=embedding_backend,
        )
        self._top_k = top_k

    def answer(self, question: str) -> str:

        docs = self._retriever.retrieve(question, top_k=self._top_k)

        if not docs:
            context_text = "No relevant documents were retrieved from the knowledge base."
        else:
            parts: List[str] = [d["text"] for d in docs]
            context_text = "\n\n---\n\n".join(parts)


        return ask_gemini(question, context_text)


if __name__ == "__main__":
    # Test
    print("Starting QAService test run...")
    print("-" * 60)

    backend = os.getenv("RAG_EMBEDDING_BACKEND", None)

    service = QAService(
        embedding_backend=backend  # None -> fastembed, "huggingface" -> huggingface
    )

    question = "What is the grading policy in this course?"
    print("QUESTION:", question)
    print("=" * 60)

    try:
        answer = service.answer(question)
        print("ANSWER:")
        print(answer)
    except Exception as e:
        print("Error while answering:", repr(e))
