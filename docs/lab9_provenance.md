# Lab 9 provenance (M0)

> Dated M0 record: 2026-11-17. Original environment, branch/remote descriptions, paths and Lab 8 results below describe that historical stage. Current canonical repository: `D:\VINAI20K\C_17112026\K5-L3A-DAY09-LuuVanVietDuc-2A202603445-EvaluationandFailureAnalysis`. See [migration record](lab9_migration.md), [current eval card](eval_card.md), and [individual report](lab9_individual_report.md). Core publication is at d480122f0ed3066e3102e47633af5330770e84fb; local Advanced changes remain unpublished.

Individual Day 9 work (Evaluation & Failure Analysis) built on the frozen team Lab 8 submission.

| Field | Value |
|---|---|
| Learner | Luu Van Viet Duc |
| Student ID | 2A202603445 |
| Class | L3A |
| Assignment mode | Individual (assigned to this learner). Note: the public starter `SUBMISSION.md` still describes a team PR from `starter/d09` to `main`. No official individual naming rule exists, so none is assumed here. |

## Sources

| Source | URL | Commit |
|---|---|---|
| Team Lab 8 (frozen base) | https://github.com/congtinhx/K5-L3A-DAY08-Khongcoten-FromWorkflowsToAgents.git | `08dedb4032a13b9cefd9ab3ad891abbee0ef7ad0` |
| Lab 9 overlay starter | https://github.com/VinUni-AI20k/K5-Day9-Evaluation-and-Failure-Analysis.git | `d1b9471540727d693c9eb392667b9f0d8a998bf5` |

- Local `main` and branch `starter/d09` both start at the frozen Lab 8 commit. The inherited remote is renamed `lab8-source` (source only, never pushed to). No personal remote is configured yet.
- The starter is an **overlay**. Only the contents of its `src/`, `docs/` and `.github/` were copied (32 files, no collisions, byte-identical). The starter's root `README.md`, `CHECKPOINTS.md`, `RUBRIC.md`, `SUBMISSION.md` and `.gitignore` were **not** copied. The Lab 8 `.github/workflows/ci.yml` is kept and `eval-gate.yml` is added.

## Local paths

| Role | Path |
|---|---|
| Individual Lab 9 repo | `D:\VINAI20K\C_17112026\K5-L3A-DAY09-LuuVanVietDuc-2A202603445-Evaluation-and-Failure-Analysis` |
| Starter checkout (read-only reference) | `D:\VINAI20K\C_17112026\lab9-starter` |
| M0 evidence (outside repo) | `D:\VINAI20K\C_17112026\M0_evidence` |
| Original Lab 8 working copy (not modified) | `D:\VINAI20K\C_16112026\K5-L3A-DAY08-Khongcoten-FromWorkflowsToAgents` |

## Historical Lab 8 results (frozen, not re-run)

These results come from the team's Lab 8 submission. They are kept as-is. They are not targets for this run.

- Selected shape: **workflow**.
- Official benchmark: 14 public claims × seeds 11, 22, 33, 44, 55 per shape. workflow, single and orchestrator each scored 70/70. swarm scored **69/70**.
- The failing swarm trial is **C-002 seed 55**. The DB says the order was 2 days late, but the ticket claims 5 days. Swarm resolved the claim and refunded 20,000 VND when it should have denied it. Historical reports keep this failure.
- Reported integration checks: 75 default tests passed and 248 public matrix tests passed. The official host/swarm crash suite passed 20/20.
- `src/reports/benchmark.json`, `crash.json` and `ablation_orchestrator_vs_swarm.json` are unchanged and were not regenerated.

## M0 environment (actual, 2026-11-17)

- Interpreter: a new venv at `src\.venv`, created from Python **3.13.17** (`C:\Users\Viet Duc\AppData\Local\Programs\Python\Python313`). Yesterday's venv was not reused.
- `python -m pip install -r requirements.txt -r requirements-lab9.txt` exited 0, and `pip check` found no broken requirements. Key versions: pydantic-evals 2.68.0, numpy 2.5.5, scipy 1.18.1, pytest 8.4.2, PyYAML 6.0.3.

## M0 checks (actual, run from `src/` with the venv interpreter)

| Command | Exit | Result |
|---|---|---|
| `python -m lab9.smoke` | 0 | `M0 PASS` |
| `python -m lab9.evalset --build` | 0 | 14 items in `data/eval/eval_set_v1.jsonl`, 14 labels in a separate `data/eval/labels_v1.json`, all `failure_modes` empty (expected at M0) |
| `python -m pytest -q` | 0 | 78 passed, 271 deselected (75 Lab 8 default + 3 unmarked Lab 9 evalset tests) |
| `python -m pytest -q tests/test_lab9_evalset.py -o addopts=` | 0 | 3 passed |
| `python -m lab9.trace_case --shape swarm --claim C-002 --seed 55` | 0 | Trial verdict **FAIL**: status resolved instead of denied, refund 20000 instead of 0. This reproduces the historical agent failure. It is not an environment failure. |
| `python -m lab9.trace_case --shape fixed --claim C-002 --seed 55` | 0 | Trial verdict **PASS**: denied, refund 0 |

`python -m lab9.evalset --check` currently reports 14 problems (empty `failure_modes`). This is expected until M1.
