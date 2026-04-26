# CHANGELOG — v2 → v3

> Tài liệu mô tả thay đổi từ v2 sang v3 dựa trên 4 feedback của user.

---

## 🎯 4 thay đổi chính

### 1. Bước 0.5 mới — Khởi tạo hồ sơ ✅

**Vấn đề v2:** Khi chọn "Nhập tự do", người dùng đi thẳng vào bước 1 mà không nhập tên/mã hồ sơ. Ở màn hình kết quả chỉ hiện "custom_input".

**Giải pháp v3:** Thêm bước **0.5 — Khởi tạo hồ sơ** giữa Bước 0 và Bước 1:
- Field bắt buộc: **Họ và tên khách hàng**
- Field tự sinh: **Mã hồ sơ vay** (ví dụ `HS-A-20260426`, `HS-CUSTOM-202604261430`)
- Field: **Ngày nộp hồ sơ** (mặc định hôm nay)
- Card tóm tắt hiển thị 3 thông tin trên ngay tại bước này
- Nút "Tiếp theo" bị disable nếu chưa nhập tên
- **Persona preset (A/B/C)** tự fill tên + mã từ persona, vẫn đi qua bước 0.5 để xác nhận

**Hiển thị ở sidebar:** Một card "Đang xét duyệt" với tên + mã hồ sơ → người dùng luôn thấy đang làm hồ sơ ai.

**Hiển thị ở kết quả:** Tên + mã + ngày nộp ngay ở dashboard hero.

### 2. Dashboard kết quả gộp 1 view ✅

**Vấn đề v2:** Thông tin chính trải dài trên nhiều phần (hero card → metric row → 4 tabs). Phải scroll/click nhiều mới thấy hết.

**Giải pháp v3:** Tổ chức lại thành 3 tầng theo độ ưu tiên:

**Tầng 1 — Dashboard Hero (luôn hiện ngay đầu):**
- Bên trái: gauge điểm to (4rem font) + hạng + risk level — 1 ô
- Bên phải: status badge + thông tin khách hàng + 4 info card (lãi suất/số tiền/kỳ hạn/sản phẩm)
- Tất cả thông tin **quan trọng nhất** trong 1 màn hình, không cần scroll

**Tầng 2 — Quick Summary (3 cột):**
- Card 1: Tóm tắt 6 hard rules pass/fail
- Card 2: Điểm theo 4 nhóm
- Card 3: **Lý do quyết định** (text giải thích bằng ngôn ngữ tự nhiên)

**Tầng 3 — Tabs cho chi tiết khi cần:**
- Tab 1: Phương án trả nợ (đặt đầu vì quan trọng nhất)
- Tab 2: Lý do lãi suất (mới)
- Tab 3: Điểm chi tiết
- Tab 4: Hard rules + Chứng từ (gộp lại từ 2 tab cũ)

**Kết quả:** Người xem thấy ngay quyết định + lý do trong 1 view duy nhất, không phải click tab.

### 3. Giải thích lãi suất khoa học ✅

**Vấn đề v2:** Chỉ hiện "Lãi suất đề xuất: 20%/năm" mà không nói tại sao.

**Giải pháp v3:** Tab mới **"💡 Lý do lãi suất"** hiển thị:

**Phần 1 — Công thức tính:**
```
r = LS_điều_hành + Chi_phí_vốn + Biên_rủi_ro_(theo hạng) + Phí_dịch_vụ
```

**Phần 2 — Phân tích từng cấu phần** (cho hạng AA làm ví dụ):
| Cấu phần | Giá trị | Nguồn |
|---------|---------|--------|
| Lãi suất điều hành NHNN | +4.50% | QĐ 1124/QĐ-NHNN ngày 19/06/2023 |
| Chi phí huy động vốn | +6.00% | Bình quân lãi suất tiết kiệm 12 tháng |
| Biên rủi ro hạng AA | +8.00% | Theo bảng risk premium |
| Phí dịch vụ + lợi nhuận | +1.50% | Chi phí vận hành + margin |
| **Tổng** | **20.00%/năm** | |

**Phần 3 — Bảng tham chiếu** so sánh tất cả các hạng (có dấu 👉 chỉ hạng hiện tại):
| Hạng | Điểm tối thiểu | Mức rủi ro | Biên rủi ro | Khoảng lãi suất | Trung bình |
|------|----|----|----|----|----|
| AA | 800 | Very Low | 8.0% | 18.0% - 22.0% | 20.0% |
| A | 700 | Low | 10.0% | 20.0% - 24.0% | 22.0% |
| BBB | 650 | Medium | 13.0% | 23.0% - 27.0% | 25.0% |
| BB | 500 | Medium High | 16.0% | 26.0% - 30.0% | 28.0% |

Đây là cách trình bày **chuẩn trong ngân hàng thực tế** — bám theo phương pháp ALCO (Asset-Liability Committee) định giá lãi suất.

### 4. Slider lãi suất dynamic ✅

**Vấn đề v2:** Lãi suất là 1 con số cứng, người dùng không thấy được sự linh hoạt trong khung sản phẩm.

**Giải pháp v3:** Thay đổi triết lý — mỗi hạng có **khoảng** thay vì 1 số cứng:

| Hạng | Khoảng cũ (v2) | Khoảng mới (v3) |
|------|----|----|
| AA | 20% | 18% – 22% |
| A | 22% | 20% – 24% |
| BBB | 25% | 23% – 27% |
| BB | 28% | 26% – 30% |

**Cách hiển thị:**
- Slider trượt trong khoảng của hạng (ví dụ AA: 18-22%)
- Bên phải slider: card hiển thị "So với mặc định 20%: -1.0%" (màu xanh nếu thấp hơn, đỏ nếu cao hơn)
- Khi kéo slider → toàn bộ bảng PA1, PA2, chart so sánh, tổng lãi, file Excel download **đều cập nhật real-time**

**Use case thực tế:** Cho phép giảng viên/người demo *tùy biến lãi suất* để so sánh các kịch bản:
- "Nếu được lãi tốt nhất 18%, tổng lãi PA1 là bao nhiêu?"
- "Nếu xấu nhất 22%, có khác nhiều không?"

**Lý do cho phép overlap nhẹ:** Hạng A có khoảng 20-24% và hạng AA là 18-22% — phần overlap 20-22% phản ánh thực tế: ngân hàng có thể offer khách hạng A lãi tốt như AA để cạnh tranh, hoặc khách AA bị offer lãi cao hơn nếu có yếu tố rủi ro phụ.

---

## 📁 Files thay đổi

| File | Trạng thái | Mô tả |
|------|-----------|------|
| `app.py` | ✏️ Sửa hoàn toàn | v2 → v3 với 4 feedback |
| `data/scorecard.json` | ✏️ Cập nhật | Thêm interest_rate_min/max/risk_premium cho mỗi hạng + interest_rate_components |
| `engine/scoring_engine.py` | ✏️ Cập nhật nhỏ | GradeResult thêm 3 field mới (interest_rate_min, max, risk_premium) |
| `app_v2_backup.py` | 🆕 Backup v2 | Có thể xóa nếu không cần |
| `data/personas.json` | ✅ Giữ nguyên | |
| `engine/repayment_calculator.py` | ✅ Giữ nguyên | |
| `tests/test_scoring.py` | ✅ Giữ nguyên (vẫn 7/7 pass) | |
| `main.py` | ✅ Giữ nguyên | |

---

## 🔧 Cách cập nhật khi đã deploy

### Cách dễ nhất — GitHub Desktop

Cần thay 3 file sau (theo thứ tự):

1. **`app.py`** — file v3 mới
2. **`data/scorecard.json`** — đã thêm fields mới
3. **`engine/scoring_engine.py`** — đã update GradeResult

Trong GitHub Desktop:
- Thay 3 file vào đúng đường dẫn
- Bạn sẽ thấy 3 changes
- Commit message: `v3: Add profile init step + dynamic rate slider + scientific rate explanation`
- Click **Commit to main** → **Push origin**
- Streamlit Cloud tự redeploy trong 1-2 phút

**Nếu chỉ thay app.py mà không thay 2 file kia → app sẽ crash** vì v3 cần các field mới trong scorecard.json và GradeResult.

### Test local trước khi push

```bash
streamlit run app.py
```

Checklist test 7 điểm:
1. ✅ Bước 0 hiện 4 persona card đẹp
2. ✅ Click Persona A → đi qua bước 0.5 → thấy tên đã auto-fill
3. ✅ Click "Nhập mới" → bước 0.5 yêu cầu nhập tên, nút Tiếp theo bị disable nếu chưa nhập
4. ✅ Đi hết 6 bước → màn kết quả có dashboard hero gộp tất cả thông tin
5. ✅ Quick summary 3 cột hiển thị đúng (hard rules / điểm / lý do)
6. ✅ Tab "Phương án trả nợ" có slider — kéo slider thấy bảng PMT cập nhật ngay
7. ✅ Tab "Lý do lãi suất" có công thức + 4 cấu phần + bảng tham chiếu

---

## 💡 Vẫn còn có thể nâng cấp tiếp

Nếu sau này muốn tinh chỉnh thêm:
- Thêm chart pie/donut cho phân tích cấu phần lãi suất
- Animation count-up cho điểm số khi chuyển sang bước 5
- Export PDF báo cáo chấm điểm để giảng viên tải về
- Lưu lịch sử các hồ sơ đã xét duyệt (cần database)
