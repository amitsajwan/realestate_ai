"""The learning loop (docs/RADAR.md §7): every operator label makes the radar better, with no fine-tuning.
  - on_label: the comment joins the example bank (L2 gate and few-shots), and an edited reply is kept for draft rules.
  - refit (weekly): logistic regression over the stored features, with an L2 pull towards the current weights (a Gaussian prior),
    so 60 labels already help and 6 labels cannot wreck it. It ships only if it is not worse than the live weights on the newest
    20% of labels (log-loss and precision@10). Every fit is kept in radar_models with its eval.
  - draft_rules (weekly): recurring edits the operator makes to drafts become short rules the writer follows.
  - uncertain: picks the items the model is least sure about for "help me learn"."""
import logging
import math
from typing import List, Optional, Tuple

import numpy as np

from . import examples, score, store

log = logging.getLogger(__name__)

MIN_LABELS = 60
PRIOR = 2.0            # strength of the pull towards the current weights
STEPS, LR = 600, 0.3
CONVERTED_WEIGHT = 3.0
LEARN_BAND = (0.35, 0.65)

HOME_NEED_SKIPS = ("wrong_area", "already_answered", "old", "other")  # still someone wanting a home: a positive example for L2


async def sync(db, limit: int = 200) -> int:
    """Labels set in the web process are learned here, in the worker (the embedding model lives only in the worker)."""
    n = 0
    coll = db.get_collection(store.SIGNALS)
    for d in await coll.find({"status": {"$in": ["sent", "skipped", "converted"]}, "learned": {"$ne": True}}).to_list(limit):
        try:
            await on_label(db, d, d["status"], d.get("label_reason"), d.get("final_reply"))
        except Exception:
            log.exception("radar: learning from a label failed")
        await coll.update_one({"_id": d["_id"]}, {"$set": {"learned": True}})
        n += 1
    return n


async def on_label(db, sig: dict, label: str, reason: Optional[str], final_reply: Optional[str]) -> None:
    text = (sig.get("text") or "").strip()
    if not text:
        return
    role = ((sig.get("intent") or {}).get("role")) or ""
    if label in ("sent", "converted") or reason in HOME_NEED_SKIPS:
        await examples.add(db, text, 1, role or "buyer", "label", _vector(sig))
    elif reason in ("broker", "not_buyer"):
        await examples.add(db, text, 0, "broker" if reason == "broker" else "noise", "label", _vector(sig))
    if final_reply and sig.get("draft") and final_reply.strip() != sig["draft"].strip():
        await db.get_collection(store.MODELS).insert_one({"kind": "edit", "draft": sig["draft"], "final": final_reply,
                                                          "language": ((sig.get("intent") or {}).get("language")), "at": store.now()})


def _vector(sig: dict):
    from app.platform import embed
    return sig.get("embedding") if sig.get("embedding") and sig.get("embed_model") == embed.model_name() else None


async def load_active(db) -> None:
    """Load the live scorer weights into score.WEIGHTS (called once per cycle)."""
    doc = await db.get_collection(store.MODELS).find_one({"kind": "scorer", "active": True}, sort=[("at", -1)])
    score.use_weights((doc or {}).get("weights"))


def _matrix(docs: List[dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    X = np.asarray([[float((d.get("features") or {}).get(k, 0.5 if k == "vote" else 0.0)) for k in score.FEATURES] for d in docs])
    y = np.asarray([1.0 if d["status"] in ("sent", "converted") else 0.0 for d in docs])
    w = np.asarray([CONVERTED_WEIGHT if d["status"] == "converted" else 1.0 for d in docs])
    return np.hstack([np.ones((len(docs), 1)), X]), y, w


def _vec(weights: dict) -> np.ndarray:
    return np.asarray([weights.get("bias", 0.0)] + [weights.get(k, 0.0) for k in score.FEATURES])


def fit(X: np.ndarray, y: np.ndarray, sw: np.ndarray, prior: np.ndarray, strength: float = PRIOR) -> np.ndarray:
    """MAP logistic regression: minimise weighted log-loss + strength/n * ||w - prior||²; gradient descent (tiny data, convex)."""
    w = prior.copy()
    n = max(1.0, sw.sum())
    for _ in range(STEPS):
        p = 1 / (1 + np.exp(-(X @ w)))
        grad = X.T @ ((p - y) * sw) / n + 2 * strength / n * (w - prior)
        w -= LR * grad
    return w


def log_loss(X, y, w) -> float:
    p = np.clip(1 / (1 + np.exp(-(X @ w))), 1e-6, 1 - 1e-6)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def precision_at(X, y, w, k: int = 10) -> float:
    order = np.argsort(-(X @ w))[:k]
    return float(y[order].mean()) if len(order) else 0.0


async def refit(db) -> dict:
    docs = await db.get_collection(store.SIGNALS).find(
        {"status": {"$in": ["sent", "skipped", "converted"]}, "features": {"$exists": True}}).sort("labelled_at", 1).to_list(5000)
    if len(docs) < MIN_LABELS:
        return {"skipped": f"{len(docs)} labels, need {MIN_LABELS}"}
    X, y, sw = _matrix(docs)
    if y.min() == y.max():
        return {"skipped": "all labels are the same"}
    cut = int(len(docs) * 0.8)
    live = _vec(dict(score.WEIGHTS))
    cand = fit(X[:cut], y[:cut], sw[:cut], live)
    ev = {"n": len(docs), "holdout": len(docs) - cut,
          "live": {"log_loss": log_loss(X[cut:], y[cut:], live), "p@10": precision_at(X[cut:], y[cut:], live)},
          "new": {"log_loss": log_loss(X[cut:], y[cut:], cand), "p@10": precision_at(X[cut:], y[cut:], cand)}}
    ship = ev["new"]["log_loss"] <= ev["live"]["log_loss"] + 1e-3 and ev["new"]["p@10"] >= ev["live"]["p@10"] - 1e-9
    final = fit(X, y, sw, live) if ship else cand  # shipped weights use every label
    weights = {"bias": float(final[0]), **{k: float(v) for k, v in zip(score.FEATURES, final[1:])}}
    models = db.get_collection(store.MODELS)
    if ship:
        await models.update_many({"kind": "scorer", "active": True}, {"$set": {"active": False}})
    await models.insert_one({"kind": "scorer", "weights": weights, "eval": ev, "active": ship, "at": store.now()})
    if ship:
        score.use_weights(weights)
    log.info("radar: refit %s %s", "shipped" if ship else "kept live weights", ev)
    return {"shipped": ship, **ev}


DRAFT_RULES = """Below are replies our team drafted (DRAFT) and what they actually sent after editing (SENT).
Find the edits they make again and again and write them as at most 5 short rules for the writer ("Start with the answer, not 'Hi!'").
Only rules supported by at least two edits. Return ONLY JSON: {"rules": ["...", ...]}"""


async def draft_rules(db, llm) -> dict:
    edits = await db.get_collection(store.MODELS).find({"kind": "edit"}).sort("at", -1).to_list(40)
    if len(edits) < 4 or llm is None:
        return {"skipped": f"{len(edits)} edits"}
    user = "\n\n".join(f"DRAFT: {e['draft'][:400]}\nSENT: {e['final'][:400]}" for e in edits)
    raw = await llm.json(DRAFT_RULES, user)
    rules = [str(r)[:160] for r in ((raw or {}).get("rules") or []) if str(r).strip()][:5]
    if rules:
        await db.get_collection(store.MODELS).update_one({"kind": "draft_rules"}, {"$set": {"rules": rules, "at": store.now()}},
                                                         upsert=True)
    return {"rules": rules}


async def current_draft_rules(db) -> List[str]:
    doc = await db.get_collection(store.MODELS).find_one({"kind": "draft_rules"})
    return list((doc or {}).get("rules") or [])


def uncertain(intent: float, vote: Optional[float]) -> bool:
    """True when the model and the bank are unsure: the label teaches the most (active learning, uncertainty sampling)."""
    lo, hi = LEARN_BAND
    return lo <= intent <= hi or (vote is not None and lo <= vote <= hi)


def entropy(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -(p * math.log(p) + (1 - p) * math.log(1 - p))
