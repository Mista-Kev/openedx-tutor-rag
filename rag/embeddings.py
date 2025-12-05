# rag/embeddings.py

import os
from typing import Literal

from llama_index.embeddings.huggingface import HuggingFaceEmbedding


EmbeddingBackend = Literal["fastembed", "huggingface"]


def get_embedding_model(
    backend: EmbeddingBackend | None = None,
):
    """
    Returns a LlamaIndex embedding model instance.

    backend:
      - "fastembed"    -> FastEmbedEmbedding
      - "huggingface"  -> HuggingFaceEmbedding (fallback / dev)

    If backend is None, takes from env var RAG_EMBEDDING_BACKEND, default "fastembed".
    """

    if backend is None:
        backend = os.getenv("RAG_EMBEDDING_BACKEND", "fastembed")  # type: ignore[assignment]

    if backend == "fastembed":
        try:
            from llama_index.embeddings.fastembed import FastEmbedEmbedding
        except ImportError as e:

            raise RuntimeError(
                "FastEmbed backend selected, but fastembed / "
                "llama-index-embeddings-fastembed are not installed or not compatible."
            ) from e

        return FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

    elif backend == "huggingface":
        return HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

    else:
        raise ValueError(f"Unknown embedding backend: {backend}")
