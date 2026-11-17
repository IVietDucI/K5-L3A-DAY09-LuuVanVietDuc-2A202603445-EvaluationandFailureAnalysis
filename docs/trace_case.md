# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape swarm --claim C-002 --seed 55
python -m lab9.trace_case --shape fixed --claim C-002 --seed 55   # đối chứng
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`handoff`, `investigator`, `model_override`, `quote`, `reply` …), ledger so với nhãn, và lý do của grader Lab 8. Lưu ý: lệnh chẩn đoán trả **exit code 0** ngay cả khi in ra verdict **FAIL** của trial (exit 0 nghĩa là lệnh thu thập trace chạy thành công, không phải agent đạt).

## Hồ sơ trace chính — `swarm C-002@55`

| Trường | Nội dung |
|---|---|
| Trial | `swarm C-002@55`, `run_id = R-swarm-C-002-s55` (cũng ghi nhận thất bại duy nhất của `swarm` trong `src/reports/benchmark.json`, pass rate 69/70) |
| Triệu chứng | Grader Lab 8 (`lab8.metrics.trial_pass`) báo `FAIL (status resolved != denied)`. Observed: `status = resolved`, `proposal_amount = 20000`, `ledger.refund_vnd = 20000`, `refund_count = 1`, `policy_denied = False`, `unexpected_rows = 0`. Expected (`labels_v1.json` / `T02`): `status = denied`, `proposal_amount = 0`, `refund_vnd = 0`, `refund_count = 0`. *(Bản `swarm` trong Lab 8 không ghi event `reply`, nên triệu chứng hiện trực tiếp ở `status`, `quote` và `refund_ledger`.)* |
| Bước sai đầu tiên | **Bước 3** (1-based) — `kind: model_override`, payload: `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | **Bước 1 (`handoff`)** hợp lệ: gán đúng `claim_id = "C-002"`, `principal_scope = "owner_order_only"`, chỉ cấp 3 read tool (`lookup_order`, `lookup_policy`, `compute_compensation`), không chứa secret hay header của parent. **Bước 2 (`investigator`)** hợp lệ: `lookup_order` đọc đúng bảng `orders` cho `O-202` (`status = "delivered"`, `delay_days = 2`, `shipping_fee_vnd = 20000`, `damage_verified = false`) và `policy_count = 1`. Theo điều khoản `SHIP-LATE-03` (`min_delay_days = 3`), đơn trễ 2 ngày **không** đủ điều kiện hoàn phí. Sai sót chỉ bắt đầu ở **bước 3** khi `swarm` nhận số `5` ngày do người dùng viết trong ticket (`"Đơn giao trễ 5 ngày, hoàn phí ship giúp."`) và ghi đè `order["delay_days"] = 5` vì `seed % 5 == 0` (`55 % 5 == 0`). Từ giá trị bị ghi đè đó, bước 4 (`quote`) tính sai thành `amount_vnd = 20000` (`SHIP-LATE-03`), kéo theo host `issue_refund` commit 20.000đ trên approval `A-002`. |
| Failure mode & Layer | `FM-03` (`ticket_trust — tin ticket hơn DB`), layer: `model/prompt` |
| Đối chứng (`fixed`) | Cùng `C-002@55` trên `fixed` (`R-fixed-C-002-s55`, `lab8_pass = True (ok)`): bước 1 `handoff` và bước 2 `investigator` (`delay_days = 2`) giống hệt, **không có** bước `model_override`. Bước 3 `quote` giữ đúng `delay_days = 2` của DB nên trả `{"amount_vnd": 0, "reason": "no_entitlement", "clause_ids": [], "parts": {}}`; bước 4 `reply` từ chối lịch sự, `status = denied`, `refund_vnd = 0`, `refund_count = 0`. Đối chiếu thêm ở seed 11: `seeded_regression C-002@11` (`R-seeded_regression-C-002-s11`, **synthetic**) tái hiện cùng lỗi ở bước 3 `model_override {"delay_days": 5}` → bước 4 `quote=20000` → `ledger=20000` (`FAIL`), còn `fixed C-002@11` (`R-fixed-C-002-s11`) `PASS` (`denied`, `0`). |
| Regression test | `src/tests/test_lab9_m1.py`: `test_c002_seed55_ticket_trust_regression_and_fixed_control` và `test_seeded_regression_c002_seed11_and_fixed_control` (mark `student`, chạy trên SQLite tạm thời độc lập với cùng oracle `lab8.metrics.trial_pass` + `ledger_snapshot` + kiểm tra event `model_override`). Oracle bác bỏ `swarm C-002@55` và `seeded_regression C-002@11`, đồng thời chấp nhận `fixed C-002@55` và `fixed C-002@11`; bản thân các pytest test đều **PASS**. |
| Chưa chắc chắn / Giới hạn | 1) Đây là một trial trên `MockLLM` với nhánh lỗi tất định `seed % 5 == 0`, nên ở 4 seed khác (`11, 22, 33, 44`) `swarm` vẫn pass và che giấu lỗi nếu chỉ chạy ít seed. 2) Kết luận từ một trial `C-002@55` chỉ chứng minh cơ chế `FM-03` trên claim đơn lẻ; các dạng biến thể im lặng (`quiet_override` trong `variant_agent.py`) có thể tin ticket mà **không** ghi event `model_override`, vì vậy kiểm tra theo step (`DbFactKept`) phải luôn đi kèm kiểm tra ledger/outcome (`TrialPass`, `RefundAmountCorrect`). 3) Bản gốc `swarm` trong Lab 8 không phát event `reply`, nên phần phân tích đối chiếu văn bản trả lời dựa trên shape `fixed` và `seeded_regression`. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai (hoặc ngược lại, như `FM-08`).
- "Bước sai đầu tiên" phải dẫn số event cụ thể (1-based), `kind` và trích payload, không phải mô tả chung chung.
- Case chỉ hoàn thành khi có regression test chạy được trong `src/tests/test_lab9_m1.py` và nối `provenance.from_trace = "R-swarm-C-002-s55"` cho `E-002` (`C-002`) trong `src/lab9/evalset.py`.
