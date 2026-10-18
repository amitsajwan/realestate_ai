"""The embedder: one small service that turns text into meaning vectors, so the model is held in memory once (the VM has ~1.7 GB
free and three Python containers that search).

    uvicorn app.modules.knowledge.embedder:app --port 8090      (compose service `embedder`, internal network only)
    POST /embed {"texts": [...], "query": false}  ->  {"dense": [[384 floats], ...]}
    GET  /health

Model: paraphrase-multilingual-MiniLM-L12-v2 (Apache-2.0), Qdrant's quantized ONNX build, run with onnxruntime + tokenizers (both
already in the image for the radar's e5-small; no torch, no new package). English, Hindi, Marathi and Hinglish questions land near
passages that mean the same. On our own questions (2026-10-18, 14 buyer questions in three languages, with BM25 alongside) it found
the right passage in the top 8 for 13; e5-small 11, the larger mpnet 13 at 1.4 GB. Downloaded once into EMBEDDER_MODEL_DIR (a volume).
The exact-word half of the search (BM25) needs no model: knowledge/sparse.py, computed by the caller.
"""
import asyncio
import os
from pathlib import Path
from typing import List

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

REPO = "https://huggingface.co/Qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q/resolve/main"
FILES = {"model.onnx": f"{REPO}/model_optimized.onnx", "tokenizer.json": f"{REPO}/tokenizer.json"}
NAME = "paraphrase-multilingual-MiniLM-L12-v2-q"
MAX_TOKENS = 128
MAX_TEXTS = 128
BATCH = 16

app = FastAPI(title="embedder")
_m: dict = {}
_lock = asyncio.Lock()   # index batches one at a time; a question ({"query": true}) never waits behind them


class Req(BaseModel):
    texts: List[str]
    query: bool = False


def _dir() -> Path:
    return Path(os.environ.get("EMBEDDER_MODEL_DIR") or Path(os.environ.get("UPLOAD_DIRECTORY", "uploads")) / "models" / NAME)


def _load() -> dict:
    if _m:
        return _m
    import onnxruntime as ort
    from tokenizers import Tokenizer

    from app.platform.embed import _download
    d = _dir()
    for name, url in FILES.items():
        if not (d / name).is_file():
            _download(url, d / name)
    tok = Tokenizer.from_file(str(d / "tokenizer.json"))
    tok.enable_truncation(MAX_TOKENS)
    tok.enable_padding()
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    opts.enable_cpu_mem_arena = False   # the arena kept ~400 MB after the first batch; the container has 1 GB
    _m["session"] = ort.InferenceSession(str(d / "model.onnx"), opts, providers=["CPUExecutionProvider"])
    _m["tok"] = tok
    _m["inputs"] = {i.name for i in _m["session"].get_inputs()}
    return _m


def embed_texts(texts: List[str]) -> np.ndarray:
    m = _load()
    out = []
    for start in range(0, len(texts), BATCH):
        enc = m["tok"].encode_batch([t or " " for t in texts[start:start + BATCH]])
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in m["inputs"]:
            feed["token_type_ids"] = np.zeros_like(ids)
        hidden = m["session"].run(None, feed)[0]
        w = mask[..., None].astype(np.float32)
        out.append((hidden * w).sum(1) / np.maximum(w.sum(1), 1e-9))   # mean pooling, as the model was trained
    v = np.concatenate(out)
    return (v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)).astype(np.float32)


@app.on_event("startup")
async def _warm() -> None:
    await asyncio.to_thread(_load)


@app.get("/health")
async def health() -> dict:
    return {"ok": bool(_m), "model": NAME}


@app.post("/embed")
async def embed(req: Req) -> dict:
    if not req.texts or len(req.texts) > MAX_TEXTS:
        raise HTTPException(400, f"1 to {MAX_TEXTS} texts")
    texts = [t[:2000] for t in req.texts]
    if req.query:   # a chat question: a few milliseconds, run beside an index batch (onnxruntime sessions are thread-safe)
        v = await asyncio.to_thread(embed_texts, texts)
    else:
        async with _lock:
            v = await asyncio.to_thread(embed_texts, texts)
    return {"dense": [[round(float(x), 6) for x in row] for row in v]}
