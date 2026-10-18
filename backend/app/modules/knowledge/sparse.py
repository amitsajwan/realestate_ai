"""BM25 as sparse vectors for Qdrant: exact words count (project names, RERA numbers, 'LIG', 'EMD'), in any script.

A passage's vector holds, per word, BM25's term weight tf*(k1+1) / (tf + k1*(1-b+b*len/AVG_LEN)); a question's holds 1 per word.
Qdrant multiplies in each word's IDF over the collection (sparse vector `bm25` with modifier idf), so dot product = BM25 score.
Words are lower-cased runs of letters/digits (Devanagari included, with its vowel signs), a few common English/Hindi/Marathi
filler words dropped, and hashed to a stable 31-bit index. No stemming: Hindi and Marathi have no stemmer we trust, and the
meaning vectors already cover 'apply'/'applying'.
"""
import re
import zlib
from collections import Counter
from typing import Dict, List

K1 = 1.2
B = 0.75
AVG_LEN = 60
WORD = re.compile(r"[a-z0-9ऀ-ॿ]+")
STOP = frozenset("""a an the is are was were be been am i you we they he she it this that these those of in on at to for from by with and or
not no do does did can could will would should my your our me us what which who whom how when where why there here as if so than then
about into any all also just only very hai hain kya ka ki ke ko se me mein aur ya bhi to na nahi kar karo
आहे आहेत का की व आणि हे ही तो ती ते मी तुम्ही काय कसे कधी कुठे है हैं क्या का की के को से में और या भी तो""".split())


def words(text: str) -> List[str]:
    return [w for w in WORD.findall((text or "").lower()) if w not in STOP and (len(w) > 1 or w.isdigit())]


def _index(word: str) -> int:
    return zlib.crc32(word.encode("utf-8")) & 0x7FFFFFFF


def _vector(weights: Dict[int, float]) -> dict:
    keys = sorted(weights)
    return {"indices": keys, "values": [round(weights[k], 4) for k in keys]}


def doc_vector(text: str) -> dict:
    w = words(text)
    n = len(w) or 1
    tf = Counter(_index(x) for x in w)
    return _vector({i: c * (K1 + 1) / (c + K1 * (1 - B + B * n / AVG_LEN)) for i, c in tf.items()})


def query_vector(text: str) -> dict:
    return _vector({_index(x): 1.0 for x in set(words(text))})
