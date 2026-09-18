# Contract: acceptance checks (v3, post-tasks squad)

Done ⇔ all pass on `chore/decide-out-of-matrix-test-dirs`. Evidence lives under
`kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/evidence/` (WP01-owned; single evidence home —
NOT `decisions/`). Every disposition-3 registry reason MUST embed a structured pointer
`evidence: analysis/evidence/<file>.json` (parsable, not free prose).

## 1. Guard integrity (NFR-004, SC-003)
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/architectural/test_module_shard_registry.py -q
```

## 2. Snapshot elimination (NFR-005, SC-001) — deferral phrases banned + names a surface
```bash
python - <<'PY'
import yaml, re
g=yaml.safe_load(open(".github/ci-module-registry.yml"))["out_of_matrix_test_dirs"]
DEFERRAL=("recorded deliberately","measured-durations decision, never a silent default")
bad=[]
for grp in g:
    r=" ".join(grp["reason"].split())
    if any(p in r for p in DEFERRAL): bad.append(("deferral-phrase",grp["dirs"][:2]))
    if not re.search(r"(tests/|module|corpus|windows_ci|nightly|e2e|architectural|#\d+)", r):
        bad.append(("names-no-surface",grp["dirs"][:2]))
assert not bad, f"non-decision reasons: {bad}"
print("ok")
PY
```

## 3. Coverage-equivalence — RUNNABLE, pointer-resolved (Renata F1; permanent in WP04)
For every disposition-3 entry claiming an in-matrix mirror, its reason carries `evidence: analysis/evidence/<f>.json`;
the referenced JSON exists, committed, and records `covered(line/branch)` of the demoted tree ⊆ the retained
in-matrix tree. WP04's guard resolves each pointer and re-asserts the stored subset (reads the JSON — does not
re-run coverage). A reason with no resolvable pointer FAILS.

## 4. Promotion evidence freshness + parity (NFR-003, SC-002; Renata F2) — freshness is COMPUTED
`analysis/evidence/capture-floor.txt` (WP01) holds an ISO mission-start floor.
```bash
python - <<'PY'
import json,subprocess,yaml,datetime,pathlib
base=yaml.safe_load(subprocess.run(["git","show","main:.github/ci-module-registry.yml"],capture_output=True,text=True).stdout)
head=yaml.safe_load(open(".github/ci-module-registry.yml"))
bsh={m["module"]:m["shard_count"] for m in base["modules"]}
t=json.load(open(".github/ci-shard-timings.json")); prov=t.get("module_capture_provenance",{})
floor=pathlib.Path("kitty-specs/decide-out-of-matrix-test-dirs-01M2TKC7/analysis/evidence/capture-floor.txt").read_text().strip()
changed=[m["module"] for m in head["modules"] if m["shard_count"]!=bsh.get(m["module"])]
for M in changed:
    p=prov.get(M) or {}; assert p, f"{M}: no provenance"
    n=len(t["module_test_durations"].get(M,[])); c=t["module_test_count"].get(M)
    assert p.get("unique_tests_measured")==n==c, f"{M}: parity {p.get('unique_tests_measured')}/{n}/{c}"
    assert p.get("captured_at","")>=floor, f"{M}: stale capture {p.get('captured_at')} < floor {floor}"
print("fresh+parity ok:", changed or "(no shard_count changes)")
PY
```

## 5. Per-PR de-silencing — DURABLE guard, not a transient injection (Renata F3; Paula F3; SC-005)
WP04 adds a permanent guard: for each module row whose `test_dirs` was expanded this mission, assert
`gate_selection.select_modules([<added_test_dir>/synthetic_test.py])` includes the owning module (test-path
routing) AND a synthetic path under the module's `roots` selects it (source routing). This proves per-PR
selection permanently, re-runnably, with zero net diff. WP03 also pastes one live `gate_selection.py` transcript
(source injection → module selected → shard red → revert) into the PR body as corroboration.

## 6. Marker-presence honesty for pop-(b) (priti F3) — permanent in WP04
Every reason naming a marker lane is backed by an actual marker in that tree (WP04 guard greps/ASTs).

## 7. Exclusions untouched + folded issues (SC-006, SC-008)
`git diff main` shows no change to `tests/specify_cli/cli/commands` or the 5 named-home entries. #4426's two
dirs decided; PR body carries `Fixes #4426` and `Fixes #4374`, links #4708/#2979 (closeout-owned; guards against
the PR-body-rewrite auto-close footgun).

## 8. Blast-radius
```bash
make test-fast
PYTHONPATH=src .venv/bin/python -m pytest tests/architectural/ -q -k "shard_registry or scrub or completion_manifest or out_of_matrix or lifted"
```
