"""The labelled example bank (docs/RADAR.md §5 L2, §7): short comments marked "home need" (1) or not (0), with their embedding.
It does two jobs with no fine-tuning:
  - L2 gate: a weighted k-nearest-neighbour vote decides whether a comment that passed the rules is worth a model call;
    it only drops a comment when its neighbours clearly agree it is not a home need.
  - Dynamic few-shots: the most similar labelled comments are shown to the model as worked examples.
It starts from SEED (hand-written, EN/HI/MR/Hinglish) and grows from operator labels (learn.py)."""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from app.platform import embed

from . import store

log = logging.getLogger(__name__)

K = 9
TEMP = 0.03          # softmax temperature over cosine similarity: e5 similarities sit in a narrow band (0.7-0.95)
DROP_BELOW = 0.18    # vote share for "home need" below which L2 drops the comment
MIN_PER_CLASS = 15   # below this the bank cannot vote; everything goes on to the model

# (text, label, role hint for few-shots)
SEED: Tuple[Tuple[str, int, str], ...] = (
    ("2bhk price kya hai?", 1, "buyer"), ("What is the price of 2 BHK here?", 1, "buyer"),
    ("2 BHK ची किंमत किती आहे?", 1, "buyer"), ("Possession kab milega?", 1, "buyer"),
    ("Is this ready to move? Looking for 3bhk under 1 cr", 1, "buyer"), ("Wagholi mein 60L tak flat mil jayega?", 1, "buyer"),
    ("Any resale 2bhk available near Kharadi EON IT park?", 1, "buyer"), ("Site visit kaise book kare?", 1, "buyer"),
    ("Kitne floor hai aur carpet area kitna hai 2bhk ka?", 1, "buyer"), ("Home loan milega is project pe? SBI approved?", 1, "buyer"),
    ("Looking for 1 BHK on rent in Hinjawadi phase 1", 1, "renter"), ("Rent kitna hai 2bhk ka yaha?", 1, "renter"),
    ("I visited last week, is there any discount on 3 BHK?", 1, "buyer"), ("Maintenance charges kitne hai per month?", 1, "buyer"),
    ("Is it RERA registered? What is the RERA number?", 1, "buyer"), ("Plot rate kya chal raha hai Ranjangaon side?", 1, "investor"),
    ("Investment ke liye kaunsa area best rahega Pune east me?", 1, "investor"), ("Brochure and floor plan please", 1, "buyer"),
    ("Is there any 2bhk under 70 lakh in Baner?", 1, "buyer"), ("घर घ्यायचे आहे वाघोली मध्ये, बजेट 50 लाख", 1, "buyer"),
    ("Hum log Keshav Nagar me 2bhk dekh rahe hai, kaunsa project accha hai?", 1, "buyer"),
    ("How is the water supply in this society? Planning to buy", 1, "buyer"), ("Booking amount kitna hai?", 1, "buyer"),
    ("Is the builder delaying possession? Thinking of booking", 1, "buyer"), ("Price per sq ft kitna hai abhi?", 1, "buyer"),
    ("Nice video bhai", 0, "noise"), ("Very informative, thanks", 0, "noise"), ("Subscribe to my channel for more", 0, "noise"),
    ("We have best deals in Wakad, call now", 0, "broker"), ("Contact me for site visit 98xxxxxx, channel partner", 0, "broker"),
    ("Worst builder, I have been waiting for possession for 3 years", 0, "noise"), ("Background music name?", 0, "noise"),
    ("Pune traffic is so bad now", 0, "noise"), ("Who else is watching in 2026?", 0, "noise"), ("Jai Maharashtra", 0, "noise"),
    ("Camera kaunsa use kiya?", 0, "noise"), ("Bhai tum kaha se ho?", 0, "noise"), ("I sold my flat here last year, good returns", 0, "seller"),
    ("Mera flat bechna hai Wakad me, buyer chahiye", 0, "seller"), ("Your editing is great", 0, "noise"),
    ("Price is too high for this location, bubble hai", 0, "noise"), ("मस्त व्हिडिओ", 0, "noise"), ("बहुत बढ़िया जानकारी", 0, "noise"),
    ("First comment", 0, "noise"), ("Are you a broker?", 0, "noise"), ("Society members are fighting over parking, shame", 0, "noise"),
    ("Real estate is a scam in India", 0, "noise"), ("Guaranteed 12% returns, invest with us", 0, "broker"),
    ("Hindi me video banao", 0, "noise"), ("Lovely sunset view from the terrace", 0, "noise"),
)


@dataclass
class Bank:
    model: str
    texts: List[str]
    labels: np.ndarray        # 0/1
    roles: List[str]
    vectors: np.ndarray       # (n, 384)

    def can_vote(self) -> bool:
        pos = int(self.labels.sum())
        return pos >= MIN_PER_CLASS and len(self.labels) - pos >= MIN_PER_CLASS


async def seed(db) -> None:
    """Insert SEED once per embedder (vectors from different embedders are never mixed)."""
    model = embed.model_name()
    coll = db.get_collection(store.EXAMPLES)
    if await coll.count_documents({"model": model, "origin": "seed"}) >= len(SEED):
        return
    vecs = embed.embed([t for t, _, _ in SEED])
    for (text, label, role), v in zip(SEED, vecs):
        await coll.update_one({"model": model, "text": text}, {"$setOnInsert": {
            "label": label, "role": role, "origin": "seed", "embedding": v.tolist(), "created_at": store.now()}}, upsert=True)


async def add(db, text: str, label: int, role: str, origin: str, vector: Optional[List[float]] = None) -> None:
    model = embed.model_name()
    v = vector if vector is not None else embed.embed_one(text)
    await db.get_collection(store.EXAMPLES).update_one(
        {"model": model, "text": text[:600]},
        {"$set": {"label": int(label), "role": role, "origin": origin, "embedding": v, "updated_at": store.now()},
         "$setOnInsert": {"created_at": store.now()}}, upsert=True)


async def load(db, limit: int = 5000) -> Bank:
    model = embed.model_name()
    docs = await db.get_collection(store.EXAMPLES).find({"model": model}).sort("updated_at", -1).to_list(limit)
    vecs = np.asarray([d["embedding"] for d in docs], dtype=np.float32) if docs else np.zeros((0, embed.DIM), np.float32)
    return Bank(model, [d["text"] for d in docs], np.asarray([int(d["label"]) for d in docs]), [d.get("role", "") for d in docs], vecs)


def neighbours(bank: Bank, v: np.ndarray, k: int = K) -> List[int]:
    if not len(bank.labels):
        return []
    sims = embed.cosine(v, bank.vectors)
    k = min(k, len(sims))
    return list(np.argsort(-sims)[:k])


def vote(bank: Bank, v: np.ndarray) -> Optional[float]:
    """Share of 'home need' among the k nearest examples, softmax-weighted by similarity; None when the bank is too small."""
    if not bank.can_vote():
        return None
    sims = embed.cosine(v, bank.vectors)
    idx = np.argsort(-sims)[:K]
    w = np.exp((sims[idx] - sims[idx].max()) / TEMP)
    return float((w * bank.labels[idx]).sum() / w.sum())


def few_shots(bank: Bank, v: np.ndarray, n: int = 6) -> List[Tuple[str, int, str]]:
    """The most similar labelled comments, both kinds, so the model sees where the line is for comments like this one."""
    out = [(bank.texts[i], int(bank.labels[i]), bank.roles[i]) for i in neighbours(bank, v, n * 2)]
    pos = [x for x in out if x[1] == 1][: n // 2]
    neg = [x for x in out if x[1] == 0][: n - len(pos)]
    return pos + neg
