from typing import List, Optional, Dict, Any
from ..core.types import RetrievalResult, Passage

try:
    from langchain_community.vectorstores import FAISS, Chroma
    from langchain_openai import OpenAIEmbeddings  # type: ignore
    from langchain_google_genai import GoogleGenerativeAIEmbeddings  # type: ignore
    from langchain_community.embeddings import FakeEmbeddings
except Exception:  # pragma: no cover
    FAISS = None  # type: ignore
    Chroma = None  # type: ignore
    OpenAIEmbeddings = None  # type: ignore
    GoogleGenerativeAIEmbeddings = None  # type: ignore
    FakeEmbeddings = None  # type: ignore


class RetrieverAgent:
    def __init__(
        self,
        vector_store: str = "faiss",
        persist_dir: Optional[str] = None,
        embedding_model: str = "auto",
    ) -> None:
        self.vector_store_type = vector_store.lower()
        self.persist_dir = persist_dir
        self.embedding_model = embedding_model
        self._vs = None
        self._emb = self._init_embeddings(embedding_model)

    def _init_embeddings(self, embedding_model: str):
        if embedding_model in ("gemini", "google", "auto") and GoogleGenerativeAIEmbeddings is not None:
            try:
                return GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            except Exception:
                pass
        if embedding_model in ("openai", "auto") and OpenAIEmbeddings is not None:
            try:
                return OpenAIEmbeddings()
            except Exception:
                pass
        # Fallback to deterministic fake embeddings (no network/API)
        if FakeEmbeddings is not None:
            return FakeEmbeddings(size=384)
        raise RuntimeError("No embeddings backend available. Install langchain-community and embeddings.")

    def index_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> None:
        if self.vector_store_type == "faiss":
            if FAISS is None:
                raise RuntimeError("FAISS not available. Ensure langchain-community and faiss-cpu are installed.")
            self._vs = FAISS.from_texts(texts=texts, embedding=self._emb, metadatas=metadatas)
        elif self.vector_store_type == "chroma":
            if Chroma is None:
                raise RuntimeError("Chroma not available. Ensure chromadb is installed.")
            self._vs = Chroma.from_texts(
                texts=texts,
                embedding=self._emb,
                metadatas=metadatas,
                persist_directory=self.persist_dir,
            )
            # Persist after initial build
            try:
                self._vs.persist()  # type: ignore
            except Exception:
                pass
        else:
            raise ValueError(f"Unsupported vector_store: {self.vector_store_type}")

    def retrieve(self, query: str, top_k: int = 5) -> RetrievalResult:
        if self._vs is None:
            # Empty index; return no passages instead of raising
            return RetrievalResult(query=query, passages=[])
        docs = self._vs.similarity_search(query, k=top_k)
        passages: List[Passage] = []
        for idx, d in enumerate(docs):
            pid = str(d.metadata.get("id", idx)) if hasattr(d, "metadata") else str(idx)
            passages.append(Passage(id=pid, text=d.page_content, metadata=getattr(d, "metadata", {}) or {}))
        return RetrievalResult(query=query, passages=passages)
