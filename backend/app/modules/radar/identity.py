"""Step 2: dedupe + identity (docs/RADAR.md §5). The same question pasted under five videos is one lead: a 64-bit SimHash over
normalised word shingles finds near-duplicates (Hamming distance ≤ 3). A `person_key` (source + author id) lets a repeat asker
raise the score instead of making a new card. Normalisation makes "2 bhk"/"2bhk"/"two bedroom" and common Devanagari home words
the same token, so the hash and the rules see one spelling."""
import hashlib
import re
from typing import Optional

NEAR = 3                  # Hamming bits
NUM_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "ek": "1", "do": "2", "teen": "3", "char": "4"}
DEVANAGARI = {             # Hindi/Marathi home words -> one Latin spelling
    "फ्लॅट": "flat", "फ्लैट": "flat", "घर": "ghar", "किंमत": "price", "कीमत": "price", "किती": "kitna", "कितना": "kitna",
    "लाख": "lakh", "करोड़": "crore", "कोटी": "crore", "ताबा": "possession", "कब्जा": "possession", "भाडे": "rent", "भाड़ा": "rent",
    "प्लॉट": "plot", "प्लाट": "plot", "बजट": "budget", "बीएचके": "bhk",
}
SYN = [(re.compile(p, re.I), r) for p, r in (
    (r"\b(\d(?:\.5)?)\s*-?\s*(?:bhk|b\.h\.k\.?|bed\s*rooms?|bedroom)\b", r"\1bhk"),
    (r"\b(lacs?|lakhs?|lac)\b", "lakh"), (r"\b(crores?|cr)\b", "crore"), (r"\bkitne|kitni|kitana\b", "kitna"),
    (r"\b(keemat|kimat|kimmat)\b", "price"), (r"\b(rates?|cost)\b", "price"), (r"\bpls|plz|please\b", ""),
)]


def normalise(text: str) -> str:
    t = (text or "").lower()
    for dev, lat in DEVANAGARI.items():
        t = t.replace(dev, f" {lat} ")
    for w, d in NUM_WORDS.items():
        t = re.sub(rf"\b{w}\s+(bhk|bed)", rf"{d} \1", t)
    for pat, rep in SYN:
        t = pat.sub(rep, t)
    t = re.sub(r"https?://\S+|@\w+", " ", t)
    return " ".join(re.sub(r"[^\w\s]+", " ", t, flags=re.U).split())


def simhash(text: str) -> int:
    words = normalise(text).split()
    grams = [" ".join(words[i:i + 2]) for i in range(max(1, len(words) - 1))] or [""]
    acc = [0] * 64
    for g in grams:
        h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "little")
        for b in range(64):
            acc[b] += 1 if h >> b & 1 else -1
    return sum(1 << b for b in range(64) if acc[b] > 0)


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def as_signed(h: int) -> int:
    """Mongo stores signed 64-bit integers."""
    return h - (1 << 64) if h >= 1 << 63 else h


def as_unsigned(h: int) -> int:
    return h + (1 << 64) if h < 0 else h


def person_key(source: str, author_id: str, author: str = "") -> Optional[str]:
    who = (author_id or "").strip() or (author or "").strip().lower()
    return f"{source}:{who}" if who else None


def bands(h: int) -> list:
    """Four 16-bit bands: two hashes within 3 bits share at least one band exactly (pigeonhole), so a near-duplicate search is
    an indexed equality lookup on any band instead of a scan."""
    return [f"{i}:{(h >> (16 * i)) & 0xFFFF:x}" for i in range(4)]


async def near_duplicate(db, coll: str, h: int, exclude_id, key: Optional[str]) -> Optional[dict]:
    """An earlier signal by the same person with almost the same text, or None. Different people asking the same common
    question ("2bhk price kya hai?") are different leads; with no known author, any earlier near-copy counts (a re-paste)."""
    flt = {"sim_bands": {"$in": bands(h)}, "_id": {"$ne": exclude_id}, **({"person_key": key} if key else {})}
    async for d in db.get_collection(coll).find(flt,
                                                {"simhash": 1, "status": 1, "person_key": 1}).limit(50):
        if d.get("simhash") is not None and hamming(as_unsigned(d["simhash"]), h) <= NEAR:
            return d
    return None


async def times_asked(db, coll: str, key: Optional[str], exclude_id) -> int:
    """How many other questions this person asked that passed the rules."""
    if not key:
        return 0
    return await db.get_collection(coll).count_documents({"person_key": key, "_id": {"$ne": exclude_id},
                                                          "status": {"$in": ["scored", "sent", "converted", "duplicate"]}})
