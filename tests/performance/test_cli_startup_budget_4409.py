"""#4409: `spec-kitty --help` must not re-acquire its import-time tax.

Before this guard, a bare ``--help`` cost ~3.2 s while importing the package
itself cost ~0.2 s. Almost all of the difference was one transitive import:
``jsonschema`` eagerly loads its format checkers, and one of those
(``rfc3987_syntax.syntax_helpers``, which builds a Lark grammar at import
time) costs ~1.8 s on its own. Eight modules imported ``jsonschema`` at module
scope, so whichever the CLI touched first paid for all of them — on a path
that validates nothing.

Deferring those imports to their single call sites took ``--help`` to ~1.0 s.
The tax is easy to reintroduce by accident: one ``import jsonschema`` at the
top of a module the CLI imports is enough. This test is the ratchet.

It lives in the ``performance`` lane (nightly) rather than the per-PR gate —
wall-clock budgets are environment-sensitive, and a shared runner under load
should not turn a green change red. The structural half of the guard (no
module-scope ``jsonschema`` import in the CLI's import graph) is cheap and
deterministic, so that half runs everywhere.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests._perf_helpers import assert_timing_budget

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Generous enough to absorb a loaded laptop or CI runner, tight enough to
#: catch the ~1.8 s regression this issue removed (pre-fix was ~3.2 s).
_HELP_BUDGET_SECONDS = 2.5


class _ModuleScopeJsonschemaImports(ast.NodeVisitor):
    """Find imports reached while importing a module; skip deferred scopes."""

    def __init__(self) -> None:
        self.lines: list[int] = []

    def visit_Import(self, node: ast.Import) -> None:
        if any(alias.name == "jsonschema" or alias.name.startswith("jsonschema.") for alias in node.names):
            self.lines.append(node.lineno)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module == "jsonschema" or module.startswith("jsonschema."):
            self.lines.append(node.lineno)

    def visit_FunctionDef(self, _node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, _node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, _node: ast.Lambda) -> None:
        return


def _module_scope_jsonschema_import_lines(source: str) -> list[int]:
    visitor = _ModuleScopeJsonschemaImports()
    visitor.visit(ast.parse(source))
    return visitor.lines


def test_jsonschema_stays_out_of_module_scope_across_src() -> None:
    """The structural half: tree-wide, deterministic, and what regresses.

    A module-scope ``import jsonschema`` anywhere in the CLI source tree can
    reintroduce the whole format-checker chain for every CLI invocation.
    """
    offending: list[str] = []
    for path in sorted((REPO_ROOT / "src").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for line in _module_scope_jsonschema_import_lines(source):
            offending.append(f"{path.relative_to(REPO_ROOT)}:{line}")

    assert not offending, (
        f"#4409: source modules import jsonschema at module scope ({offending}). "
        "That pulls jsonschema._format -> rfc3987_syntax (~1.8s) into every "
        "`spec-kitty` invocation. Import it inside the function that validates."
    )


def test_module_scope_guard_finds_import_indented_under_try() -> None:
    source = """try:\n    import jsonschema.validators\nexcept ImportError:\n    pass\n\nclass Schema:\n    from jsonschema import Draft7Validator\n"""

    assert _module_scope_jsonschema_import_lines(source) == [2, 7]


def test_module_scope_guard_allows_deferred_function_import() -> None:
    source = """def validate():\n    from jsonschema import Draft7Validator\n"""

    assert _module_scope_jsonschema_import_lines(source) == []


@pytest.mark.performance
def test_help_stays_inside_its_startup_budget() -> None:
    """The wall-clock half: nightly-only, measured through the real entry point."""
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, "-m", "specify_cli.__init__", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    elapsed = time.monotonic() - started

    measured = elapsed if completed.returncode == 0 else float("inf")
    name = f"spec-kitty --help startup (exit={completed.returncode}, stderr={completed.stderr[-2000:]!r})"
    assert_timing_budget(measured, _HELP_BUDGET_SECONDS, name=name)
