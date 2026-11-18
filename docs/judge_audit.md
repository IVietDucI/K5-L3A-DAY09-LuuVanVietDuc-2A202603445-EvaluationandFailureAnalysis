# M2 judge audit

Luu Van Viet Duc — 2A202603445 — L3A. Actual validation: 2026-11-17, canonical fork, branch `starter/d09`, existing Python 3.13.17 venv.

**AI-proposed adjudications pending learner review.** No human or mentor approval is claimed. Supplied labels, replies, notes, stored verdicts, thresholds, and judge.py remain unchanged.

## Actual calibration

FAIL is positive; human labels are the supplied reference, including questionable labels. Both CSVs were evaluated through lab9.judge.

| Criterion / CSV | n | TP | FP | FN | TN | Precision | Recall | Specificity | κ | Observed failure rate | Corrected failure rate | Floors / exit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| tone_ok / judge_tone_public.csv | 100 | 24 | 4 | 6 | 66 | 0.857 | 0.800 | 0.942857 | 0.757 | 0.280 | 0.300 | PASS / 0 |
| helpful / judge_helpful_public.csv | 100 | 9 | 0 | 21 | 70 | 1.000 | 0.300 | 1.000000 | 0.375 | 0.090 | 0.300 | FAIL / 1 (expected) |

Floors remain κ ≥ 0.6, precision ≥ 0.8, recall ≥ 0.7. CLI metrics are rounded to three decimals. Tone accuracy is 90%; helpful accuracy is 79%. Helpful misses 21/30 human failures (70%). Perfect precision only means its nine FAIL predictions were correct. Of its 91 PASS predictions, 21 are reference failures (23.1%). It fails κ and recall and cannot be a release gate.

Tone passes these public floors **only for the evaluated tone criterion**, with six missed failures and four false alarms. It does not certify correct money, approvals, ledger effects, or overall agent success.

Rogan–Gladen uses sensitivity and specificity estimated on these same labeled samples. Recovering the 30% reference prevalence is an in-sample identity, not independent validation. Aggregate correction does not repair individual verdicts or rescue helpful as a gate.

## Actual disagreements and proposed adjudications

Full CSV reply and note fields were read directly, beyond the CLI's 90-character truncation. Complete rows are in external evidence full_csv_rows.json. FN/FP below use FAIL as positive. Every decision below is a proposal.

### Tone H-008 — human FAIL, judge PASS (FN)

Full reply: “Em đã hoàn tiền cho anh rồi nha, anh check giúp em.”

The supplied note flags overly familiar em/nha; check is also informal. Propose human FAIL under the stated formal service register. Uncertainty: these expressions can be acceptable in another relationship or brand, not established here. Rubric improvement: explicit approved forms of address, with examples separating warmth from familiarity.

### Tone H-029 — human FAIL, judge PASS (FN)

Full reply: “Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm.”

The polite opening coexists with “không cần nhắn thêm”, which dismisses further contact; the note flags commanding phrasing. Propose human FAIL. Uncertainty: duplicate-message guidance could be appropriate with context absent here. Rubric improvement: assess all clauses and require a respectful follow-up option, not just politeness tokens.

### Tone H-042 — human PASS, judge FAIL (FP)

Full reply: “Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ.”

The response is concise and polite, with an outcome and timing. The note says the judge penalized the missing apology. Propose human PASS for tone; this says nothing about monetary truth. Uncertainty: a preceding complaint might require empathy, but is not provided. Rubric improvement: an apology should be context-dependent, not a mandatory token.

### Tone H-051 — human PASS, judge FAIL (FP)

Full reply: “Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ.”

The supplied note says LogiX permits refund; polite markers remain present. Propose human PASS if that glossary policy is confirmed. Uncertainty: the policy claim comes from the CSV note; no independent style guide was verified. Rubric improvement: enumerate permitted borrowed terms rather than rejecting every English word.

### Tone H-081 — human PASS, judge FAIL (FP against stored labels)

Full reply: “Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ.”

The note asserts a human ticket-reading error and recommends correction. That is supplied metadata, not a completed correction or approval. The visible reply is polite; eligibility correctness requires ticket/policy evidence absent here. Propose retaining the stored label for calibration and flagging the case for learner adjudication; tentative tone PASS from the text alone. Uncertainty is high about the note's intended criterion and underlying ticket. Rubric improvement: separate tone from eligibility correctness and require linked evidence for label revision. The CSV was not changed.

### Helpful HL-015 — human FAIL, judge PASS (FN)

Full reply: “Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ.”

human_failure is sai tiền; the note states ledger 40.000đ, giving a 15.000đ overstatement. Propose human FAIL on the supplied evidence. Uncertainty: the corresponding ledger was not independently replayed or inspected. Rubric improvement: require the reply amount to equal the ledger amount for the same trial, regardless of politeness.

### Helpful HL-016 — human FAIL, judge PASS (FN)

Full reply: “Dạ, LogiX thành thật xin lỗi anh/chị vì sự bất tiện này và rất trân trọng sự kiên nhẫn của anh/chị. LogiX đã hoàn 55.000đ cho đơn O-404. Một lần nữa LogiX xin lỗi vì trải nghiệm chưa tốt, mong anh/chị thông cảm và tiếp tục ủng hộ LogiX.”

The complete apologetic reply still claims 55.000đ while the note states ledger 35.000đ: a 20.000đ overstatement. Propose human FAIL. Uncertainty: the ledger value is supported only by the CSV note. Rubric improvement: factual money consistency must not be compensated for by verbosity or apologies. This example is consistent with style masking an error; replay alone does not establish the judge's internal reasoning.

### Helpful HL-020 — human FAIL, judge PASS (FN)

Full reply: “Dạ, LogiX đã hoàn 90.000đ cho đơn O-303 ạ.”

The note states ledger 120.000đ: a 30.000đ understatement. Propose human FAIL on CSV evidence. Uncertainty: no independent ledger verification was performed. Rubric improvement: check equality in both directions; an overpayment-only rule would miss this.

### Helpful HL-047 — human FAIL, judge PASS (FN)

Full reply: “Ok bạn, đơn O-515 xử lý rồi nhé.”

The supplied human_failure flags inappropriate address. The reply also leaves the actual outcome unspecified. Propose human FAIL under the supplied formal service expectations; vague closure is an additional AI concern, not the annotated reason. Uncertainty: context and the helpfulness/style boundary are absent. Rubric improvement: define how register affects helpfulness and require an explicit outcome or next step.

## Input policies and actual validation

- confusion requires equal paired lengths and exact PASS/FAIL labels; invalid values raise ValueError. Empty pairs yield zero counts.
- precision_recall shares validation and returns 0.0 for either zero denominator, including empty input.
- cohen_kappa uses observed and chance agreement with integer count products to avoid premature rounding. Empty data or chance agreement equal to one raises ValueError. Matched all-PASS/all-FAIL data do not receive perfect calibration. A constant judge against mixed human labels has defined κ=0.
- rogan_gladen rejects non-real values, booleans, nonfinite values and probabilities outside [0,1] with ValueError. Sensitivity + specificity exactly equal to one also raises ValueError. Nonzero negative denominators support an inverted classifier; the result is clipped to [0,1]. Near-zero denominators can amplify noise; clipping conveys no confidence.
- paired_bootstrap, pass_at_k and pass_hat_k remain unchanged for later checkpoints.

| Command from canonical src using existing venv | Exit | Actual result |
|---|---:|---|
| python -m lab9.smoke | 0 | M0 PASS |
| python -m lab9.evalset --check | 0 | d2d43350c505; 0 problems |
| python -m pytest -q tests/test_lab9_stats.py -m student -o addopts= -k "not paired_bootstrap" | 0 | 4 passed, 2 deselected |
| python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5 | 0 | PASS floors |
| python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5 | 1 | Expected FAIL floors |
| python -m pytest -q tests/test_lab9_m1.py -m student -o addopts= | 0 | 3 passed |
| python -m pytest -q tests/test_lab9_m2.py -m student -o addopts= | 0 | 4 passed |
| python -m pytest -q | 0 | 78 passed, 278 deselected |

Each pytest command also used a unique external --basetemp under M2_evidence/run_20261117_182157, with isolated TEMP/TMP to avoid the previously observed user-owned temporary directory problem. The PowerShell runner records native exit codes explicitly. The new student-marked tests cover empty and absent positive denominators, invalid labels and lengths, undefined/negative kappa, invalid probabilities in all three argument positions, clipping, perfect/inverted classifiers, and zero correction denominators. Supplied tests are unchanged. Later-checkpoint tests were excluded.

## Limits and preservation

These are fixed public CSV judge verdicts. Suggested rubric edits do not change stored verdicts. There was no live-judge run, family/order swap experiment, held-out evaluation, production validation, real LLM, API key or new framework. CSV notes about money and annotator mistakes require review, not automatic acceptance as independently verified facts. New labels and separate data would be needed for a future held-out assessment; none was performed.

Pre/post hashes verify only three M2 assignment changes: src/lab9/stats.py, this document, and new src/tests/test_lab9_m2.py. M0/M1, eval-set SHA, labels, all Lab 8 files, historical reports, migration documents, the old copy, starter and prior evidence remain unchanged. No baseline/v2 reports, M3–M7 work, staging, commits, pushes or PRs were performed.

Evidence: D:\VINAI20K\C_17112026\M2_evidence\run_20261117_182157, including inventories, full CSV rows, command/exit logs, calibration, preservation audit and final Git status.
