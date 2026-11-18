"""M1 regression tests for FM-03 (ticket_trust) and deterministic evalset tagging.

Run: python -m pytest -q tests/test_lab9_m1.py -m student -o addopts=
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import pytest

from lab8.db import connect, init_store
from lab8.metrics import ledger_snapshot, trial_pass, unexpected_ledger_rows
from lab8.shapes import SHAPES
from lab9 import evalset, variants
from tests.conftest import BY_ID, CLAIMS, WORLD

pytestmark = pytest.mark.student


def _run_with_oracle(shape: str, claim_id: str, seed: int, tmp_path: Path) -> dict[str, Any]:
    """Run one shape trial on a fresh isolated SQLite store and evaluate the shared oracle."""
    from pydantic_evals.evaluators import EvaluatorContext
    from lab9.graders import DbFactKept

    variants.register()
    store = tmp_path / f"{shape}-{claim_id}-s{seed}.sqlite"
    init_store(store, WORLD, CLAIMS).close()
    started_at = time.time()
    result = SHAPES[shape](claim_id, seed=seed, store_path=str(store))
    payload = result.as_dict()
    conn = connect(store)
    try:
        passed, reason = trial_pass(payload, BY_ID[claim_id]["expected"], conn, started_at=started_at)
        snap = ledger_snapshot(conn, claim_id)
        unexpected = unexpected_ledger_rows(conn, claim_id)
    finally:
        conn.close()

    trace_body = json.loads(Path(payload["trace_path"]).read_text(encoding="utf-8"))
    events = trace_body["events"]
    trial = {
        "result": payload,
        "snapshot": snap,
        "unexpected_rows": unexpected,
        "events": events,
        "lab8_pass": passed,
        "lab8_reason": reason,
    }
    ctx = EvaluatorContext(
        name=f"{shape}:{claim_id}@{seed}",
        inputs={"claim_id": claim_id, "seed": seed},
        metadata=None,
        expected_output=BY_ID[claim_id]["expected"],
        output=trial,
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )
    db_fact = DbFactKept().evaluate(ctx)
    return {
        "passed": passed,
        "reason": reason,
        "result": payload,
        "snapshot": snap,
        "unexpected_rows": unexpected,
        "events": events,
        "db_fact_kept": bool(db_fact.value),
    }


def test_c002_seed55_ticket_trust_regression_and_fixed_control(tmp_path: Path) -> None:
    """Same oracle must reject swarm C-002@55 (FM-03) and accept fixed C-002@55."""
    buggy = _run_with_oracle("swarm", "C-002", 55, tmp_path)
    assert buggy["passed"] is False
    assert buggy["reason"] == "status resolved != denied"
    assert buggy["result"]["status"] == "resolved"
    assert buggy["result"]["proposal_amount"] == 20000
    assert buggy["snapshot"]["refund_vnd"] == 20000
    assert buggy["snapshot"]["refund_count"] == 1
    assert buggy["unexpected_rows"] == 0
    # 1-based step 3 is the first wrong event: ticket delay (5) overwrites DB delay (2).
    assert buggy["events"][2]["kind"] == "model_override"
    assert buggy["events"][2]["payload"] == {"delay_days": 5}
    assert buggy["db_fact_kept"] is False

    control = _run_with_oracle("fixed", "C-002", 55, tmp_path)
    assert control["passed"] is True, control["reason"]
    assert control["reason"] == "ok"
    assert control["result"]["status"] == "denied"
    assert control["result"]["proposal_amount"] == 0
    assert control["snapshot"]["refund_vnd"] == 0
    assert control["snapshot"]["refund_count"] == 0
    assert control["unexpected_rows"] == 0
    assert not any(ev.get("kind") == "model_override" for ev in control["events"])
    assert control["db_fact_kept"] is True


def test_seeded_regression_c002_seed11_and_fixed_control(tmp_path: Path) -> None:
    """Same oracle must reject seeded_regression C-002@11 (FM-03) and accept fixed C-002@11."""
    buggy = _run_with_oracle("seeded_regression", "C-002", 11, tmp_path)
    assert buggy["passed"] is False
    assert buggy["reason"] == "status resolved != denied"
    assert buggy["result"]["status"] == "resolved"
    assert buggy["result"]["proposal_amount"] == 20000
    assert buggy["snapshot"]["refund_vnd"] == 20000
    assert buggy["snapshot"]["refund_count"] == 1
    assert buggy["events"][2]["kind"] == "model_override"
    assert buggy["events"][2]["payload"] == {"delay_days": 5}
    assert buggy["db_fact_kept"] is False

    control = _run_with_oracle("fixed", "C-002", 11, tmp_path)
    assert control["passed"] is True, control["reason"]
    assert control["result"]["status"] == "denied"
    assert control["snapshot"]["refund_vnd"] == 0
    assert control["snapshot"]["refund_count"] == 0
    assert control["db_fact_kept"] is True


def test_m1_evalset_build_and_check_isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """evalset.build() deterministically writes 14 tagged items with separate labels in an isolated dir."""
    src_claims = Path(__file__).resolve().parents[1] / "data" / "public_claims.jsonl"
    isolated_source = tmp_path / "data" / "public_claims.jsonl"
    isolated_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_claims, isolated_source)

    monkeypatch.chdir(tmp_path)
    n_items, n_labels = evalset.build()
    assert (n_items, n_labels) == (14, 14)
    assert evalset.check() == []

    items = evalset.load_jsonl(tmp_path / "data" / "eval" / "eval_set_v1.jsonl")
    labels = json.loads((tmp_path / "data" / "eval" / "labels_v1.json").read_text(encoding="utf-8"))
    assert len(items) == 14
    assert len(labels) == 14
    assert all(item["failure_modes"] for item in items)
    assert all("expected" not in item and "label" not in item for item in items)

    e002 = next(item for item in items if item["item_id"] == "E-002")
    assert e002["claim_id"] == "C-002"
    assert e002["failure_modes"] == ["FM-03"]
    assert e002["provenance"]["from_trace"] == "R-swarm-C-002-s55"
