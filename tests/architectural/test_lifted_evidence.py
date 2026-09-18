"""Always-on gate: the project-sync consent evidence manifest is immutable.

Lifted from ``tests/evidence/test_project_sync_consent_manifest.py`` (WP11
T049/T054), a ``tests/evidence`` tree recorded ``out_of_matrix`` in
``.github/ci-module-registry.yml`` — no per-PR lane selects it (#4374
disposition ledger, disposition 2 — lift-invariant).

The source suite exercises ``scripts/evidence/build_project_sync_consent_manifest.py``
through its real subprocess CLI across many fail-closed refusal branches
(floating refs, dirty checkouts, digest drift, duplicate ownership, expired
retention...). Those refusal branches are broad, enumerable-but-numerous
coverage and stay make-test-full-only; what is lifted here is the tree's
single headline claim from its own module docstring — the manifest builder
"fails closed and emits an immutable, deterministic bundle" — i.e. a valid
input set produces a schema-complete manifest, and once written that
manifest is never silently overwritten by a second run.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.architectural]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "evidence" / "build_project_sync_consent_manifest.py"

_CONTRACT_BODY = "openapi: 3.1.0\ninfo:\n  title: cli-saas current api\n"
_CREATED_AT = "2026-08-13T00:00:00Z"
_EXPIRES_OK = "2026-11-12T00:00:00Z"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()  # noqa: TID251 - file-integrity checksum of raw evidence bytes, not the charter hash


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(("git", "-C", str(cwd), *args), check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def _init_repo(path: Path, files: dict[str, str]) -> str:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "evidence@example.test")
    _git(path, "config", "user.name", "Evidence Test")
    return _commit_files(path, files, "initial candidate state")


def _commit_files(path: Path, files: dict[str, str], message: str) -> str:
    for relative, content in files.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-qm", message)
    return _git(path, "rev-parse", "HEAD")


class _Inputs:
    """One complete, valid explicit input set."""

    def __init__(self, tmp_path: Path) -> None:
        self.core_checkout = tmp_path / "core-candidate"
        self.core_commit = _init_repo(self.core_checkout, {"README.md": "core candidate\n"})

        self.saas_checkout = tmp_path / "saas-wp04-candidate"
        self.tombstone_commit = _init_repo(self.saas_checkout, {"TOMBSTONE.md": "wp02 milestone\n"})
        self.saas_commit = _commit_files(self.saas_checkout, {"contracts/cli-saas-current-api.yaml": _CONTRACT_BODY}, "candidate head")
        self.contract_sha256 = _sha256(_CONTRACT_BODY.encode("utf-8"))

        self.artifact_root = tmp_path / "raw"
        self.artifact_root.mkdir()
        self.artifact_body = b'{"samples": [1, 2, 3]}\n'
        (self.artifact_root / "six-project-omission.json").write_bytes(self.artifact_body)
        self.artifacts = [f"core:six-project-omission:{_sha256(self.artifact_body)}:six-project-omission.json"]

        self.commands = ["core-six-project-proof:0:uv run python -m pytest tests/integration/test_project_sync_six_project.py"]
        self.saas_wp02_evidence_uri = "https://evidence.example.test/saas-wp02/bundle"
        self.saas_wp02_evidence_sha256 = _sha256(b"saas wp02 evidence bundle")
        self.saas_wp08_evidence_uri = "https://evidence.example.test/saas-wp08/bundle"
        self.saas_wp08_evidence_sha256 = _sha256(b"saas wp08 evidence bundle")
        self.created_at = _CREATED_AT
        self.retention_uri = "https://evidence.example.test/retention/run-1"
        self.retention_expires_at = _EXPIRES_OK
        self.output_root = tmp_path / "bundle"

    def argv(self) -> list[str]:
        arguments = [
            "--core-checkout",
            str(self.core_checkout),
            "--expected-core-commit",
            self.core_commit,
            "--saas-checkout",
            str(self.saas_checkout),
            "--expected-saas-commit",
            self.saas_commit,
            "--expected-contract-sha256",
            self.contract_sha256,
            "--tombstone-commit",
            self.tombstone_commit,
            "--saas-wp02-evidence-uri",
            self.saas_wp02_evidence_uri,
            "--saas-wp02-evidence-sha256",
            self.saas_wp02_evidence_sha256,
            "--saas-wp08-evidence-uri",
            self.saas_wp08_evidence_uri,
            "--saas-wp08-evidence-sha256",
            self.saas_wp08_evidence_sha256,
            "--artifact-root",
            str(self.artifact_root),
            "--created-at",
            self.created_at,
            "--retention-uri",
            self.retention_uri,
            "--retention-expires-at",
            self.retention_expires_at,
            "--output-root",
            str(self.output_root),
        ]
        for artifact in self.artifacts:
            arguments.extend(["--artifact", artifact])
        for command in self.commands:
            arguments.extend(["--command", command])
        return arguments

    def run(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            (sys.executable, str(_SCRIPT), *self.argv()),
            check=False,
            capture_output=True,
            text=True,
        )

    @property
    def manifest_path(self) -> Path:
        return self.output_root / self.core_commit / "manifest.json"


@pytest.fixture
def inputs(tmp_path: Path) -> _Inputs:
    return _Inputs(tmp_path)


def test_valid_inputs_produce_schema_complete_manifest(inputs: _Inputs) -> None:
    result = inputs.run()
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(inputs.manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "project-sync-consent-evidence-manifest/1"
    assert manifest["attestation"]["core"] == {"commit": inputs.core_commit, "checkout_label": "core-candidate"}
    assert manifest["retention"] == {"uri": inputs.retention_uri, "expires_at": _EXPIRES_OK, "minimum_days": 90}


def test_existing_manifest_is_never_overwritten(inputs: _Inputs) -> None:
    """The evidence manifest's core immutability contract: once written, a
    second run over the same candidate commit refuses rather than silently
    replacing it."""
    assert inputs.run().returncode == 0
    original = inputs.manifest_path.read_bytes()

    result = inputs.run()

    assert result.returncode == 1
    assert "immutable" in result.stderr
    assert inputs.manifest_path.read_bytes() == original
