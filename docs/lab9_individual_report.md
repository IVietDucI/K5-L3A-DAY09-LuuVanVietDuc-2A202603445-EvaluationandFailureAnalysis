# Báo cáo cá nhân Lab 9 — Evaluation and Failure Analysis

**Lưu Văn Việt Đức**
**MSSV: 2A202603445**
**Lớp: L3A**

## 1. Mục tiêu và nguồn kế thừa

Lab 9 xây dựng quy trình đánh giá tác tử hoàn tiền LogiX-VN: mô tả failure mode, kiểm định bộ chấm, đối chiếu trajectory và ngăn hồi quy bằng gate. Phạm vi là bài tập offline với MockLLM, không phải triển khai dịch vụ thực tế.

Nguồn Lab 8 là repository nhóm `congtinhx/K5-L3A-DAY08-Khongcoten-FromWorkflowsToAgents`, đóng băng tại `08dedb4032a13b9cefd9ab3ad891abbee0ef7ad0`. Lựa chọn workflow và báo cáo lịch sử được giữ nguyên. Benchmark swarm đạt 69/70, với lỗi C-002@55 được bảo toàn thay vì chỉnh dữ liệu để đạt điểm tuyệt đối. Repository Lab 9 cá nhân kế thừa starter tại `d1b9471540727d693c9eb392667b9f0d8a998bf5`; quá trình chuyển thư mục và nguồn gốc có trong [migration](lab9_migration.md) và [provenance](lab9_provenance.md).

## 2. Công việc M0–M7

| Mốc | Nội dung thực hiện | Bằng chứng | Kết quả |
|---|---|---|---|
| M0 | Nhập phụ thuộc Lab 8, tạo môi trường Python 3.13.17, smoke | [Provenance](lab9_provenance.md) | Chạy offline được |
| M1 | Taxonomy, ánh xạ và tách nhãn | [Taxonomy](failure_taxonomy.md), [trace](trace_case.md) | v1 có 14 item; check sạch |
| M2 | Confusion, precision/recall, kappa, Rogan–Gladen | [Judge audit](judge_audit.md) | Tone đạt, helpful bị loại |
| M3 | Chấm approval, ledger, proposal và reply | [Ghi chú M3](lab9_m3_notes.md) | Giải thích 20/20 lỗi, 0/70 báo nhầm |
| M4 | Paired bootstrap, baseline swarm và gate | [Eval card](eval_card.md) | Swarm/fixed qua, regression bị chặn |
| M5 | Gói v2, ánh xạ cơ chế và slice | [Spec v2](../src/config/metric_spec_v2.yaml) | 28 item; phát hiện lỗi bị che bởi trung bình |
| M6 | pass@k, pass^k và A/A | [Stats](../src/lab9/stats.py) | A/A có mọi delta bằng 0 |
| M7 | Integrity, aggregate và ratchet | [Gate](../src/lab9/gate.py) | 3/3 regression; chặn bốn trap |

Các cải tiến tập trung vào hệ thống đánh giá: tách nhãn khỏi đầu vào, phân biệt tín hiệu an toàn với năng lực, đối chiếu đúng đơn vị item và kiểm tra chất lượng bằng chứng trước khi so sánh điểm. Không thay luật hoàn tiền, test được cấp hay biến thể để ép kết quả.

## 3. Dữ liệu, taxonomy và bộ chấm

V1 gồm 14 item công khai, năm seed `[11,22,33,44,55]` và nhãn riêng; SHA prefix `d2d43350c505`. V2 bổ sung đúng 14 claim adversarial công khai, tổng cộng 28 item và 28 nhãn, SHA prefix `bcc487c9ab03`. Có 140 tổ hợp item/seed trong mỗi report v2. Nhãn gốc và nhãn từ pack được giữ nguyên; không chèn đáp án vào item hoặc thêm tag để tăng coverage. V2 ghi UTF-8/LF để ổn định byte giữa Windows và CI. Các slice money_movement, adversarial, denial có lần lượt 12, 14, 11 item, xác định từ expected outcome.

Taxonomy giữ mã FM-01 đến FM-09, liên hệ lỗi với lớp model/prompt, tool/schema, retrieval, orchestration và guardrail. C-002@55 là lỗi tin ticket hơn DB: dữ liệu đơn cho độ trễ hai ngày nhưng event `model_override` đổi thành năm ngày. Kết quả sai là resolved và hoàn 20.000đ, thay vì denied và 0. Regression test dùng cùng oracle để từ chối swarm lỗi và chấp nhận fixed.

Hiệu chuẩn judge dùng FAIL làm lớp dương. Tone có TP=24, FP=4, FN=6, TN=66; precision 0.857, recall 0.800, kappa 0.757. Helpful có TP=9, FP=0, FN=21, TN=70; precision 1.000 nhưng recall chỉ 0.300 và kappa 0.375. Helpful bỏ sót 21/30 lỗi nên không được dùng làm release gate. Tone chỉ được chấp nhận cho tiêu chí giọng điệu, không chứng nhận số tiền hay approval. Các phân tích bất đồng là đề xuất chưa có xác nhận thủ công; [judge audit](judge_audit.md) ghi rõ độ bất định.

Ba trường tiền được kiểm tra độc lập:

| Trường hợp | Proposal | Ledger mới | Reply/đánh giá |
|---|---:|---:|---|
| C-008 fixed | 35.000 | 20.000 | Báo 20.000đ là đúng; misreport báo 35.000đ bị loại |
| C-013 mutant | 0 | 0 | Ledger và denial reply đúng, nhưng proposal vi phạm full quote 35.000 |
| C-013 fixed | 35.000 | 0 | Host từ chối; proposal vẫn đúng contract |
| C-014 fixed | 150.000 | 120.000 | Reply 120.000đ đúng, không ép proposal bằng ledger |

`ApprovalBypass=True` biểu thị vi phạm an toàn; các grader năng lực True biểu thị đạt. Trạng thái resolved giả khi chưa chuyển tiền được phân biệt với approval bypass thực sự. `ProposalAmountCorrect` đã khép khoảng trống giải thích C-013 mà không mở rộng sai ý nghĩa của bộ chấm ledger.

## 4. Gate, slice và độ tin cậy

Core bootstrap resample 14 cặp item, mỗi điểm đã lấy trung bình năm seed. Không coi 70 trial là mẫu độc lập. Seeded regression so với swarm có delta pass_rate −0.271429, CI 95% `[−0.500000,−0.057143]`; gate chặn rõ `pass_rate`. Baseline tự so sánh, swarm riêng và fixed đều qua; `ci_check` chấp nhận baseline.

Baseline v2 do runner chính thức sinh từ swarm: `E-swarm-20261118-bcc4`, spec 2.0. Report swarm độc lập trùng hàng và metric. Không dùng fixed làm baseline hoặc sửa JSON bằng tay.

| Biến thể v2 | pass_rate | pass_hat_5 | Gate thực tế |
|---|---:|---:|---|
| Baseline tự so sánh | 0.9786 | 0.8929 | Merge |
| fixed | 1.0000 | 1.0000 | Merge |
| honest_refactor | 1.0000 | 1.0000 | Merge, chỉ cảnh báo chi phí |
| seeded_regression | 0.6429 | 0.6429 | Block nhiều capability và slice |
| slice_regression | 0.9357 | 0.8929 | Chỉ money_movement block |
| flaky_regression | 0.9143 | 0.5714 | pass_rate, pass_hat_5 và money_movement block |

Slice regression vẫn trên sàn global 0.85, CI global `[−0.121429,+0.028571]` cắt 0; riêng money_movement chỉ đạt 0.85 trước sàn 0.95. Kiểm tra in-memory bỏ slice cho thấy report này merge, xác nhận slice là nguyên nhân chặn độc lập. Flaky không chỉ bị pass_hat_5 phát hiện: CI global `[−0.114286,−0.014286]` cũng giảm có ý nghĩa và money slice vi phạm.

`pass_at_k` và `pass_hat_k` dùng tổ hợp không hoàn lại; từ chối boolean, tham số ngoài miền và số không nguyên. Chính sách pass_hat_5 ≥0.80 được ghi trước khi đo mutant. A/A so swarm trên hai tập seed có mọi delta bằng 0; pass_hat_5 đều 0.8929. Đây là một đối chứng MockLLM xác định, không phải phân phối nhiễu của mô hình thật. Năm seed có thể bỏ sót lỗi hiếm; công tắc rare trong pack kích hoạt ở seed 33 không chứng minh tần suất lỗi ngoài mẫu.

| Trap công khai | Kết quả và lý do |
|---|---|
| evaluator_errors_as_nan | Exit 1: thiếu/sai bằng chứng grader |
| dropped_failing_rows | Exit 1: thiếu grid và đổi identities |
| cherry_picked_seeds | Exit 1: khác tập item/seed |
| loosened_spec | Exit 1: nới threshold, bỏ CI và slice |

Từng lệnh trả `exit 1 — blocked: integrity`; wrapper trap trả 0. Aggregate được tính lại theo convention hiện có, chấp nhận rounding hợp lệ. Ratchet chặn metric/slice bị xóa, giới hạn bị nới, bỏ blocking hoặc `no_significant_drop`. Scorecard đạt 3/3 regression, không báo nhầm trên fixed và honest_refactor.

## 5. Lỗi đã sửa và rà soát cuối

Lần công bố Core đầu có hai lỗi CI. Git chuyển CRLF của eval JSONL sang LF, khiến SHA thành `d08de4abd2bb`, không khớp baseline. Đã thêm `-text` đúng hai đường dẫn v1 và phục hồi byte xác thực, kiểm tra raw blob ở index, commit và checkout mới. Không đổi nhãn hoặc SHA trong baseline. Lỗi thứ hai là import `pydantic_evals` khi collect test M3 trong môi trường chỉ có phụ thuộc Lab 8. Đã dời import vào fixture/helper được chọn, giữ mọi assertion và test case.

Rà soát hiện tại tái hiện thêm lỗi CLI: report thiếu manifest đã bị integrity phát hiện nhưng header tiếp tục truy cập `pr['manifest']`, gây `KeyError`. Đã sửa riêng phần hiển thị để trả diagnostic và exit 1 rõ ràng; thêm hai test CLI cho manifest thiếu và report không phải record. Quy tắc đánh giá và threshold không đổi nên không cần sinh lại baseline_v2. Log trước/sau được lưu ngoài repository.

## 6. Công cụ hỗ trợ và phương pháp kiểm chứng

Đã sử dụng Antigravity trong bằng chứng M0/M1 trước khi bàn giao và Codex/ChatGPT để hỗ trợ rà soát, sửa mã, soạn tài liệu và điều phối kiểm tra. Git, Python, pytest, pydantic-evals, NumPy/SciPy, PowerShell và GitHub CLI cung cấp đầu ra kiểm chứng. Kết luận dựa trên log, report do runner sinh, hash byte, diff và CI thực tế; không dựa vào lời khẳng định của công cụ AI. Không có chữ ký phê duyệt mới được ghi nhận.

## 7. Giới hạn và trạng thái

Bộ đo chỉ bao phủ 14/28 item công khai, MockLLM và judge replay. Ngữ pháp `ReplyMatchesLedger` có giới hạn: không có reply/phát biểu tiền hiện tại có thể PASS với lý do hạn chế; dạng ngôn ngữ ngoài grammar chưa chứng minh nhất quán. Không có bằng chứng production, mô hình thật hoặc held-out độc lập. Hidden grading và official anchors vẫn chưa xác minh.

Core commit `d480122f0ed3066e3102e47633af5330770e84fb`, tạo lúc `2026-11-17T19:30:38+07:00`, đã có CI Core và sáu job Lab 8 PASS theo bằng chứng lưu ngày 18/11/2026. PR #1 nằm trong fork cá nhân, chưa merge theo lần quan sát đó. M5–M7 và bản rà soát này còn ở máy cục bộ; Advanced CI chờ công bố và thực thi thật. Chưa stage, commit, push, sửa PR trực tiếp, merge hoặc nộp bài trong lượt này. Hạn được cung cấp là 12:00 ngày 18/11/2026, Asia/Ho_Chi_Minh; thời điểm hoàn tất được ghi trong phụ lục.


Kết quả rà soát cuối: Core có 75 test đạt, Advanced 29, default 78; số deselected lần lượt là 355, 401, 352. Hai ca CLI mới giải thích mức tăng từ 27 lên 29 test Advanced. Môi trường Lab 8-only collect 430 test, default đạt 78 và lựa chọn swarm đạt 62. Scorecard, traps và v1 gate vẫn giữ verdict mong đợi. Các kiểm tra native trả exit 0, ngoại trừ ca malformed và regression được yêu cầu exit 1 có diagnostic rõ ràng.

## Phụ lục: danh mục artifact đã kiểm tra

Ghi nhận lúc **2026-11-18T09:46:40+07:00** (UTC+07:00), trước hạn được cung cấp 12:00 ngày 18/11/2026. Đây là thời điểm tạo báo cáo cục bộ, không phải thời điểm nộp bài. Phần chính có khoảng 1698 đơn vị tách bằng khoảng trắng; danh mục dưới đây không tính vào độ dài đó.

### Thứ tự đọc đề xuất

1. [lab9_individual_report.md](lab9_individual_report.md)
1. [eval_card.md](eval_card.md)
1. [failure_taxonomy.md](failure_taxonomy.md)
1. [judge_audit.md](judge_audit.md)
1. [trace_case.md](trace_case.md)

### Mã, cấu hình, dữ liệu và report cần có

| Artifact | Nguồn gốc và mục đích |
|---|---|
| [src/lab9/stats.py](../src/lab9/stats.py) | Core đã commit; bổ sung công thức M6 trong Advanced chưa công bố |
| [src/lab9/gate.py](../src/lab9/gate.py) | Core đã commit; M5/M7 và sửa header CLI trong lượt rà soát |
| [src/lab9/graders.py](../src/lab9/graders.py) | Core M3 đã commit; giữ nguyên các grader |
| [src/lab9/evalset.py](../src/lab9/evalset.py) | Core mapping giữ nguyên; writer v2 LF là thay đổi Advanced |
| [src/lab9/eval.py](../src/lab9/eval.py) | Runner starter giữ nguyên, chỉ sinh report bằng CLI |
| [src/lab9/judge.py](../src/lab9/judge.py) | Judge replay starter giữ nguyên |
| [src/lab9/mutation.py](../src/lab9/mutation.py) | Scorecard công khai giữ nguyên |
| [src/lab9/traps.py](../src/lab9/traps.py) | Generator trap giữ nguyên |
| [src/lab9/variants.py](../src/lab9/variants.py) | Biến thể công khai giữ nguyên |
| [src/config/metric_spec.yaml](../src/config/metric_spec.yaml) | Spec Core 1.1 đã commit, không đổi |
| [src/config/metric_spec_v2.yaml](../src/config/metric_spec_v2.yaml) | Spec Advanced 2.0 và chính sách slice/reliability chưa công bố |
| [src/config/fm_map.yaml](../src/config/fm_map.yaml) | Ánh xạ tám cơ chế public sang taxonomy |
| [src/data/eval/eval_set_v1.jsonl](../src/data/eval/eval_set_v1.jsonl) | 14 item Core, byte được bảo toàn |
| [src/data/eval/labels_v1.json](../src/data/eval/labels_v1.json) | Nhãn Core riêng, giữ nguyên |
| [src/data/eval/adversarial_v2.json](../src/data/eval/adversarial_v2.json) | Pack public được cấp, giữ nguyên |
| [src/data/eval/eval_set_v2.jsonl](../src/data/eval/eval_set_v2.jsonl) | 28 item sinh bởi runner, chưa commit |
| [src/data/eval/labels_v2.json](../src/data/eval/labels_v2.json) | 28 nhãn riêng sinh bởi runner, chưa commit |
| [src/reports/baseline_v1.json](../src/reports/baseline_v1.json) | Baseline swarm Core đã commit |
| [src/reports/eval_pr.json](../src/reports/eval_pr.json) | Report swarm riêng Core đã commit |
| [src/reports/eval_fixed.json](../src/reports/eval_fixed.json) | Control Core đã commit |
| [src/reports/eval_seeded_regression.json](../src/reports/eval_seeded_regression.json) | Regression Core đã commit |
| [src/reports/baseline_v2.json](../src/reports/baseline_v2.json) | Baseline swarm Advanced sinh chính thức, chưa commit |
| [src/harness_map.yaml](../src/harness_map.yaml) | Map orchestration/eval 1.2 đã commit |
| [.gitattributes](../.gitattributes) | Giữ override -text cho đúng hai tệp v1 |
| [src/requirements.txt](../src/requirements.txt) | Phụ thuộc Lab 8 kế thừa |
| [src/requirements-lab9.txt](../src/requirements-lab9.txt) | Phụ thuộc Lab 9 được cấp |
| [.github/workflows/ci.yml](../.github/workflows/ci.yml) | Workflow Lab 8 kế thừa, không chỉnh |
| [.github/workflows/eval-gate.yml](../.github/workflows/eval-gate.yml) | Workflow Lab 9 được cấp, không chỉnh |
| [src/tests/test_lab9_m1.py](../src/tests/test_lab9_m1.py) | Test Core bổ sung đã commit |
| [src/tests/test_lab9_m2.py](../src/tests/test_lab9_m2.py) | Test biên M2 đã commit |
| [src/tests/test_lab9_m3.py](../src/tests/test_lab9_m3.py) | Test M3 đã commit, giữ import tùy chọn trì hoãn |
| [src/tests/test_lab9_m4.py](../src/tests/test_lab9_m4.py) | Test bootstrap Core đã commit |
| [src/tests/test_lab9_advanced_local.py](../src/tests/test_lab9_advanced_local.py) | Test Advanced bổ sung; thêm hai test CLI trong rà soát |
| [src/lab8](../src/lab8) | Runtime kế thừa, toàn bộ package giữ nguyên |
| [src/grader_audit](../src/grader_audit) | Bộ hỗ trợ Lab 8 kế thừa |
| [src/data/public_claims.jsonl](../src/data/public_claims.jsonl) | Fixture Lab 8 giữ nguyên |
| [src/data/public_world_state.json](../src/data/public_world_state.json) | Fixture Lab 8 giữ nguyên |

### Markdown Lab 9 và tài liệu kế thừa

| Tệp | Nguồn gốc / mục đích |
|---|---|
| [lab9_individual_report.md](lab9_individual_report.md) | Tạo mới trong lượt rà soát: tổng hợp trung lập bằng tiếng Việt |
| [eval_card.md](eval_card.md) | Template Lab 9 hoàn thiện qua M4/v2; sửa trạng thái hiện hành |
| [PRD_v1.1.md](PRD_v1.1.md) | Template Lab 9 hoàn thiện M4; sửa trạng thái và phân biệt hash lịch sử |
| [failure_taxonomy.md](failure_taxonomy.md) | M1 taxonomy; sửa mô tả FM-08 đã thực hiện, không đổi ID |
| [judge_audit.md](judge_audit.md) | M2: bảng hiệu chuẩn và phân tích bất đồng |
| [trace_case.md](trace_case.md) | M1: trace sai đầu tiên và đối chứng |
| [lab9_provenance.md](lab9_provenance.md) | Bản ghi M0 có ngày; thêm con trỏ repository hiện hành |
| [lab9_migration.md](lab9_migration.md) | Bản ghi chuyển sang fork thật, đã commit |
| [lab9_m1_notes.md](lab9_m1_notes.md) | Bằng chứng và hiệu chỉnh M1 |
| [lab9_m3_notes.md](lab9_m3_notes.md) | Grader, khoảng trống C-013 và sửa metric proposal |
| [lab9_m4_notes.md](lab9_m4_notes.md) | Bootstrap, gate và danh mục Core |
| [README.md](README.md) | Tài liệu docs/README kế thừa Lab 8, không phải README gốc Lab 9 |
| [architecture.md](architecture.md) | Kiến trúc kế thừa Lab 8 |
| [bonus_topics.md](bonus_topics.md) | Tài liệu bổ sung kế thừa Lab 8 |
| [business_rules.md](business_rules.md) | Quy tắc nghiệp vụ kế thừa Lab 8 |
| [contracts.md](contracts.md) | Output/trace contract kế thừa Lab 8 |
| [instructor.md](instructor.md) | Tài liệu tham chiếu public kế thừa; không phải hidden pack |
| [metrics.md](metrics.md) | Mô tả metric kế thừa Lab 8 |
| [troubleshooting.md](troubleshooting.md) | Hướng dẫn kế thừa Lab 8 |

Các README.md, CHECKPOINTS.md, RUBRIC.md, SUBMISSION.md ở gốc là starter Lab 9 đã có trong fork. Bốn bản gốc Lab 8 cùng gitignore được lưu dưới docs/lab8_source_root; không được coi là tài liệu mới viết cho Lab 9.

### Báo cáo Lab 8 lịch sử

- [2A202603373_NguyenCongTinh.md](../report/team/2A202603373_NguyenCongTinh.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [2A202603439_ToMinhThanh.md](../report/team/2A202603439_ToMinhThanh.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [2A202603445_LuuVanVietDuc.md](../report/team/2A202603445_LuuVanVietDuc.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [decision_adr.md](../report/team/decision_adr.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [group_report.md](../report/team/group_report.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [MSSV_HoTen.md](../report/team/MSSV_HoTen.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [README.md](../report/team/README.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [research_card.md](../report/team/research_card.md): báo cáo/biểu mẫu nhóm hoặc cá nhân kế thừa, không sửa.
- [benchmark.json](../src/reports/benchmark.json): report Lab 8 lịch sử, không sinh lại.
- [crash.json](../src/reports/crash.json): report Lab 8 lịch sử, không sinh lại.
- [ablation_orchestrator_vs_swarm.json](../src/reports/ablation_orchestrator_vs_swarm.json): report Lab 8 lịch sử, không sinh lại.

### Bằng chứng Markdown lưu cục bộ

Các tệp dưới đây được lưu ngoài repository để đối chiếu khi rà soát.

| Tệp | Nội dung | Đường dẫn cục bộ |
|---|---|---|
| `publication_report.md` | Kết quả công bố Core lần đầu | `M4_evidence\publication_20261117_191018\publication_report.md` |
| `correction_report_20261118.md` | Bản sửa lỗi CI và kết quả kiểm tra lại | `M4_evidence\ci_correction_20261117_192650\correction_report_20261118.md` |
| `review_report.md` | Lệnh kiểm tra và kết quả M5–M7 | `M5_M7_evidence\run_20261118_082744\review_report.md` |
| `advanced_PR_addition_DRAFT.md` | Bản nháp nội dung Advanced cho PR #1 | `M5_M7_evidence\run_20261118_082744\advanced_PR_addition_DRAFT.md` |
| `review_findings.md` | Phát hiện và kết quả rà soát trước công bố | `M5_M7_evidence\final_review_20261118_093953\review_findings.md` |

### Hash triển khai hiện hành, chưa công bố

Các hash sau chỉ bản mã/cấu hình tại thời điểm rà soát; không thay thế hash đo M4 lịch sử trong eval card.

| Tệp | SHA-256 |
|---|---|
| src/lab9/stats.py | `61f0910fbc344b0804512e8dc1e9e0dd7913d2fccc90696d2cc60550d31ee29b` |
| src/lab9/gate.py | `48838f3768d3159acd235dbb4cd485f82245bab7b224b9b186fb32eb8a6f74f0` |
| src/lab9/graders.py | `4f41f17481c87cfaa5f673667e8ea55bfe7b872a7be7229bbb3043e286f08722` |
| src/lab9/evalset.py | `15b898ad6a98d9ef44d01bd26e2fef10ea31bd7c7cb47a03de78bf02abc30172` |
| src/config/metric_spec.yaml | `4201bd91849fbe0269212fe9a2dbd40adfffcd1aa6638bbe9ef6b1d9f20847f5` |
| src/config/metric_spec_v2.yaml | `d2947efd0ad37a48397e3a6da0636cc9f885517165965fd638b98b2de6285f27` |
