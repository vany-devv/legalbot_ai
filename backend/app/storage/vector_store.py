import json
import pathlib
import typing as t
import uuid
import re

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    _HAS_ST = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SK = True
except Exception:
    _HAS_SK = False


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_long_text(text: str, max_len: int) -> t.List[str]:
    parts: t.List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + max_len)
        if end < length:
            cut = text.rfind(" ", start, end)
            if cut <= start:
                cut = text.find(" ", end)
            if cut == -1:
                cut = end
            end = cut
        chunk = text[start:end].strip()
        if chunk:
            parts.append(chunk)
        start = max(end, start + 1)
    return parts


def simple_chunk(text: str, max_len: int = 1200) -> t.List[str]:
    if not text:
        return []
    normalized = text.replace("\r\n", "\n")
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", normalized) if p.strip()]
    chunks: t.List[str] = []
    current_sentences: t.List[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current_sentences, current_len
        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if chunk_text:
                if len(chunk_text) <= max_len:
                    chunks.append(chunk_text)
                else:
                    chunks.extend(_split_long_text(chunk_text, max_len))
        current_sentences = []
        current_len = 0

    for paragraph in paragraphs:
        sentences = _SENTENCE_SPLIT_RE.split(paragraph.strip())
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sentence_len = len(sentence)
            if current_len + sentence_len + 1 > max_len and current_sentences:
                flush()
            current_sentences.append(sentence)
            current_len += sentence_len + 1
        flush()

    if chunks:
        return chunks
    fallback_text = " ".join(paragraphs).strip()
    return _split_long_text(fallback_text or normalized.strip(), max_len)


class VectorStore:
    def __init__(self, store_path: pathlib.Path, emb_path: pathlib.Path) -> None:
        self.texts: t.List[str] = []
        self.metadatas: t.List[dict] = []
        self.ids: t.List[str] = []
        self.doc_ids: t.List[str] = []
        self.embeddings: t.Optional[np.ndarray] = None
        self._embedder: t.Optional["SentenceTransformer"] = None
        self._tfidf: t.Optional["TfidfVectorizer"] = None
        self.store_path = store_path
        self.emb_path = emb_path

    def _ensure_embedder(self) -> None:
        if _HAS_ST and self._embedder is None:
            self._embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def _embed(self, texts: t.List[str]) -> np.ndarray:
        if _HAS_ST:
            self._ensure_embedder()
            assert self._embedder is not None
            vecs = self._embedder.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return vecs.astype(np.float32)
        if _HAS_SK:
            if self._tfidf is None:
                self._tfidf = TfidfVectorizer(max_features=4096)
                X = self._tfidf.fit_transform(texts)
            else:
                all_texts = self.texts + texts
                self._tfidf = TfidfVectorizer(max_features=4096)
                X = self._tfidf.fit_transform(all_texts)
                self.embeddings = X[: len(self.texts)].toarray().astype(np.float32)
                return X[len(self.texts) :].toarray().astype(np.float32)
            return X.toarray().astype(np.float32)
        def hash_embed(s: str, dim: int = 384) -> np.ndarray:
            vec = np.zeros(dim, dtype=np.float32)
            if not s:
                return vec
            for tok in s.split():
                h = abs(hash(tok)) % dim
                vec[h] += 1.0
            n = np.linalg.norm(vec) + 1e-8
            return (vec / n).astype(np.float32)
        return np.vstack([hash_embed(t) for t in texts])

    def add_documents(self, docs: t.List[t.Any]) -> int:
        chunk_texts: t.List[str] = []
        chunk_metas: t.List[dict] = []
        chunk_ids: t.List[str] = []
        doc_ids: t.List[str] = []
        for d in docs:
            if isinstance(d, dict):
                base_id = str(d.get("id") or uuid.uuid4())
                text = str(d.get("text") or "")
                meta = dict(d.get("meta") or {})
            else:
                base_id = str(getattr(d, "id", None) or uuid.uuid4())
                text = str(getattr(d, "text", "") or "")
                meta = dict(getattr(d, "meta", {}) or {})
            for idx, ch in enumerate(simple_chunk(text)):
                chunk_texts.append(ch)
                m = dict(meta)
                m.update({"source_id": base_id, "chunk_index": idx})
                chunk_metas.append(m)
                chunk_ids.append(f"{base_id}#{idx}")
                doc_ids.append(base_id)

        new_emb = self._embed(chunk_texts)
        if self.embeddings is None:
            self.embeddings = new_emb
        else:
            self.embeddings = np.vstack([self.embeddings, new_emb])
        self.texts.extend(chunk_texts)
        self.metadatas.extend(chunk_metas)
        self.ids.extend(chunk_ids)
        self.doc_ids.extend(doc_ids)
        return len(chunk_ids)

    def search(self, query: str, top_k: int = 5) -> t.List[dict]:
        if not self.texts or self.embeddings is None:
            return []
        q = self._embed([query])
        if _HAS_ST or (_HAS_SK and isinstance(self.embeddings, np.ndarray)):
            sims = (q @ self.embeddings.T).reshape(-1) if (_HAS_ST and q.shape[1] == self.embeddings.shape[1]) else cosine_similarity(q, self.embeddings)[0]
        else:
            def cos(a: np.ndarray, b: np.ndarray) -> float:
                return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))
            sims = np.array([cos(q[0], v) for v in self.embeddings], dtype=np.float32)
        order = np.argsort(-sims)[:top_k]
        results: t.List[dict] = []
        for i in order:
            results.append({
                "doc_id": self.metadatas[i].get("source_id", self.doc_ids[i]),
                "chunk_id": self.ids[i],
                "score": float(sims[i]),
                "text": self.texts[i],
                "meta": self.metadatas[i],
            })
        return results

    def save(self) -> None:
        payload = {
            "texts": self.texts,
            "metadatas": self.metadatas,
            "ids": self.ids,
            "doc_ids": self.doc_ids,
        }
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        if self.embeddings is not None:
            np.save(self.emb_path, self.embeddings)

    def load(self) -> None:
        if self.store_path.exists() and self.emb_path.exists():
            with open(self.store_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.texts = payload.get("texts", [])
            self.metadatas = payload.get("metadatas", [])
            self.ids = payload.get("ids", [])
            self.doc_ids = payload.get("doc_ids", [])
            self.embeddings = np.load(self.emb_path)


