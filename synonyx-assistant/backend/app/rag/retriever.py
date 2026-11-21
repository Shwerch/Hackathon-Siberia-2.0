import re
from pathlib import Path
from rank_bm25 import BM25Okapi
from app.rag.indexer import KBChunk, load_kb_chunks


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[а-яёa-z0-9]+", text.lower())


class KBRetriever:
    def __init__(self, kb_dir: Path) -> None:
        self.chunks: list[KBChunk] = load_kb_chunks(kb_dir)
        tokenized = [_tokenize(f"{c.section} {c.text}") for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized) if tokenized else None

    def search(self, query: str, top_k: int = 4) -> list[KBChunk]:
        if not self.bm25 or not self.chunks:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return self.chunks[:top_k]
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.chunks[i] for i in ranked[:top_k] if scores[i] > 0]
