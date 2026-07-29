"""Purity guard rails -- the rule everything else depends on (R1).

Spec: docs/specs/underwriting/grading-engine-core.md, R1, section 8.
"""
import ast
import copy
import datetime as datetime_module
import socket
from pathlib import Path

from app.underwriting import grading
from app.underwriting.grading import grade, load_params

from .conftest import make_valid_input

_PACKAGE_DIR = Path(grading.__file__).parent


def _iter_package_py_files():
    for py_file in sorted(_PACKAGE_DIR.rglob("*.py")):
        yield py_file


def test_grade_is_deterministic_across_repeated_calls():
    inputs = make_valid_input()
    params = load_params()

    results = [grade(inputs, params) for _ in range(100)]
    first = results[0]
    for result in results[1:]:
        assert result == first


def test_grading_package_imports_nothing_from_app():
    for py_file in _iter_package_py_files():
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "app" and not alias.name.startswith("app."), (
                        f"{py_file}: imports {alias.name!r} -- R1 forbids importing from app/"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    assert node.module != "app" and not node.module.startswith("app."), (
                        f"{py_file}: imports from {node.module!r} -- R1 forbids importing from app/"
                    )


def test_grading_package_has_no_async_def():
    for py_file in _iter_package_py_files():
        tree = ast.parse(py_file.read_text(), filename=str(py_file))
        for node in ast.walk(tree):
            assert not isinstance(node, ast.AsyncFunctionDef), (
                f"{py_file}: defines `async def {node.name}` -- R1 requires this package to be "
                "plain synchronous `def` throughout (CLAUDE.md's async rule is an approved, "
                "documented deviation here -- see deviations register D14)"
            )


def test_grade_performs_no_io(monkeypatch):
    # load_params() is the one place this package touches disk (R1) -- do it
    # BEFORE patching `open`, so `grade()` itself is what's under test.
    params = load_params()
    inputs = make_valid_input()

    def _boom_open(*args, **kwargs):
        raise AssertionError("grade() called open() -- R1 forbids file I/O at call time")

    def _boom_socket(*args, **kwargs):
        raise AssertionError("grade() opened a socket -- R1 forbids network calls")

    class _ForbiddenDatetime:
        @classmethod
        def now(cls, *args, **kwargs):
            raise AssertionError("grade() called datetime.now() -- R1 forbids non-determinism")

    monkeypatch.setattr("builtins.open", _boom_open)
    monkeypatch.setattr(socket, "socket", _boom_socket)
    monkeypatch.setattr(datetime_module, "datetime", _ForbiddenDatetime)

    result = grade(inputs, params)
    assert result.decision in {"APPROVED", "REVIEW", "REJECT", "AI_PENDING", "INSUFFICIENT_DATA"}


def test_grade_does_not_mutate_input():
    inputs = make_valid_input()
    snapshot = copy.deepcopy(inputs)

    grade(inputs, load_params())

    assert inputs == snapshot
