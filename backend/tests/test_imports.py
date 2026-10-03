"""Every module imports, and every import written inside a function points at something that exists.

Imports inside functions only run when that code path runs, so a module moved or renamed during the modernization can
break one without any other test noticing. This test resolves all of them up front.
"""
import ast
import importlib
import logging
import pkgutil
from pathlib import Path

import pytest

import app

APP_DIR = Path(app.__file__).parent
# Old-layer packages are imported as the app imports them; their unused leftovers are deleted in MODERNIZATION step 8.
SKIP = ("app.main",)


def _module_names():
    for info in pkgutil.walk_packages([str(APP_DIR)], prefix="app."):
        if not info.name.startswith(SKIP):
            yield info.name


def _function_level_imports():
    """(file, line, module, names) for every `from X import a, b` / `import X` nested inside a function."""
    for path in sorted(APP_DIR.rglob("*.py")):
        rel = path.relative_to(APP_DIR.parent).with_suffix("")
        package = ".".join(rel.parts[:-1]) if rel.name != "__init__" else ".".join(rel.parts[:-1])
        tree = ast.parse(path.read_text("utf8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for node in ast.walk(fn):
                if isinstance(node, ast.ImportFrom):
                    base = node.module or ""
                    if node.level:
                        parts = package.split(".")
                        parts = parts[: len(parts) - (node.level - 1)]
                        base = ".".join(parts + ([base] if base else []))
                    if base == "app" or base.startswith("app."):
                        yield str(rel), node.lineno, base, [a.name for a in node.names]
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        if a.name.startswith("app."):
                            yield str(rel), node.lineno, a.name, []


@pytest.fixture(autouse=True, scope="module")
def _keep_logging_as_it_was():
    """Some old modules configure logging when imported (app/core/logging.py makes the 'app' logger stop propagating);
    put it back afterwards so later tests that check log output still see it. Those modules go in MODERNIZATION step 8."""
    loggers = [logging.getLogger(), logging.getLogger("app")]
    saved = [(lg, list(lg.handlers), lg.level, lg.propagate, lg.disabled) for lg in loggers]
    yield
    for lg, handlers, level, propagate, disabled in saved:
        lg.handlers[:] = handlers
        lg.setLevel(level)
        lg.propagate, lg.disabled = propagate, disabled


@pytest.mark.parametrize("name", sorted(_module_names()))
def test_module_imports(name):
    importlib.import_module(name)


def test_every_function_level_import_resolves():
    missing = []
    for where, line, module, names in _function_level_imports():
        try:
            mod = importlib.import_module(module)
        except Exception as e:  # noqa: BLE001
            missing.append(f"{where}:{line} import {module} failed: {type(e).__name__}: {e}")
            continue
        for n in names:
            if n == "*" or hasattr(mod, n):
                continue
            try:
                importlib.import_module(f"{module}.{n}")  # a submodule imported by name
            except ImportError:
                missing.append(f"{where}:{line} {module} has no {n}")
    assert not missing, "\n".join(missing)
