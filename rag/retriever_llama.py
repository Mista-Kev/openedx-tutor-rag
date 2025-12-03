# rag/retriever_llama.py

from typing import List, Dict

from qdrant_client import QdrantClient
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore

from rag.embeddings import get_embedding_model


class LlamaQdrantRetriever:
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "openedx_courses",
        default_top_k: int = 5,
        embedding_backend: str | None = None,  # "fastembed" / "huggingface"
    ):
        self._client = QdrantClient(host=qdrant_host, port=qdrant_port)

        self._vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=collection_name,
        )

        self._storage_context = StorageContext.from_defaults(
            vector_store=self._vector_store
        )

        # embedding model
        self._embed_model = get_embedding_model(backend=embedding_backend)

        self._index = VectorStoreIndex.from_vector_store(
            vector_store=self._vector_store,
            storage_context=self._storage_context,
            embed_model=self._embed_model,
        )

        self._retriever = self._index.as_retriever(
            similarity_top_k=default_top_k
        )

    def retrieve(self, question: str, top_k: int = 5) -> List[Dict]:
        self._retriever.similarity_top_k = top_k
        nodes_with_scores = self._retriever.retrieve(question)

        results: List[Dict] = []
        for nws in nodes_with_scores:
            node = nws.node
            results.append(
                {
                    "text": node.get_content(),
                    "metadata": node.metadata or {},
                    "score": nws.score,
                }
            )
        return results
