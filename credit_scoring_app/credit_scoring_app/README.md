# Credit Scoring App - Vietnam Consumer Loan

Hệ thống xét duyệt hồ sơ vay tiêu dùng cá nhân theo scorecard 4 nhóm chứng từ, tính toán 2 phương án trả nợ. Xây dựng bằng Streamlit.

## 🚀 Hướng dẫn chạy app

### Lần đầu tiên — setup môi trường

Bạn cần Python >= 3.10 và pip. Kiểm tra bằng:

```bash
python --version
```

Nếu chưa có Python, tải từ https://www.python.org/downloads/

Cài thư viện:

```bash
cd credit_scoring_app
pip install -r requirements.txt
```

### Chạy Streamlit app

```bash
streamlit run app.py
```

Browser sẽ tự mở tại http://localhost:8501. Nếu không tự mở, copy link từ terminal vào browser.

### Chạy demo terminal (không UI)

```bash
python main.py
```

### Chạy unit tests

```bash
python tests/test_scoring.py
```

## 📁 Cấu trúc dự án

```
credit_scoring_app/
├── app.py                       # Streamlit UI wizard 5 bước  ⭐
├── main.py                      # Demo terminal chạy 3 persona
├── requirements.txt             # Dependencies
├── README.md
├── data/
│   ├── scorecard.json           # Cấu hình chấm điểm (có thể sửa để thay đổi trọng số)
│   └── personas.json            # 3 hồ sơ test demo
├── engine/
│   ├── __init__.py
│   ├── scoring_engine.py        # HardRulesChecker + Scorer + GradeClassifier
│   └── repayment_calculator.py  # Tính 2 phương án trả nợ
└── tests/
    └── test_scoring.py          # 7 unit tests
```

## 🎯 Tính năng app

**Wizard 5 bước rõ ràng:**
1. Chọn persona preset (A/B/C) hoặc nhập tự do
2. Nhập thông tin nhóm 1 — Lịch sử tín dụng + upload chứng từ
3. Nhập thông tin nhóm 2 — Thu nhập & việc làm + upload
4. Nhập thông tin nhóm 3 — Nhân thân + upload
5. Nhập thông tin nhóm 4 — Tài sản + thông tin vay + upload

**Kết quả xét duyệt có:**
- Thẻ kết quả với màu sắc theo quyết định (xanh/vàng/đỏ)
- Tab Hard Rules: hiển thị pass/fail từng điều kiện
- Tab Điểm chi tiết: bar chart + bảng điểm từng biến
- Tab Phương án trả nợ: 2 bảng lịch trả nợ song song + line chart so sánh
- Tab Chứng từ đã upload: danh sách file

**Tiện ích:**
- Download bảng lịch trả nợ dưới dạng Excel (3 sheet)
- Sidebar tracker tiến trình
- Nút "Quay lại" mỗi bước để sửa thông tin
- "Làm lại từ đầu" để xét duyệt hồ sơ khác

## 📊 Scorecard

Hệ thống chấm điểm trên thang 1000 với 4 nhóm:

| Nhóm | Trọng số | Điểm tối đa | Biến chính |
|------|----------|-------------|------------|
| Lịch sử tín dụng | 35% | 350 | CIC, DTI, số khoản vay |
| Thu nhập & việc làm | 30% | 300 | Lương, HĐLĐ, thời gian làm việc |
| Nhân thân | 20% | 200 | Tuổi, học vấn, cư trú, hôn nhân |
| Tài sản | 15% | 150 | BĐS, xe, tiết kiệm |

**Xếp hạng:**
- AA (>=800): Duyệt ưu tiên, lãi 20%/năm
- A (>=700): Duyệt, lãi 22%/năm
- BBB (>=650): Duyệt có điều kiện, lãi 25%/năm
- BB (>=500): Xem xét thủ công, lãi 28%/năm
- B (<500): Từ chối

## 🛡️ 6 Hard Rules (loại trực tiếp)

Trước khi chấm điểm, hệ thống kiểm tra:
1. Tuổi >= 20
2. Tuổi <= 60
3. Thu nhập >= 5 triệu VNĐ/tháng
4. Thời gian công tác >= 3 tháng
5. Không có nợ CIC nhóm 3, 4, 5 (theo TT 11/2021/TT-NHNN)
6. DTI sau khi vay <= 60%

## 📋 Ba persona demo

| Persona | Mô tả | Điểm dự kiến | Kết quả |
|---------|-------|--------------|---------|
| A - Nguyễn Văn An | 32t, kỹ sư FPT, lương 25tr, CIC nhóm 1 | 915/1000 | 🟢 Duyệt ưu tiên (AA) |
| B - Trần Thị Bình | 27t, kế toán, lương 11tr, CIC nhóm 2 1 lần | 660/1000 | 🟡 Duyệt có điều kiện (BBB) |
| C - Lê Văn Cường | 45t, lao động tự do, CIC nhóm 3 | — | 🔴 Từ chối (hard rule) |

## 🔧 Cách mở rộng

### Thay đổi scorecard

Chỉnh sửa `data/scorecard.json` — không cần đụng code. Có thể:
- Thêm/bớt hard rules
- Điều chỉnh trọng số từng nhóm
- Thay đổi bin điểm
- Điều chỉnh ngưỡng hạng và lãi suất

### Thêm persona test

Thêm object mới vào mảng `personas` trong `data/personas.json`.

## 🌐 Deploy lên cloud (miễn phí)

### Streamlit Cloud

1. Tạo tài khoản tại https://streamlit.io/cloud
2. Push code lên GitHub
3. Connect repo với Streamlit Cloud
4. Deploy - sẽ có link `https://<username>-credit-scoring-app.streamlit.app`

Chi tiết: https://docs.streamlit.io/streamlit-community-cloud

## 📖 Nguồn tham khảo chính

1. **FICO** - Chuẩn quốc tế về trọng số scorecard
2. **BIDV** - Mô hình chấm điểm cá nhân
3. **CIC** - Trung tâm Thông tin Tín dụng Quốc gia Việt Nam
4. **TT 39/2016/TT-NHNN** - Hoạt động cho vay của TCTD
5. **TT 43/2016/TT-NHNN** - Cho vay tiêu dùng của công ty tài chính
6. **TT 11/2021/TT-NHNN** - Phân loại nợ
7. **Nghiên cứu ĐH Ngoại thương (2023)** - Mô hình Logistic
