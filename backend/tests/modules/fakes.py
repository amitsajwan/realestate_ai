"""Minimal in-memory stand-ins for Motor collections, enough for service-level tests."""
import copy
import itertools

from pymongo.errors import DuplicateKeyError

_ids = itertools.count(1)


def _match(doc, flt):
    for key, cond in flt.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, arg in cond.items():
                if op == "$gte" and not (val is not None and val >= arg):
                    return False
                if op == "$gt" and not (val is not None and val > arg):
                    return False
                if op == "$in" and val not in arg:
                    return False
        elif isinstance(val, list) and not isinstance(cond, list):
            if cond not in val:  # Mongo array-membership semantics
                return False
        elif val != cond:
            return False
    return True


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, field, direction=1):
        self.docs.sort(key=lambda d: d[field], reverse=direction < 0)
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length=None):
        return [copy.deepcopy(d) for d in self.docs]


class _UpdateResult:
    def __init__(self, n):
        self.matched_count = self.modified_count = n


class FakeCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        doc = copy.deepcopy(doc)
        doc.setdefault("_id", f"id{next(_ids)}")
        if any(d["_id"] == doc["_id"] for d in self.docs):  # like Mongo: _id is unique
            raise DuplicateKeyError(f"E11000 duplicate key: {doc['_id']!r}")
        self.docs.append(doc)
        return type("R", (), {"inserted_id": doc["_id"]})

    async def find_one(self, flt=None, sort=None):
        found = [d for d in self.docs if _match(d, flt or {})]
        if sort:
            field, direction = sort[0]
            found.sort(key=lambda d: d[field], reverse=direction < 0)
        return copy.deepcopy(found[0]) if found else None

    async def count_documents(self, flt=None):
        return sum(1 for d in self.docs if _match(d, flt or {}))

    def find(self, flt=None):
        return _Cursor([d for d in self.docs if _match(d, flt or {})])

    @staticmethod
    def _apply(d, update):
        for k, v in update.get("$set", {}).items():
            d[k] = v
        for k, v in update.get("$inc", {}).items():
            d[k] = d.get(k, 0) + v
        for k, v in update.get("$addToSet", {}).items():
            if v not in d.setdefault(k, []):
                d[k].append(v)
        for k, v in update.get("$push", {}).items():
            d.setdefault(k, []).append(v)

    async def update_one(self, flt, update):
        for d in self.docs:
            if _match(d, flt):
                self._apply(d, update)
                return _UpdateResult(1)
        return _UpdateResult(0)

    async def update_many(self, flt, update):
        for d in self.docs:
            if _match(d, flt):
                self._apply(d, update)


class FakeDb:
    def __init__(self):
        self.cols = {}

    def get_collection(self, name):
        return self.cols.setdefault(name, FakeCollection())
