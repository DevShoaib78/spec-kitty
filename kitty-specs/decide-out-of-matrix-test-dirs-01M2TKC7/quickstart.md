# Quickstart: resolve one out-of-matrix tree

Worked example of the two most common dispositions.

## A. Promote a tree with unique behavioral coverage (Disposition 1a)
Say `tests/specify_cli/merge` genuinely tests merge behavior not in `tests/merge`.
1. Edit `.github/ci-module-registry.yml`, `merge` row — add explicit `test_dirs`:
   ```yaml
   - module: merge
     roots: [src/specify_cli/merge/**]
     cov_targets: [specify_cli.merge]
     tier: standard
     shard_count: 1          # re-decide from measured durations below
     test_dirs:
     - tests/merge           # materialize the former fallback
     - tests/specify_cli/merge
   ```
   …and remove `tests/specify_cli/merge` from `out_of_matrix_test_dirs`.
2. Measure:
   ```bash
   python scripts/ci/capture_shard_timings.py --module merge --write
   ```
   Confirm `len(module_test_durations["merge"]) == module_test_count["merge"]`.
3. Choose `shard_count` by greedy-LPT so within-module skew ≤20% and serial wall ≤30-min budget; note it in a
   YAML comment.
4. Verify:
   ```bash
   PYTHONPATH=src .venv/bin/python -m pytest tests/architectural/test_module_shard_registry.py -q
   ```

## B. Keep a tree out-of-matrix with a sharpened reason (Disposition 3)
Say `tests/specify_cli/<x>` duplicates coverage already in its primary mirror.
- Rewrite its `out_of_matrix` reason to a decision, e.g.:
  > Behavioral coverage is a strict subset of the `<module>` row's primary mirror `tests/<module>` (same
  > module under test); this secondary tree adds no path not already lane-selected, so it stays out-of-matrix
  > by decision. (spec-kitty#4374)
- Run the guard; it must stay green (still recorded once).

## C. Lift a single invariant (Disposition 2, the #4715 pattern)
- Add `tests/architectural/test_<x>_<invariant>.py` with `pytestmark = [pytest.mark.architectural]` asserting
  the one drift-prone fact; sharpen the tree's reason to name that gate.

## Verify everything
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/architectural/test_module_shard_registry.py -q
make test-fast   # baseline blast radius
```
