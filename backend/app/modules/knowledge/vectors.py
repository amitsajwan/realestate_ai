"""Search over everything we have published: the vector store (Qdrant) and the embedder, behind three calls.

    await search("certificate pending, can I apply?", limit=6)  -> [Passage]   hybrid: meaning (dense) + exact words (BM25), RRF
    await upsert(chunks) / await delete(ids) / await stored()                  used by knowledge/index.py only

Off (search returns []) when QDRANT_URL or EMBEDDER_URL is not set, and on any error or timeout: the chat then answers from
site.ENTRIES and the page's facts as before, so retrieval can only add knowledge, never break a reply.
Talks to Qdrant's REST API with httpx (no client library). Collection `kb`: named vectors `dense` (384, cosine) and `bm25`
(sparse, IDF computed by Qdrant). Point ids are uuid5 of the chunk id; the payload keeps id, kind, title, text, url, area,
regno and hash (what index.py compares to skip unchanged chunks).
"""
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx

from . import sparse

log = logging.getLogger(__name__)

COLLECTION = "kb"
DIM = 384
SEARCH_TIMEOUT_S = 4.0
PREFETCH = 24
NS = uuid.UUID("6f1c2a52-5d4e-4c1b-9a7e-3b0f6c2d8e11")


@dataclass
class Passage:
    id: str
    kind: str      # site | area | topic | project | post
    title: str
    text: str
    url: str
    score: float


def _qdrant() -> str:
    return os.environ.get("QDRANT_URL", "").rstrip("/")


def _embedder() -> str:
    return os.environ.get("EMBEDDER_URL", "").rstrip("/")


def enabled() -> bool:
    return bool(_qdrant() and _embedder())


def point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(NS, chunk_id))


async def embed(texts: List[str], query: bool = False, timeout: float = 120.0) -> dict:
    """{"dense": meaning vectors from the embedder service, "sparse": BM25 word vectors (knowledge/sparse.py, computed here)}."""
    async with httpx.AsyncClient(timeout=timeout) as c:
        r = await c.post(f"{_embedder()}/embed", json={"texts": texts})
        r.raise_for_status()
    make = sparse.query_vector if query else sparse.doc_vector
    return {"dense": r.json()["dense"], "sparse": [make(t) for t in texts]}


async def ensure_collection() -> None:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{_qdrant()}/collections/{COLLECTION}")
        if r.status_code == 200:
            return
        body = {"vectors": {"dense": {"size": DIM, "distance": "Cosine", "on_disk": True}},
                "sparse_vectors": {"bm25": {"modifier": "idf"}}, "on_disk_payload": True}
        (await c.put(f"{_qdrant()}/collections/{COLLECTION}", json=body)).raise_for_status()
        for field in ("kind", "area", "regno"):
            await c.put(f"{_qdrant()}/collections/{COLLECTION}/index", json={"field_name": field, "field_schema": "keyword"})


async def stored() -> Dict[str, str]:
    """Chunk id -> hash of every point in the collection."""
    out: Dict[str, str] = {}
    offset = None
    async with httpx.AsyncClient(timeout=60) as c:
        while True:
            body = {"limit": 1000, "with_payload": ["id", "hash"], "with_vector": False}
            if offset is not None:
                body["offset"] = offset
            r = await c.post(f"{_qdrant()}/collections/{COLLECTION}/points/scroll", json=body)
            r.raise_for_status()
            res = r.json()["result"]
            for p in res["points"]:
                pl = p.get("payload") or {}
                if pl.get("id"):
                    out[pl["id"]] = pl.get("hash", "")
            offset = res.get("next_page_offset")
            if offset is None:
                return out


async def upsert(chunks: List[dict]) -> None:
    """chunks: {id, kind, title, text, url, area, regno, hash}; embeds 'title. text' and writes the points."""
    vec = await embed([f"{ch['title']}. {ch['text']}" for ch in chunks])
    points = [{"id": point_id(ch["id"]), "vector": {"dense": d, "bm25": s}, "payload": ch}
              for ch, d, s in zip(chunks, vec["dense"], vec["sparse"])]
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.put(f"{_qdrant()}/collections/{COLLECTION}/points?wait=true", json={"points": points})
        r.raise_for_status()


async def delete(ids: List[str]) -> None:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{_qdrant()}/collections/{COLLECTION}/points/delete?wait=true",
                         json={"points": [point_id(i) for i in ids]})
        r.raise_for_status()


async def search(question: str, limit: int = 6, kinds: Optional[List[str]] = None) -> List[Passage]:
    """The passages that best answer the question (hybrid, reciprocal-rank fusion); [] when off or on any failure."""
    q = " ".join((question or "").split())[:500]
    if not q or not enabled():
        return []
    try:
        vec = await embed([q], query=True, timeout=SEARCH_TIMEOUT_S)
        flt = {"must": [{"key": "kind", "match": {"any": kinds}}]} if kinds else None
        prefetch = [{"query": vec["dense"][0], "using": "dense", "limit": PREFETCH}]
        if vec["sparse"][0]["indices"]:   # a question of filler words only has no BM25 half
            prefetch.append({"query": vec["sparse"][0], "using": "bm25", "limit": PREFETCH})
        if flt:
            for p in prefetch:
                p["filter"] = flt
        async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT_S) as c:
            r = await c.post(f"{_qdrant()}/collections/{COLLECTION}/points/query",
                             json={"prefetch": prefetch, "query": {"fusion": "rrf"}, "limit": limit, "with_payload": True})
            r.raise_for_status()
        out = []
        for p in r.json()["result"]["points"]:
            pl = p.get("payload") or {}
            out.append(Passage(pl.get("id", ""), pl.get("kind", ""), pl.get("title", ""), pl.get("text", ""), pl.get("url", ""),
                               float(p.get("score") or 0)))
        return out
    except Exception as e:
        log.warning("knowledge search failed (%s: %s); answering without it", type(e).__name__, str(e)[:120])
        return []
