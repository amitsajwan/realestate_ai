"""Minimal in-memory stand-ins for Motor collections, enough for service-level tests."""
import copy
import itertools

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
        elif val != cond:
            return False
    return True


class FakeCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc):
        doc = copy.deepcopy(doc)
        doc.setdefault("_id", f"id{next(_ids)}")
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

    async def update_one(self, flt, update):
        for d in self.docs:
            if _match(d, flt):
                for k, v in update.get("$set", {}).items():
                    d[k] = v
                for k, v in update.get("$inc", {}).items():
                    d[k] = d.get(k, 0) + v
                return


class FakeDb:
    def __init__(self):
        self.cols = {}

    def get_collection(self, name):
        return self.cols.setdefault(name, FakeCollection())
