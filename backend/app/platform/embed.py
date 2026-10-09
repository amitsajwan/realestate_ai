"""Multilingual sentence embeddings, in process, on CPU (docs/RADAR.md §5 L2). The model is multilingual-e5-small (ONNX, quantized,
~120 MB, MIT): English, Hindi, Marathi and Hinglish land near each other when they mean the same thing. Downloaded once from
Hugging Face into <uploads>/models/ (or EMBED_MODEL_DIR). Without onnxruntime/tokenizers or the download, a character n-gram hash
embedder is used instead: weaker on meaning, but it still catches spelling variants ("2bhk"/"2 bhk"/"kitna") and never fails.

Vectors are L2-normalised float32, so cosine similarity is a dot product. Each vector is stored with `model_name()`; vectors from
different embedders are never compared."""
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

log = logging.getLogger(__name__)

REPO = "https://huggingface.co/Xenova/multilingual-e5-small/resolve/main"
FILES = {"model.onnx": f"{REPO}/onnx/model_quantized.onnx", "tokenizer.json": f"{REPO}/tokenizer.json"}
E5 = "e5-small-v1"
HASH = "hash3-5-v1"
DIM = 384
MAX_TOKENS = 128

_session = None
_tokenizer = None
_tried = False


def _dir() -> Path:
    env = os.environ.get("EMBED_MODEL_DIR")
    return Path(env) if env else Path(os.environ.get("UPLOAD_DIRECTORY", "uploads")) / "models" / "multilingual-e5-small"


def _download(url: str, p: Path) -> None:
    import httpx
    p.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, follow_redirects=True, timeout=300) as r:
        r.raise_for_status()
        tmp = p.with_suffix(p.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
        tmp.replace(p)


def _load() -> bool:
    global _session, _tokenizer, _tried
    if _session is not None:
        return True
    if _tried or (os.environ.get("EMBED_BACKEND") or "").lower() == "hash":
        return False
    _tried = True
    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer
        d = _dir()
        for name, url in FILES.items():
            if not (d / name).is_file():
                _download(url, d / name)
        tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        tok.enable_truncation(MAX_TOKENS)
        tok.enable_padding()
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = max(1, min(4, os.cpu_count() or 1))
        _session = ort.InferenceSession(str(d / "model.onnx"), opts, providers=["CPUExecutionProvider"])
        _tokenizer = tok
        log.info("embed: multilingual-e5-small loaded")
        return True
    except Exception as e:  # any problem: the hash embedder
        log.warning("embed: e5 model unavailable (%s: %s); using the n-gram hash embedder", type(e).__name__, str(e)[:120])
        _session = _tokenizer = None
        return False


def model_name() -> str:
    return E5 if _load() else HASH


def _norm(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return (v / np.maximum(n, 1e-9)).astype(np.float32)


def _e5(texts: Sequence[str]) -> np.ndarray:
    out = []
    names = {i.name for i in _session.get_inputs()}
    for start in range(0, len(texts), 32):
        enc = _tokenizer.encode_batch([f"query: {t}" for t in texts[start:start + 32]])
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        feed = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in names:
            feed["token_type_ids"] = np.zeros_like(ids)
        hidden = _session.run(None, feed)[0]                       # (batch, tokens, 384)
        m = mask[..., None].astype(np.float32)
        out.append((hidden * m).sum(1) / np.maximum(m.sum(1), 1e-9))  # mean pooling, as e5 was trained
    return _norm(np.concatenate(out))


WORD = re.compile(r"\w+", re.U)


def _hash(texts: Sequence[str]) -> np.ndarray:
    v = np.zeros((len(texts), DIM), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in WORD.findall((t or "").lower()):
            w = f"<{w}>"
            for n in (3, 4, 5):
                for j in range(max(1, len(w) - n + 1)):
                    h = int.from_bytes(hashlib.blake2b(w[j:j + n].encode(), digest_size=4).digest(), "little")
                    v[i, h % DIM] += 1.0 if h & 1 << 31 else -1.0
    return _norm(v)


def embed(texts: Sequence[str]) -> np.ndarray:
    """(len(texts), 384) float32, rows L2-normalised. Empty input -> (0, 384)."""
    texts = [(t or "")[:1000] for t in texts]
    if not texts:
        return np.zeros((0, DIM), dtype=np.float32)
    if _load():
        try:
            return _e5(texts)
        except Exception:
            log.exception("embed: e5 inference failed; hash embedder for this batch")
    return _hash(texts)


def embed_one(text: str) -> List[float]:
    return embed([text])[0].tolist()


def cosine(q: np.ndarray, bank: np.ndarray) -> np.ndarray:
    """Similarity of one normalised vector to each row of a normalised bank."""
    return bank @ q if len(bank) else np.zeros(0, dtype=np.float32)


def as_matrix(rows: List[List[float]]) -> Optional[np.ndarray]:
    return np.asarray(rows, dtype=np.float32) if rows else None
