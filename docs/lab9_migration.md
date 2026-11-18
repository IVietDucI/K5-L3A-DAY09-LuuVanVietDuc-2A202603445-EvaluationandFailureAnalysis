# Lab 9 M0/M1 migration record

Migration date: 2026-11-17 (Asia/Saigon). Student: Luu Van Viet Duc, 2A202603445, L3A.

This is a migration of previously completed M0 and corrected M1 work. It does not implement M2 or later. The original work and its historical provenance remain attributed to their original working copy. In particular, `docs/lab9_provenance.md` and `docs/lab9_m1_notes.md` were copied byte for byte; their historical paths and environment descriptions were not rewritten to imply that work originally happened here.

## Sources and canonical working copy

| Role | URL or path | Commit |
|---|---|---|
| Personal Lab 9 fork, cloned as origin | https://github.com/IVietDucI/K5-L3A-DAY09-LuuVanVietDuc-2A202603445-EvaluationandFailureAnalysis.git | `d1b9471540727d693c9eb392667b9f0d8a998bf5` |
| Lab 9 upstream | https://github.com/VinUni-AI20k/K5-Day9-Evaluation-and-Failure-Analysis.git | `d1b9471540727d693c9eb392667b9f0d8a998bf5` |
| Frozen Lab 8 team base | https://github.com/congtinhx/K5-L3A-DAY08-Khongcoten-FromWorkflowsToAgents.git | `08dedb4032a13b9cefd9ab3ad891abbee0ef7ad0` |
| Migration source, preserved | `D:\VINAI20K\C_17112026\K5-L3A-DAY09-LuuVanVietDuc-2A202603445-Evaluation-and-Failure-Analysis` | source HEAD is the frozen Lab 8 commit, branch `starter/d09`, with completed M0/M1 assignment files untracked |
| New canonical repository | `D:\VINAI20K\C_17112026\K5-L3A-DAY09-LuuVanVietDuc-2A202603445-EvaluationandFailureAnalysis` | fork HEAD, local `main`, and `origin/main` remain at the reviewed Lab 9 commit |
| Read-only starter reference | `D:\VINAI20K\C_17112026\lab9-starter` | reviewed Lab 9 commit |

The destination was absent before migration and was genuinely cloned from the personal fork. The clone's `.git` and history were preserved. `starter/d09` was created from its `main`; the reviewed Lab 9 commit is an ancestor of HEAD (indeed, HEAD equals that commit). There were no unexpected newer commits. The existing upstream remote was verified to point to the URL above. The Lab 8 commit identifies the imported snapshot; this migration does not graft Lab 8 Git history into the fork.

## Explicit import decisions

The original 94 Lab 8 paths were obtained with `git --no-optional-locks ls-tree -r --name-only 08dedb4032a13b9cefd9ab3ad891abbee0ef7ad0` in the source repository. Read-only Git inspections used `--no-optional-locks`; sandbox ownership checks were handled with command-scoped `-c safe.directory=<exact repository path>`, without changing global Git configuration.

An explicit 102-entry import manifest was recorded before copying:

- 89 original Lab 8 files imported at their original relative paths, including `src/lab8`, runtime/data/config, `src/requirements.txt`, `src/pytest.ini`, `src/harness_map.yaml`, original tests, supporting files, all three historical report JSONs, and `.github/workflows/ci.yml`.
- Four Lab 8 root documents archived at `docs/lab8_source_root/README.md`, `CHECKPOINTS.md`, `RUBRIC.md`, and `SUBMISSION.md`. Their archive bytes equal the source. The destination's Lab 9 versions remain byte-identical at the root.
- The Lab 8 `.gitignore` archived byte for byte at `docs/lab8_source_root/gitignore.lab8.txt`.
- Eight completed M0/M1 files reused byte for byte: `src/lab9/evalset.py`, `src/data/eval/eval_set_v1.jsonl`, `src/data/eval/labels_v1.json`, `docs/failure_taxonomy.md`, `docs/trace_case.md`, `docs/lab9_m1_notes.md`, `src/tests/test_lab9_m1.py`, and `docs/lab9_provenance.md`.

Original authorship in `TEAM.md` and `report/team/` is preserved. The 131 source assignment files match the prior corrected M1 inventory. All 32 supplied Lab 9 overlay files were compared with the reviewed starter before importing: 29 match exactly; the only three differences are the completed M1 changes to `docs/failure_taxonomy.md`, `docs/trace_case.md`, and `src/lab9/evalset.py`. Supplied Lab 9 tests, variants, graders, stats, gates, and metric specifications remain unchanged.

The root `.gitignore` intentionally merges the useful Lab 9 rules with protections for `.env` files, virtual environments, Python caches, raw runtime traces, temporary SQLite databases and their sidecars, `student_drop`, instructor-only packs, and hidden grading output. The starter's blanket `src/reports/` rule was removed so required historical and future submission reports can be included. Eighteen exclusion probes and six report-inclusion probes passed. No `.git`, environments, caches, source runtime traces, temporary databases, secrets, instructor packs, or external evidence directories were copied into the repository.

Corrected M1 semantics remain unchanged: FM-04 uses `model/prompt`, FM-05 uses `tool/schema`, FM-02 distinguishes false resolved status after denial from actual unauthorized money movement, and C-009 has only `["FM-01"]`. Official-anchor results remain unverified.

## New environment and actual validation

The new `src/.venv` was created with the verified base installation `C:\Users\Viet Duc\AppData\Local\Programs\Python\Python313\python.exe`, Python **3.13.17**. The source virtual environment was neither copied nor modified or installed into.

New interpreter: `D:\VINAI20K\C_17112026\K5-L3A-DAY09-LuuVanVietDuc-2A202603445-EvaluationandFailureAnalysis\src\.venv\Scripts\python.exe`.

Both requirements files are unchanged. Installation used the destination interpreter explicitly:

`python -m pip install --disable-pip-version-check --no-cache-dir --retries 0 --timeout 30 -r requirements.txt -r requirements-lab9.txt`

Installation, `python -m pip check`, and `python -m pip freeze` each exited 0. A package inventory is in the external migration evidence.

All validation commands below ran from the destination `src` with the new destination interpreter:

| Command | Exit | Actual result |
|---|---|---|
| `python -c "import sys; print(sys.executable); print(sys.version)"` | 0 | Destination interpreter, Python 3.13.17 |
| `python -m lab9.smoke` | 0 | M0 PASS |
| `python -m lab9.evalset --check` | 0 | `eval set d2d43350c505: 0 problem(s)`; 14 items, 14 separate labels |
| `python -m pytest -q tests/test_lab9_evalset.py -o addopts=` | 0 | 3 passed |
| `python -m pytest -q tests/test_lab9_m1.py -m student -o addopts=` | 0 | 3 passed |
| `python -m pytest -q` | 0 | 78 passed, 274 deselected |
| `python -m lab9.trace_case --shape swarm --claim C-002 --seed 55` | 0 | Trial **FAIL**, `status resolved != denied`; resolved, refund 20000, refund_count 1; expected denied/0 |
| `python -m lab9.trace_case --shape fixed --claim C-002 --seed 55` | 0 | Trial **PASS**; denied, refund 0, refund_count 0 |

The diagnostic CLI returning 0 is distinct from the trial verdict. The swarm failure is intentionally preserved. The eval set was checked in place and was not rebuilt. No baseline/v2 reports were generated.

The first sandbox clone attempt could not reach GitHub; the authorized clone succeeded with network access. The first eval-set pytest invocation exited 1 with three setup errors because a pre-existing user-owned pytest temporary directory was inaccessible. A fresh external temporary directory was selected through `TEMP`/`TMP`, and the unchanged command passed with three tests. A subsequent evidence-wrapper console encoding error occurred after the fixed trace CLI had already exited 0; the UTF-8 log contained its complete PASS output. These failed attempts remain in the new evidence and were not overwritten. No project fix was required.

## Preservation audit and final working state

- Source project files (including 94 tracked and 37 existing untracked assignment files), source Git metadata, and source Git status remain unchanged. Source caches and runtime files outside its venv were also hash-compared. The source venv was only used to inspect its base Python and run evidence helpers with bytecode writes disabled.
- All 94 original Lab 8 paths are accounted for: 89 same-path copies and five byte-identical archived root files. Historical labels and all three report JSONs match the source; none were regenerated.
- All eight completed M0/M1 files match the source byte for byte. The read-only starter and all 68 pre-existing evidence files remain unchanged.
- Destination deliverables are exactly the fork starter plus the explicit imports, intentionally merged `.gitignore`, and this migration note. Environments, caches, and generated runtime traces are ignored, outside the deliverable set. No credentials or instructor packs were imported.
- Final expected status: four unstaged tracked modifications (`.gitignore`, `docs/failure_taxonomy.md`, `docs/trace_case.md`, `src/lab9/evalset.py`) and 100 intended untracked files including this note; zero staged files. Fork `main`, `origin/main`, and HEAD remain intact. No staging, commit, push, PR, or M2 implementation was performed.

## Evidence and activation

New migration evidence only: `D:\VINAI20K\C_17112026\M1_evidence\migration_20261117_180856_4fb1d45f`.

This folder contains the source inventories, 102-entry import manifest, supplied-file comparison, complete commands and exit codes, validation outputs, preservation audits, and the final full Git status. Earlier evidence and inventories were not overwritten.

```powershell
Set-Location -LiteralPath 'D:\VINAI20K\C_17112026\K5-L3A-DAY09-LuuVanVietDuc-2A202603445-EvaluationandFailureAnalysis\src'
. .\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable); print(sys.version)"
```
