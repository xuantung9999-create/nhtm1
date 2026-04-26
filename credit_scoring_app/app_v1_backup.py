"""
Streamlit App - Hệ thống xét duyệt hồ sơ vay tiêu dùng cá nhân
Chạy: streamlit run app.py

Wizard 5 bước:
  0 - Chọn persona preset hoặc nhập tự do
  1 - Nhóm 1: Lịch sử tín dụng
  2 - Nhóm 2: Thu nhập & việc làm
  3 - Nhóm 3: Nhân thân
  4 - Nhóm 4: Tài sản + thông tin khoản vay
  5 - Kết quả xét duyệt
"""

import json
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from engine import CreditScoringPipeline, calculate_both_plans


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).parent
SCORECARD_PATH = BASE_DIR / "data" / "scorecard.json"
PERSONAS_PATH = BASE_DIR / "data" / "personas.json"

st.set_page_config(
    page_title="Hệ thống xét duyệt vay tiêu dùng",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customization
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stProgress > div > div > div > div { background-color: #1F4E79; }
    .result-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid;
    }
    .pass-card { background-color: #D9EAD3; border-color: #3B6D11; }
    .fail-card { background-color: #F4CCCC; border-color: #791F1F; }
    .warn-card { background-color: #FFF2CC; border-color: #854F0B; }
    .big-score { font-size: 3rem; font-weight: 700; margin: 0; }
    .step-label {
        font-size: 0.9rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_scorecard():
    with open(SCORECARD_PATH, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_personas():
    with open(PERSONAS_PATH, encoding="utf-8") as f:
        return json.load(f)["personas"]


@st.cache_resource
def get_pipeline():
    return CreditScoringPipeline(str(SCORECARD_PATH))


# ============================================================
# STATE MANAGEMENT
# ============================================================

def init_state():
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "applicant" not in st.session_state:
        st.session_state.applicant = {
            "personal_info": {},
            "employment": {},
            "credit_history": {},
            "assets": {},
            "loan_request": {},
        }
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {
            "group1": [],
            "group2": [],
            "group3": [],
            "group4": [],
        }
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None


def reset_state():
    for key in ["step", "applicant", "uploaded_files", "selected_persona"]:
        if key in st.session_state:
            del st.session_state[key]
    init_state()


def load_persona_to_state(persona):
    st.session_state.applicant = {
        "personal_info": persona["personal_info"].copy(),
        "employment": persona["employment"].copy(),
        "credit_history": persona["credit_history"].copy(),
        "assets": persona["assets"].copy(),
        "loan_request": persona["loan_request"].copy(),
    }
    st.session_state.selected_persona = persona["persona_id"]


def next_step():
    st.session_state.step += 1


def prev_step():
    st.session_state.step -= 1


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar(scorecard):
    with st.sidebar:
        st.markdown("### 🏦 Hệ thống xét duyệt")
        st.markdown(f"**Sản phẩm:** {scorecard['product']['name']}")
        st.markdown("---")

        # Progress
        steps = ["Chọn hồ sơ", "Lịch sử TD", "Thu nhập", "Nhân thân", "Tài sản & Vay", "Kết quả"]
        st.markdown("### Tiến trình")
        for i, label in enumerate(steps):
            if i < st.session_state.step:
                st.markdown(f"✅ {label}")
            elif i == st.session_state.step:
                st.markdown(f"🔵 **{label}**")
            else:
                st.markdown(f"⚪ {label}")

        st.markdown("---")
        if st.button("🔄 Làm lại từ đầu", use_container_width=True):
            reset_state()
            st.rerun()

        st.markdown("---")
        st.markdown("### Thông tin scorecard")
        st.caption(f"Thang điểm: {scorecard['scoring_system']['max_score']}")
        st.caption("Trọng số 4 nhóm:")
        for key, group in scorecard["scoring_groups"].items():
            st.caption(f"• {group['name']}: {group['weight']*100:.0f}%")


# ============================================================
# STEP 0: CHOOSE PERSONA
# ============================================================

def render_step0_choose(personas):
    st.markdown('<p class="step-label">Bước 0 / 5</p>', unsafe_allow_html=True)
    st.title("Bắt đầu xét duyệt")
    st.markdown(
        "Chọn một trong 3 hồ sơ demo có sẵn hoặc tự nhập thông tin mới. "
        "Các hồ sơ demo đã được thiết kế để minh họa 3 kịch bản khác nhau: "
        "duyệt ưu tiên, duyệt có điều kiện, và từ chối."
    )
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    for i, (col, persona) in enumerate(zip([col1, col2, col3], personas)):
        with col:
            result_map = {
                "approved_priority": ("🟢 Duyệt ưu tiên", "#D9EAD3"),
                "manual_review": ("🟡 Xem xét thủ công", "#FFF2CC"),
                "rejected": ("🔴 Từ chối", "#F4CCCC"),
            }
            label, bg = result_map.get(persona["expected_result"], ("", "#fff"))
            st.markdown(
                f"""<div style="background:{bg};padding:1rem;border-radius:8px;min-height:180px;">
                <h4>Persona {persona['persona_id'][0]}</h4>
                <p><b>{persona['full_name_censored']}</b></p>
                <p style="font-size:0.9rem;">{persona['description']}</p>
                <p><b>{label}</b></p>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(f"Chọn persona {persona['persona_id'][0]}", key=f"pick_{i}", use_container_width=True):
                load_persona_to_state(persona)
                next_step()
                st.rerun()

    with col4:
        st.markdown(
            """<div style="background:#E6F1FB;padding:1rem;border-radius:8px;min-height:180px;">
            <h4>✍️ Nhập tự do</h4>
            <p><b>Hồ sơ mới</b></p>
            <p style="font-size:0.9rem;">Nhập thủ công từng trường thông tin cho một khách hàng mới để hệ thống xét duyệt.</p>
            <p><b>Phù hợp để test hệ thống</b></p>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("Nhập tự do", key="pick_custom", use_container_width=True):
            st.session_state.selected_persona = None
            next_step()
            st.rerun()


# ============================================================
# STEP 1: CREDIT HISTORY
# ============================================================

def render_step1_credit(scorecard):
    st.markdown('<p class="step-label">Bước 1 / 5</p>', unsafe_allow_html=True)
    st.title("Nhóm 1: Lịch sử tín dụng")
    st.caption(f"Trọng số {scorecard['scoring_groups']['credit_history']['weight']*100:.0f}% · "
               f"Tối đa {scorecard['scoring_groups']['credit_history']['max_points']} điểm")

    ch = st.session_state.applicant["credit_history"]

    col1, col2 = st.columns(2)
    with col1:
        ch["credit_history_cic"] = st.selectbox(
            "Lịch sử CIC 24 tháng gần nhất",
            options=["no_history", "group1_all_ontime", "group2_once", "group2_multiple",
                     "group3", "group4", "group5"],
            format_func=lambda x: {
                "no_history": "Không có lịch sử vay",
                "group1_all_ontime": "Nhóm 1 - Trả đúng hạn toàn bộ",
                "group2_once": "Nhóm 2 - Trễ 10-90 ngày 1 lần",
                "group2_multiple": "Nhóm 2 - Trễ nhiều lần",
                "group3": "Nhóm 3 - Nợ dưới chuẩn (LOẠI)",
                "group4": "Nhóm 4 - Nợ nghi ngờ (LOẠI)",
                "group5": "Nhóm 5 - Nợ có khả năng mất vốn (LOẠI)",
            }[x],
            index=1 if not ch.get("credit_history_cic") else ["no_history","group1_all_ontime","group2_once","group2_multiple","group3","group4","group5"].index(ch["credit_history_cic"]),
            help="Theo TT 11/2021/TT-NHNN: Nhóm 3 trở lên bị từ chối ngay",
        )
        ch["active_loans_count"] = st.number_input(
            "Số khoản vay đang hoạt động",
            min_value=0, max_value=20,
            value=ch.get("active_loans_count", 0),
            help="Tổng số khoản vay, thẻ tín dụng còn dư nợ",
        )
    with col2:
        ch["credit_history_length_years"] = st.number_input(
            "Thời gian có lịch sử tín dụng (năm)",
            min_value=0, max_value=50,
            value=ch.get("credit_history_length_years", 0),
        )
        ch["dti_current"] = st.slider(
            "DTI hiện tại (trước khi vay mới)",
            min_value=0.0, max_value=1.0, step=0.01,
            value=ch.get("dti_current", 0.0),
            format="%.2f",
            help="Tỷ lệ tổng nợ phải trả hàng tháng / thu nhập. DTI sau khi vay sẽ tự tính thêm.",
        )

    st.markdown("---")
    st.markdown("### 📎 Upload chứng từ nhóm 1")
    st.caption("Báo cáo CIC cá nhân, hợp đồng tín dụng cũ (nếu có). Nhớ che thông tin cá nhân trước khi upload.")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g1",
    )
    if uploaded:
        st.session_state.uploaded_files["group1"] = [f.name for f in uploaded]
        st.success(f"Đã upload {len(uploaded)} file: {', '.join(f.name for f in uploaded)}")

    # Navigation
    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("← Quay lại", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("Tiếp theo →", type="primary", use_container_width=True):
            next_step()
            st.rerun()


# ============================================================
# STEP 2: INCOME
# ============================================================

def render_step2_income(scorecard):
    st.markdown('<p class="step-label">Bước 2 / 5</p>', unsafe_allow_html=True)
    st.title("Nhóm 2: Thu nhập & việc làm")
    st.caption(f"Trọng số {scorecard['scoring_groups']['income']['weight']*100:.0f}% · "
               f"Tối đa {scorecard['scoring_groups']['income']['max_points']} điểm")

    emp = st.session_state.applicant["employment"]

    col1, col2 = st.columns(2)
    with col1:
        emp["employer"] = st.text_input(
            "Tên công ty / nơi làm việc",
            value=emp.get("employer", ""),
        )
        emp["job_title"] = st.text_input(
            "Chức danh / nghề nghiệp",
            value=emp.get("job_title", ""),
        )
        emp["employment_contract"] = st.selectbox(
            "Loại hợp đồng lao động",
            options=["permanent", "fixed_gte_12m", "fixed_lt_12m", "self_employed_licensed", "freelance"],
            format_func=lambda x: {
                "permanent": "Không thời hạn / biên chế",
                "fixed_gte_12m": "Xác định thời hạn >= 12 tháng",
                "fixed_lt_12m": "Xác định thời hạn < 12 tháng",
                "self_employed_licensed": "Tự doanh có giấy phép KD",
                "freelance": "Lao động tự do",
            }[x],
            index=["permanent","fixed_gte_12m","fixed_lt_12m","self_employed_licensed","freelance"].index(emp.get("employment_contract", "permanent")),
        )
    with col2:
        emp["employment_duration_months"] = st.number_input(
            "Thời gian làm việc tại CTY hiện tại (tháng)",
            min_value=0, max_value=600,
            value=emp.get("employment_duration_months", 12),
        )
        emp["monthly_income_vnd"] = st.number_input(
            "Thu nhập hàng tháng (VNĐ)",
            min_value=0, max_value=500_000_000, step=1_000_000,
            value=emp.get("monthly_income_vnd", 10_000_000),
            help="Thu nhập ròng trung bình 3-6 tháng gần nhất",
        )
        emp["salary_method"] = st.selectbox(
            "Hình thức nhận lương",
            options=["bank_transfer", "cash_verified", "cash_unverified"],
            format_func=lambda x: {
                "bank_transfer": "Chuyển khoản ngân hàng (có sao kê)",
                "cash_verified": "Tiền mặt có xác nhận của công ty",
                "cash_unverified": "Tiền mặt không có xác nhận",
            }[x],
            index=["bank_transfer","cash_verified","cash_unverified"].index(emp.get("salary_method", "bank_transfer")),
        )

    st.markdown("---")
    st.markdown("### 📎 Upload chứng từ nhóm 2")
    st.caption("HĐLĐ, sao kê lương 3-6 tháng, xác nhận công tác, phiếu lương. Nhớ che thông tin cá nhân.")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g2",
    )
    if uploaded:
        st.session_state.uploaded_files["group2"] = [f.name for f in uploaded]
        st.success(f"Đã upload {len(uploaded)} file")

    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("← Quay lại", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("Tiếp theo →", type="primary", use_container_width=True):
            next_step()
            st.rerun()


# ============================================================
# STEP 3: PERSONAL
# ============================================================

def render_step3_personal(scorecard):
    st.markdown('<p class="step-label">Bước 3 / 5</p>', unsafe_allow_html=True)
    st.title("Nhóm 3: Nhân thân")
    st.caption(f"Trọng số {scorecard['scoring_groups']['personal']['weight']*100:.0f}% · "
               f"Tối đa {scorecard['scoring_groups']['personal']['max_points']} điểm")

    p = st.session_state.applicant["personal_info"]

    col1, col2 = st.columns(2)
    with col1:
        p["age"] = st.number_input(
            "Tuổi",
            min_value=16, max_value=90,
            value=p.get("age", 30),
        )
        p["gender"] = st.selectbox(
            "Giới tính",
            options=["male", "female", "other"],
            format_func=lambda x: {"male":"Nam", "female":"Nữ", "other":"Khác"}[x],
            index=["male","female","other"].index(p.get("gender", "male")),
        )
        p["marital_status"] = st.selectbox(
            "Tình trạng hôn nhân",
            options=["single", "married", "divorced_widowed"],
            format_func=lambda x: {"single":"Độc thân", "married":"Đã kết hôn", "divorced_widowed":"Ly hôn / goá"}[x],
            index=["single","married","divorced_widowed"].index(p.get("marital_status", "single")),
        )
    with col2:
        p["dependents"] = st.number_input(
            "Số người phụ thuộc",
            min_value=0, max_value=10,
            value=p.get("dependents", 0),
        )
        p["education"] = st.selectbox(
            "Trình độ học vấn",
            options=["below_highschool", "highschool", "bachelor", "postgrad"],
            format_func=lambda x: {
                "below_highschool":"Dưới THPT",
                "highschool":"THPT / Trung cấp",
                "bachelor":"Đại học / Cao đẳng",
                "postgrad":"Sau đại học",
            }[x],
            index=["below_highschool","highschool","bachelor","postgrad"].index(p.get("education", "bachelor")),
        )
        p["residency_status"] = st.selectbox(
            "Tình trạng cư trú",
            options=["owner", "family_home", "renting_gte_2y", "renting_lt_2y"],
            format_func=lambda x: {
                "owner":"Sở hữu nhà (có sổ đỏ)",
                "family_home":"Ở nhà gia đình (có hộ khẩu)",
                "renting_gte_2y":"Thuê nhà >= 2 năm",
                "renting_lt_2y":"Thuê nhà < 2 năm",
            }[x],
            index=["owner","family_home","renting_gte_2y","renting_lt_2y"].index(p.get("residency_status", "family_home")),
        )

    st.markdown("---")
    st.markdown("### 📎 Upload chứng từ nhóm 3")
    st.caption("CCCD/CMND, sổ hộ khẩu, giấy đăng ký kết hôn, giấy khai sinh con (nếu có).")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g3",
    )
    if uploaded:
        st.session_state.uploaded_files["group3"] = [f.name for f in uploaded]
        st.success(f"Đã upload {len(uploaded)} file")

    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("← Quay lại", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("Tiếp theo →", type="primary", use_container_width=True):
            next_step()
            st.rerun()


# ============================================================
# STEP 4: ASSETS + LOAN
# ============================================================

def render_step4_assets_loan(scorecard):
    st.markdown('<p class="step-label">Bước 4 / 5</p>', unsafe_allow_html=True)
    st.title("Nhóm 4: Tài sản & Thông tin khoản vay")

    a = st.session_state.applicant["assets"]
    loan = st.session_state.applicant["loan_request"]

    st.markdown("### Tài sản sở hữu")
    st.caption(f"Trọng số {scorecard['scoring_groups']['assets']['weight']*100:.0f}% · "
               f"Tối đa {scorecard['scoring_groups']['assets']['max_points']} điểm")

    col1, col2, col3 = st.columns(3)
    with col1:
        a["real_estate"] = st.selectbox(
            "Bất động sản đứng tên",
            options=["none", "family_shared", "owned_titled"],
            format_func=lambda x: {
                "none":"Không có BĐS",
                "family_shared":"Đồng sở hữu với gia đình",
                "owned_titled":"Sở hữu, có sổ đỏ",
            }[x],
            index=["none","family_shared","owned_titled"].index(a.get("real_estate", "none")),
        )
    with col2:
        a["vehicle"] = st.selectbox(
            "Phương tiện đi lại",
            options=["none", "motorbike", "car"],
            format_func=lambda x: {"none":"Không có", "motorbike":"Xe máy", "car":"Ô tô"}[x],
            index=["none","motorbike","car"].index(a.get("vehicle", "motorbike")),
        )
    with col3:
        a["savings_vnd"] = st.number_input(
            "Tiền gửi tiết kiệm (VNĐ)",
            min_value=0, max_value=10_000_000_000, step=5_000_000,
            value=a.get("savings_vnd", 0),
        )

    st.markdown("---")
    st.markdown("### 💰 Thông tin khoản vay mong muốn")

    col1, col2 = st.columns(2)
    with col1:
        loan["vehicle_name"] = st.text_input(
            "Tên xe muốn mua",
            value=loan.get("vehicle_name", "Honda Vision 2025"),
        )
        loan["vehicle_price_vnd"] = st.number_input(
            "Giá xe (VNĐ)",
            min_value=5_000_000, max_value=200_000_000, step=1_000_000,
            value=loan.get("vehicle_price_vnd", 34_000_000),
        )
        loan["down_payment_vnd"] = st.number_input(
            "Số tiền trả trước (VNĐ)",
            min_value=0, max_value=loan.get("vehicle_price_vnd", 34_000_000), step=500_000,
            value=loan.get("down_payment_vnd", 4_000_000),
            help="Tối thiểu 20% giá xe",
        )
    with col2:
        loan["loan_amount_vnd"] = loan["vehicle_price_vnd"] - loan["down_payment_vnd"]
        st.metric("Số tiền cần vay", f"{loan['loan_amount_vnd']:,} VNĐ")
        loan["term_months"] = st.selectbox(
            "Kỳ hạn vay",
            options=[6, 9, 12, 18, 24, 36],
            index=[6,9,12,18,24,36].index(loan.get("term_months", 12)) if loan.get("term_months", 12) in [6,9,12,18,24,36] else 2,
            format_func=lambda x: f"{x} tháng",
        )
        down_ratio = loan["down_payment_vnd"] / max(loan["vehicle_price_vnd"], 1)
        if down_ratio < 0.20:
            st.warning(f"⚠️ Trả trước {down_ratio*100:.1f}% — dưới ngưỡng tối thiểu 20%")

    st.markdown("---")
    st.markdown("### 📎 Upload chứng từ nhóm 4")
    st.caption("Sổ đỏ, cà vẹt xe, sổ tiết kiệm, hợp đồng thuê nhà (nếu có).")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g4",
    )
    if uploaded:
        st.session_state.uploaded_files["group4"] = [f.name for f in uploaded]
        st.success(f"Đã upload {len(uploaded)} file")

    col_l, col_r = st.columns([1, 1])
    with col_l:
        if st.button("← Quay lại", use_container_width=True):
            prev_step()
            st.rerun()
    with col_r:
        if st.button("🔍 Chạy xét duyệt", type="primary", use_container_width=True):
            next_step()
            st.rerun()


# ============================================================
# STEP 5: RESULT
# ============================================================

def render_step5_result(scorecard):
    st.markdown('<p class="step-label">Bước 5 / 5</p>', unsafe_allow_html=True)
    st.title("Kết quả xét duyệt")

    pipeline = get_pipeline()
    persona_data = st.session_state.applicant.copy()
    persona_data["persona_id"] = st.session_state.selected_persona or "custom_input"

    decision = pipeline.evaluate(persona_data)

    # --- Summary card ---
    decision_map = {
        "approved_priority": ("🟢 DUYỆT ƯU TIÊN", "pass-card", "#27500A"),
        "approved": ("🟢 DUYỆT", "pass-card", "#27500A"),
        "approved_conditional": ("🟡 DUYỆT CÓ ĐIỀU KIỆN", "warn-card", "#633806"),
        "manual_review": ("🟡 XEM XÉT THỦ CÔNG", "warn-card", "#633806"),
        "rejected": ("🔴 TỪ CHỐI", "fail-card", "#791F1F"),
    }
    label, css_class, text_color = decision_map.get(
        decision.final_decision, ("", "warn-card", "#333")
    )

    st.markdown(
        f"""<div class="result-card {css_class}">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <h2 style="color:{text_color};margin:0;">{label}</h2>
            <p style="color:{text_color};margin:0.5rem 0;">
              Hồ sơ: {persona_data['persona_id']}
            </p>
          </div>
          <div style="text-align:right;">
            <p class="big-score" style="color:{text_color};">
              {decision.scoring_result.total_points if decision.scoring_result else '—'}
              <span style="font-size:1.5rem;">/ {scorecard['scoring_system']['max_score']}</span>
            </p>
            <p style="color:{text_color};margin:0;">
              Hạng: <b>{decision.grade_result.grade if decision.grade_result else 'N/A'}</b>
            </p>
          </div>
        </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # --- Tabs for details ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🛡️ Hard Rules",
        "📊 Điểm chi tiết",
        "💵 Phương án trả nợ",
        "📎 Chứng từ đã upload",
    ])

    # Tab 1: Hard Rules
    with tab1:
        st.subheader("Kết quả kiểm tra 6 điều kiện loại trực tiếp")
        for check in decision.hard_rules_result.checks:
            icon = "✅" if check.passed else "❌"
            color = "green" if check.passed else "red"
            st.markdown(
                f"**{icon} {check.description}**  \n"
                f":{color}[Giá trị thực tế: `{check.actual_value}` · Ngưỡng: `{check.threshold}`]"
            )

        if not decision.hard_rules_result.all_passed:
            st.error("Hồ sơ vi phạm hard rules — từ chối ngay, không chấm điểm.")
            st.markdown("**Lý do từ chối:**")
            for reason in decision.rejection_reasons:
                st.markdown(f"- {reason}")

    # Tab 2: Scoring detail
    with tab2:
        if decision.scoring_result is None:
            st.info("Hồ sơ bị từ chối ở bước hard rules, không chấm điểm.")
        else:
            render_scoring_detail(decision.scoring_result)

    # Tab 3: Repayment plans
    with tab3:
        if decision.grade_result is None or decision.grade_result.interest_rate_annual is None:
            st.info("Hồ sơ bị từ chối, không tính phương án trả nợ.")
        else:
            render_repayment_plans(
                persona_data["loan_request"]["loan_amount_vnd"],
                decision.grade_result.interest_rate_annual,
                persona_data["loan_request"]["term_months"],
            )

    # Tab 4: Uploaded documents
    with tab4:
        st.subheader("Danh sách chứng từ đã upload")
        total = 0
        for group_key, label in [
            ("group1", "Nhóm 1 - Lịch sử tín dụng"),
            ("group2", "Nhóm 2 - Thu nhập"),
            ("group3", "Nhóm 3 - Nhân thân"),
            ("group4", "Nhóm 4 - Tài sản"),
        ]:
            files = st.session_state.uploaded_files.get(group_key, [])
            with st.expander(f"{label} ({len(files)} file)"):
                if files:
                    for f in files:
                        st.markdown(f"- 📄 {f}")
                    total += len(files)
                else:
                    st.caption("Chưa upload file nào")
        st.markdown(f"**Tổng số file đã upload: {total}**")

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Sửa thông tin", use_container_width=True):
            prev_step()
            st.rerun()
    with col2:
        if st.button("🔄 Xét duyệt hồ sơ khác", type="primary", use_container_width=True):
            reset_state()
            st.rerun()


def render_scoring_detail(scoring_result):
    # Overview bar chart
    group_data = pd.DataFrame([
        {
            "Nhóm": g.group_name,
            "Điểm đạt": g.points,
            "Điểm tối đa": g.max_points,
            "Tỷ lệ": g.ratio * 100,
        }
        for g in scoring_result.groups
    ])

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Điểm theo từng nhóm")
        st.bar_chart(
            group_data.set_index("Nhóm")[["Điểm đạt", "Điểm tối đa"]],
            height=300,
        )
    with col2:
        st.subheader("Tổng quan")
        st.metric(
            "Tổng điểm",
            f"{scoring_result.total_points}/{scoring_result.max_total_points}",
            f"{scoring_result.ratio*100:.1f}%",
        )
        for g in scoring_result.groups:
            st.caption(f"{g.group_name}: **{g.points}/{g.max_points}** ({g.ratio*100:.0f}%)")

    # Detail table per group
    st.markdown("---")
    st.subheader("Chi tiết từng biến")
    for group in scoring_result.groups:
        with st.expander(f"{group.group_name} — {group.points}/{group.max_points} điểm"):
            df = pd.DataFrame([
                {
                    "Biến": v.variable_name,
                    "Giá trị thực tế": str(v.actual_value),
                    "Điểm đạt": v.points,
                    "Điểm tối đa": v.max_points,
                    "Tỷ lệ": f"{(v.points/v.max_points*100) if v.max_points>0 else 0:.0f}%",
                }
                for v in group.variables
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)


def render_repayment_plans(loan_amount, annual_rate, term_months):
    plans = calculate_both_plans(loan_amount, annual_rate, term_months)
    p1 = plans["plan_1_annuity"]
    p2 = plans["plan_2_equal_principal"]

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Số tiền vay", f"{loan_amount:,.0f} VNĐ")
    with col2:
        st.metric("Lãi suất", f"{annual_rate*100:.1f}%/năm")
    with col3:
        st.metric("Kỳ hạn", f"{term_months} tháng")
    with col4:
        saving = p1.total_interest - p2.total_interest
        st.metric("PA2 tiết kiệm so với PA1", f"{saving:,.0f} VNĐ")

    st.markdown("---")

    # Two columns: plan 1 vs plan 2
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📘 PA1: Niên kim (gốc + lãi đều)")
        st.caption("Số tiền trả mỗi kỳ bằng nhau. Dòng tiền ổn định.")
        df1 = schedule_to_df(p1)
        st.dataframe(df1, use_container_width=True, hide_index=True, height=280)
        st.info(f"**Tổng lãi:** {p1.total_interest:,.0f} VNĐ  \n"
                f"**Tổng phải trả:** {p1.total_paid:,.0f} VNĐ")

    with col2:
        st.subheader("📙 PA2: Gốc đều + lãi dư nợ đầu kỳ")
        st.caption("Gốc cố định, lãi giảm dần. Tổng lãi thấp hơn PA1.")
        df2 = schedule_to_df(p2)
        st.dataframe(df2, use_container_width=True, hide_index=True, height=280)
        st.info(f"**Tổng lãi:** {p2.total_interest:,.0f} VNĐ  \n"
                f"**Tổng phải trả:** {p2.total_paid:,.0f} VNĐ")

    # Comparison chart
    st.markdown("---")
    st.subheader("📈 So sánh dòng tiền trả mỗi kỳ")
    compare_df = pd.DataFrame({
        "Kỳ": [p.period for p in p1.payments],
        "PA1 - Niên kim": [p.total_payment for p in p1.payments],
        "PA2 - Gốc đều": [p.total_payment for p in p2.payments],
    }).set_index("Kỳ")
    st.line_chart(compare_df, height=280)

    # Download buttons
    st.markdown("---")
    st.subheader("📥 Tải bảng lịch trả nợ")
    col1, col2 = st.columns(2)
    with col1:
        excel_bytes = export_to_excel(p1, p2, loan_amount, annual_rate, term_months)
        st.download_button(
            "📊 Tải file Excel (cả 2 phương án)",
            data=excel_bytes,
            file_name=f"lich_tra_no_{loan_amount//1_000_000}trieu_{term_months}thang.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col2:
        csv1 = df1.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📄 Tải CSV (chỉ PA1)",
            data=csv1,
            file_name="pa1_nien_kim.csv",
            mime="text/csv",
            use_container_width=True,
        )


def schedule_to_df(schedule):
    return pd.DataFrame([
        {
            "Kỳ": p.period,
            "Dư nợ đầu kỳ": f"{p.opening_balance:,.0f}",
            "Gốc": f"{p.principal:,.0f}",
            "Lãi": f"{p.interest:,.0f}",
            "Tổng trả": f"{p.total_payment:,.0f}",
            "Dư nợ cuối": f"{p.closing_balance:,.0f}",
        }
        for p in schedule.payments
    ])


def export_to_excel(p1, p2, loan_amount, annual_rate, term_months):
    """Xuất cả 2 phương án sang file Excel 2 sheet."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Summary
        summary = pd.DataFrame([
            {"Thông số": "Số tiền vay", "Giá trị": f"{loan_amount:,.0f} VNĐ"},
            {"Thông số": "Lãi suất/năm", "Giá trị": f"{annual_rate*100:.1f}%"},
            {"Thông số": "Kỳ hạn", "Giá trị": f"{term_months} tháng"},
            {"Thông số": "PA1 - Tổng lãi", "Giá trị": f"{p1.total_interest:,.0f} VNĐ"},
            {"Thông số": "PA1 - Tổng phải trả", "Giá trị": f"{p1.total_paid:,.0f} VNĐ"},
            {"Thông số": "PA2 - Tổng lãi", "Giá trị": f"{p2.total_interest:,.0f} VNĐ"},
            {"Thông số": "PA2 - Tổng phải trả", "Giá trị": f"{p2.total_paid:,.0f} VNĐ"},
            {"Thông số": "PA2 tiết kiệm so với PA1", "Giá trị": f"{p1.total_interest - p2.total_interest:,.0f} VNĐ"},
        ])
        summary.to_excel(writer, sheet_name="Tổng hợp", index=False)

        # Sheet 2: PA1
        df1 = pd.DataFrame([
            {
                "Kỳ": p.period,
                "Dư nợ đầu kỳ": p.opening_balance,
                "Gốc": p.principal,
                "Lãi": p.interest,
                "Tổng trả": p.total_payment,
                "Dư nợ cuối": p.closing_balance,
            }
            for p in p1.payments
        ])
        df1.to_excel(writer, sheet_name="PA1 - Niên kim", index=False)

        # Sheet 3: PA2
        df2 = pd.DataFrame([
            {
                "Kỳ": p.period,
                "Dư nợ đầu kỳ": p.opening_balance,
                "Gốc": p.principal,
                "Lãi": p.interest,
                "Tổng trả": p.total_payment,
                "Dư nợ cuối": p.closing_balance,
            }
            for p in p2.payments
        ])
        df2.to_excel(writer, sheet_name="PA2 - Gốc đều", index=False)

    output.seek(0)
    return output.getvalue()


# ============================================================
# MAIN
# ============================================================

def main():
    init_state()
    scorecard = load_scorecard()
    personas = load_personas()

    render_sidebar(scorecard)

    # Route to current step
    step = st.session_state.step
    if step == 0:
        render_step0_choose(personas)
    elif step == 1:
        render_step1_credit(scorecard)
    elif step == 2:
        render_step2_income(scorecard)
    elif step == 3:
        render_step3_personal(scorecard)
    elif step == 4:
        render_step4_assets_loan(scorecard)
    elif step == 5:
        render_step5_result(scorecard)


if __name__ == "__main__":
    main()
