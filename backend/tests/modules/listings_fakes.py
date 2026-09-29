"""Fakes for listings tests: adds $in/$ne and skip() on top of the shared in-memory fakes."""
import copy

from .fakes import FakeCollection, FakeDb, _Cursor


def match(doc, flt):
    for key, cond in flt.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, arg in cond.items():
                ok = {
                    "$in": lambda: val in arg, "$ne": lambda: val != arg,
                    "$gte": lambda: val is not None and val >= arg, "$gt": lambda: val is not None and val > arg,
                }[op]()
                if not ok:
                    return False
        elif isinstance(val, list) and not isinstance(cond, list):
            if cond not in val:
                return False
        elif val != cond:
            return False
    return True


class _SkipCursor(_Cursor):
    def skip(self, n):
        self.docs = self.docs[n:]
        return self


class ListingsCollection(FakeCollection):
    async def find_one(self, flt=None, sort=None):
        found = [d for d in self.docs if match(d, flt or {})]
        return copy.deepcopy(found[0]) if found else None

    async def count_documents(self, flt=None):
        return sum(1 for d in self.docs if match(d, flt or {}))

    def find(self, flt=None):
        return _SkipCursor([d for d in self.docs if match(d, flt or {})])

    async def update_one(self, flt, update):
        for d in self.docs:
            if match(d, flt):
                self._apply(d, update)
                return


class ListingsDb(FakeDb):
    def get_collection(self, name):
        return self.cols.setdefault(name, ListingsCollection())
