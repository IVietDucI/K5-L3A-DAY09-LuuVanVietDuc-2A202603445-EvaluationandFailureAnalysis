"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, aggregate, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    required = [m['id'] for m in spec.get('metrics', []) if m['id'] in GRADERS]
    identities, memberships = [], []
    for side, report in [('PR', pr), ('baseline', base)]:
        if not isinstance(report, dict):
            problems.append(f'{side}: report must be a record')
            identities.append(set()); memberships.append({}); continue
        manifest = report.get('manifest') or {}
        if not isinstance(manifest, dict):
            problems.append(f'{side}: manifest must be a record'); manifest = {}
        if not isinstance(manifest.get('eval_set_sha'), str) or not manifest.get('eval_set_sha'):
            problems.append(f'{side}: missing eval_set_sha')
        rows, metrics = report.get('rows'), report.get('metrics')
        items, seeds = manifest.get('items'), manifest.get('seeds')
        valid = True
        if type(items) is not int or items < 1:
            problems.append(f'{side}: manifest items must be positive'); valid = False
        if not isinstance(seeds, list) or not seeds or any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds):
            problems.append(f'{side}: manifest seeds must be a nonempty unique integer list'); valid = False
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            problems.append(f'{side}: rows must be a list of records')
            identities.append(set()); memberships.append({}); continue
        if not isinstance(metrics, dict):
            problems.append(f'{side}: metrics missing'); metrics = {}; valid = False
        if report.get('evaluator_failures'):
            problems.append(f'{side}: evaluator_failures is nonempty')
        for name, value in metrics.items():
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value)):
                problems.append(f'{side}: nonfinite or invalid metric {name}')
        for name in required:
            if metrics.get(name) is None:
                problems.append(f'{side}: missing graded aggregate {name}')
        grid, tags, by_item = set(), {}, {}
        for index, row in enumerate(rows):
            item, seed = row.get('item_id'), row.get('seed')
            if not isinstance(item, str) or not item or type(seed) is not int:
                problems.append(f'{side}: invalid item/seed identity at row {index}'); valid = False; continue
            key = (item, seed)
            if key in grid:
                problems.append(f'{side}: duplicate item/seed {key}'); valid = False
            grid.add(key); by_item.setdefault(item, set()).add(seed)
            slices = row.get('slices', [])
            if not isinstance(slices, list) or any(not isinstance(t, str) for t in slices) or len(set(slices)) != len(slices):
                problems.append(f'{side}: invalid slice tags at {key}'); valid = False; slices = []
            current = frozenset(slices)
            if item in tags and tags[item] != current:
                problems.append(f'{side}: inconsistent slice membership across seeds for {item}'); valid = False
            tags[item] = current
            for name in required:
                if type(row.get(name)) is not bool:
                    problems.append(f'{side}: missing/invalid graded row value {name} at {key}'); valid = False
            if 'cost' in row and (isinstance(row['cost'], bool) or not isinstance(row['cost'], (int, float))
                                  or not math.isfinite(row['cost']) or row['cost'] < 0):
                problems.append(f'{side}: invalid/nonfinite row cost at {key}'); valid = False
        if valid:
            if len(rows) != items * len(seeds) or len(by_item) != items or any(s != set(seeds) for s in by_item.values()):
                problems.append(f'{side}: incomplete item x seed grid'); valid = False
        identities.append(grid); memberships.append(tags)
        if valid:
            # Minimal public fixtures need not include cost. Use placeholders only
            # for computing independent metrics; never certify an unavailable cost.
            cost_available = all(isinstance(r.get('cost'), (int, float)) and not isinstance(r.get('cost'), bool)
                                 and math.isfinite(r['cost']) and r['cost'] >= 0 for r in rows)
            prepared = [{**r, 'cost': r.get('cost', 0.0) if cost_available else 0.0} for r in rows]
            recomputed = aggregate(prepared, required, k_values=spec.get('pass_k', []))
            for name, expected in recomputed.items():
                if name not in metrics or (name == 'cost_per_success' and not cost_available):
                    continue
                # Derived reliability requires actual pass_rate inputs, not a
                # missing value converted into False by bool(None).
                if name not in required and name != 'cost_per_success' and not all(type(r.get('pass_rate')) is bool for r in rows):
                    continue
                value = metrics[name]
                if expected is None:
                    if value is not None: problems.append(f'{side}: inconsistent undefined aggregate {name}')
                elif not isinstance(value, (int, float)) or not math.isfinite(value) or not math.isclose(value, expected, rel_tol=1e-9, abs_tol=0.000051):
                    problems.append(f'{side}: aggregate {name} inconsistent with rows (reported {value}, recomputed {expected})')
    if identities[0] != identities[1]:
        problems.append('PR/baseline item/seed identities differ')
    if memberships[0] != memberships[1]:
        problems.append('PR/baseline slice membership differs')
    if base_spec and base_spec.get('eval_set_version') == spec.get('eval_set_version'):
        for kind, key in [('metrics', lambda r: r['id']), ('slices', lambda r: (r['name'], r['metric']))]:
            old = {key(r): r for r in base_spec.get(kind, [])}
            new = {key(r): r for r in spec.get(kind, [])}
            for identity, protection in old.items():
                label = f'ratchet {kind} {identity}'
                if identity not in new:
                    problems.append(f'{label}: removed protection'); continue
                candidate = new[identity]
                if protection.get('blocking') and not candidate.get('blocking'):
                    problems.append(f'{label}: blocking changed to advisory')
                old_limits = protection.get('threshold', {}) if kind == 'metrics' else protection
                new_limits = candidate.get('threshold', {}) if kind == 'metrics' else candidate
                for field in ('min', 'max', 'max_increase'):
                    if field not in old_limits: continue
                    value = new_limits.get(field)
                    if not isinstance(value, (int, float)) or not math.isfinite(value):
                        problems.append(f'{label}: {field} removed/invalid')
                    elif (field == 'min' and value < old_limits[field]) or (field != 'min' and value > old_limits[field]):
                        problems.append(f'{label}: {field} loosened')
                if old_limits.get('no_significant_drop') and not new_limits.get('no_significant_drop'):
                    problems.append(f'{label}: no_significant_drop removed')
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get('bootstrap', {})
    for rule in spec.get('slices', []):
        name, metric = rule['name'], rule['metric']
        identifier = f'slice:{name}/{metric}'
        try:
            a, b = per_item(pr, metric, name), per_item(base, metric, name)
        except (TypeError, ValueError, KeyError):
            a, b = {}, {}
        failures, note = [], ''
        def evidence(report):
            selected = [r for r in report['rows'] if name in (r.get('slices') or [])]
            ids = {(r['item_id'], r['seed']) for r in selected}
            valid = all(isinstance(r.get(metric), (bool, int, float)) and math.isfinite(r[metric]) for r in selected)
            return ids, valid
        ids_a, valid_a = evidence(pr); ids_b, valid_b = evidence(base)
        if not a or not b or set(a) != set(b) or ids_a != ids_b or not valid_a or not valid_b:
            failures.append('missing or incomparable slice evidence (no partial intersection allowed)')
            value = baseline = delta = None
        else:
            keys = sorted(a)
            value, baseline = sum(a.values()) / len(a), sum(b.values()) / len(b)
            delta = value - baseline
            if 'min' in rule and value < rule['min']:
                failures.append(f'floor {value:.6f} < {rule["min"]}')
            if rule.get('no_significant_drop'):
                try:
                    delta, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                        n_resamples=bs.get('n_resamples', 1000), rng=bs.get('rng', 2027), confidence=bs.get('confidence', 0.95))
                    note = f'CI [{lo:+.6f}, {hi:+.6f}]'
                    if hi < 0: failures.append('paired CI entirely below zero')
                except ValueError as exc:
                    failures.append(f'incomparable paired evidence: {exc}')
        if failures and rule.get('blocking'): blocked.append(identifier)
        verdict = 'BLOCK' if failures and rule.get('blocking') else ('warn' if failures else 'ok')
        lines.append(f'  {identifier} n={len(a)} PR={value} baseline={baseline} delta={delta} {note} {verdict}: {"; ".join(failures) or "conditions met"}')
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    # Integrity may already have rejected a missing/malformed manifest or report.
    # Rendering that diagnostic must not dereference the rejected structure.
    pr_record = pr if isinstance(pr, dict) else {}
    base_record = base if isinstance(base, dict) else {}
    manifest = pr_record.get('manifest')
    manifest = manifest if isinstance(manifest, dict) else {}
    print(f"gate: PR {pr_record.get('run_id', '<missing>')} vs main {base_record.get('run_id', '<missing>')} · eval set {manifest.get('eval_set_sha', '<missing>')}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
