"""
Backend layer connecting Streamlit UI to the RAG pipeline.
Uses QAService to retrieve context from Qdrant and generate answers with Gemini.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# add project root to path so we can import from rag/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from rag.qa_service import QAService

# initialize the service once (connects to Qdrant)
_service = None

def get_service():
    global _service
    if _service is None:
        _service = QAService()
    return _service


def query_rag_backend(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Query the RAG pipeline and return the answer from Gemini.
    """
    try:
        service = get_service()
        answer = service.answer(query)

        return [{
            "score": 1.0,
            "text": answer,
            "metadata": {"source": "gemini", "model": "gemini-2.5-flash"}
        }]
    except Exception as e:
        return [{
            "score": 0.0,
            "text": f"Error: {str(e)}",
            "metadata": {"error": True}
        }]
