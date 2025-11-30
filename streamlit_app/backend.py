"""
Thin abstraction layer between the Streamlit UI and the RAG backend (returning dummy data for now)
"""

from typing import List, Dict, Any


def query_rag_backend(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    # to replace with real logic
    return [
        {
            "score": 0.9,
            "text": f"[RAG placeholder] Best match for: {query}",
            "metadata": {"source": "dummy", "chunk": 1},
        },
        {
            "score": 0.8,
            "text": f"[RAG placeholder] Second match for: {query}",
            "metadata": {"source": "dummy", "chunk": 2},
        },
    ][:top_k]