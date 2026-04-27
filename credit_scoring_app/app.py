"""
Streamlit App v3 - Hệ thống xét duyệt hồ sơ vay tiêu dùng cá nhân
UI: Navy + Gold, banking dashboard style.

v3 changes (4 feedback):
  1. Bước 0.5 mới - Khởi tạo hồ sơ (nhập tên + mã hồ sơ)
  2. Dashboard kết quả gọn - 1 view duy nhất, không cần click tab
  3. Giải thích lãi suất khoa học - công thức NHNN + biên rủi ro
  4. Slider lãi suất dynamic - bảng PMT cập nhật real-time

Wizard 7 bước:
  0 - Chọn hồ sơ (preset hoặc tự do)
  0.5 - Khởi tạo hồ sơ (tên, mã hồ sơ)  ← v3 NEW
  1 - Lịch sử tín dụng
  2 - Thu nhập & việc làm
  3 - Nhân thân
  4 - Tài sản & khoản vay
  5 - Kết quả

Chạy: streamlit run app.py
"""

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from engine import CreditScoringPipeline, calculate_both_plans


@st.cache_data(show_spinner=False)
def cached_calculate_both_plans(principal: float, annual_rate: float, term_months: int):
    """Cached version - tránh tính lại khi slider trigger rerun với cùng giá trị."""
    return calculate_both_plans(principal, annual_rate, term_months)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).parent
SCORECARD_PATH = BASE_DIR / "data" / "scorecard.json"
PERSONAS_PATH = BASE_DIR / "data" / "personas.json"

st.set_page_config(
    page_title="Hệ thống xét duyệt tín dụng",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS - Navy + Gold (giữ từ v2)
# ============================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    :root {
        --navy: #0A2540;
        --navy-light: #1B3A5C;
        --gold: #C9A961;
        --gold-light: #E0C988;
        --bg-soft: #F5F7FA;
        --text-primary: #0A2540;
        --text-secondary: #5A6B80;
        --success: #0F7A5C;
        --warning: #B87300;
        --danger: #B33A3A;
    }

    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    h1, h2, h3, h4 {
        color: var(--navy) !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    h1 { font-size: 1.75rem !important; }
    h2 { font-size: 1.4rem !important; }
    h3 { font-size: 1.15rem !important; }

    .hero-header {
        background: linear-gradient(135deg, #0A2540 0%, #1B3A5C 100%);
        color: white;
        padding: 1.75rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 12px rgba(10, 37, 64, 0.08);
    }
    .hero-header h1 {
        color: white !important;
        margin: 0 0 0.3rem 0 !important;
        font-size: 1.65rem !important;
    }
    .hero-header p {
        color: #D4DCE8;
        margin: 0;
        font-size: 0.95rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(201, 169, 97, 0.2);
        color: #E0C988;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-secondary);
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    .step-indicator .step-dot {
        width: 6px;
        height: 6px;
        background: var(--gold);
        border-radius: 50%;
    }

    .persona-card {
        background: white;
        border: 1px solid #E5E9F0;
        border-radius: 12px;
        padding: 1.25rem;
        height: 230px;
        transition: all 0.2s ease;
        display: flex;
        flex-direction: column;
    }
    .persona-card:hover {
        border-color: var(--gold);
        box-shadow: 0 4px 16px rgba(201, 169, 97, 0.15);
        transform: translateY(-2px);
    }
    .persona-card-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .persona-card-name {
        font-weight: 600;
        color: var(--navy);
        font-size: 1.05rem;
        margin-bottom: 0.3rem;
    }
    .persona-card-desc {
        color: var(--text-secondary);
        font-size: 0.85rem;
        line-height: 1.45;
        flex-grow: 1;
    }
    .persona-card-badge {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        display: inline-block;
    }
    .badge-approved { background: #E3F4EC; color: var(--success); }
    .badge-review   { background: #FFF4DB; color: var(--warning); }
    .badge-rejected { background: #FCE4E4; color: var(--danger); }
    .badge-custom   { background: #E8EEF5; color: var(--navy); }

    .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-left: 3px solid var(--gold);
        padding-left: 0.75rem;
        color: var(--navy);
        font-weight: 600;
        font-size: 1.1rem;
        margin: 1.5rem 0 1rem 0;
    }

    .stButton > button {
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--navy) !important;
        color: white !important;
        border: 1px solid var(--navy) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--navy-light) !important;
        border-color: var(--gold) !important;
        box-shadow: 0 2px 8px rgba(10, 37, 64, 0.15) !important;
    }
    .stButton > button[kind="secondary"] {
        background: white !important;
        color: var(--navy) !important;
        border: 1px solid #E5E9F0 !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--navy) !important;
        background: var(--bg-soft) !important;
    }

    /* v3: Result dashboard hero - bigger and gold accent */
    .dashboard-hero {
        background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%);
        border: 1px solid #E5E9F0;
        border-top: 4px solid;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(10, 37, 64, 0.06);
    }
    .dashboard-hero.approved { border-top-color: var(--success); }
    .dashboard-hero.review   { border-top-color: var(--warning); }
    .dashboard-hero.rejected { border-top-color: var(--danger); }

    .dashboard-grid {
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 2rem;
        align-items: center;
    }

    .gauge-section {
        text-align: center;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        border: 1px solid #E5E9F0;
    }
    .gauge-number {
        font-size: 4rem;
        font-weight: 700;
        line-height: 1;
        color: var(--navy);
        letter-spacing: -0.03em;
    }
    .gauge-suffix {
        font-size: 1.4rem;
        color: var(--text-secondary);
        font-weight: 400;
    }
    .gauge-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
        font-weight: 500;
    }
    .gauge-grade {
        display: inline-block;
        background: var(--navy);
        color: var(--gold);
        padding: 0.4rem 1rem;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.1rem;
        letter-spacing: 0.05em;
        margin-top: 0.75rem;
    }

    .info-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
    }
    .info-item {
        background: white;
        border: 1px solid #E5E9F0;
        border-radius: 8px;
        padding: 0.85rem 1rem;
    }
    .info-item-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .info-item-value {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--navy);
    }
    .info-item-value.gold { color: var(--gold); }
    .info-item-value.success { color: var(--success); }
    .info-item-value.danger { color: var(--danger); }

    .result-status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .status-approved { background: #E3F4EC; color: var(--success); }
    .status-review   { background: #FFF4DB; color: var(--warning); }
    .status-rejected { background: #FCE4E4; color: var(--danger); }

    /* v3: Quick summary section */
    .quick-summary {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .summary-card {
        background: white;
        border: 1px solid #E5E9F0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
    }
    .summary-card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--navy);
        margin-bottom: 0.6rem;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid #E5E9F0;
    }
    .summary-card-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        padding: 0.25rem 0;
    }
    .summary-card-row .label {
        color: var(--text-secondary);
    }
    .summary-card-row .value {
        color: var(--navy);
        font-weight: 500;
    }

    /* v3: Interest rate explanation card */
    .rate-explain-card {
        background: linear-gradient(135deg, #FDFAF2 0%, #FFFFFF 100%);
        border: 1px solid var(--gold-light);
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin: 1rem 0;
    }
    .rate-formula {
        background: white;
        border: 1px dashed var(--gold);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin: 0.75rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: var(--navy);
    }
    .rate-component {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        font-size: 0.88rem;
        border-bottom: 1px dotted #E5E9F0;
    }
    .rate-component:last-child {
        border-bottom: 2px solid var(--gold);
        padding-top: 0.6rem;
        margin-top: 0.3rem;
        font-weight: 600;
    }
    .rate-component .label { color: var(--text-secondary); }
    .rate-component .value { color: var(--navy); font-weight: 500; }
    .rate-component:last-child .value { color: var(--gold); font-size: 1.05rem; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-bottom: 1px solid #E5E9F0;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        padding: 0.75rem 1.25rem !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--navy) !important;
        border-bottom: 2px solid var(--gold) !important;
    }

    section[data-testid="stSidebar"] {
        background: var(--navy) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #D4DCE8 !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: white !important;
    }

    .stepper-item {
        position: relative;
        padding: 0.5rem 0 0.5rem 1.5rem;
        font-size: 0.9rem;
    }
    .stepper-item::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0.75rem;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #2D4A6B;
        border: 2px solid #2D4A6B;
    }
    .stepper-item.done::before {
        background: var(--gold);
        border-color: var(--gold);
    }
    .stepper-item.current::before {
        background: var(--gold);
        border-color: var(--gold);
        box-shadow: 0 0 0 3px rgba(201, 169, 97, 0.3);
    }
    .stepper-item::after {
        content: '';
        position: absolute;
        left: 4px;
        top: 1.4rem;
        bottom: -0.4rem;
        width: 2px;
        background: #2D4A6B;
    }
    .stepper-item:last-child::after { display: none; }
    .stepper-item.done::after { background: var(--gold); }
    .stepper-item.current { color: white !important; font-weight: 500; }
    .stepper-item.pending { color: #8593A8 !important; }

    [data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    .stDataFrame {
        border: 1px solid #E5E9F0 !important;
        border-radius: 8px !important;
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
# STATE MANAGEMENT - v3 thêm profile_meta cho tên/mã hồ sơ
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
    # v3: thêm profile_meta cho thông tin định danh hồ sơ
    if "profile_meta" not in st.session_state:
        st.session_state.profile_meta = {
            "full_name": "",
            "cccd_number": "",
            "profile_id": "",
            "submission_date": datetime.now().strftime("%d/%m/%Y"),
        }
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {
            "group1": [], "group2": [], "group3": [], "group4": [],
        }
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None
    # v3: state cho slider lãi suất tự chọn
    if "selected_rate" not in st.session_state:
        st.session_state.selected_rate = None


def reset_state():
    keys_to_clear = ["step", "applicant", "profile_meta", "uploaded_files",
                     "selected_persona", "selected_rate",
                     "calc_loan_amount", "calc_term_months",
                     "rate_slider", "amount_slider", "term_slider"]
    for key in keys_to_clear:
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
    # v3: tự fill tên + mã hồ sơ từ persona
    persona_letter = persona["persona_id"][0]
    # Sample CCCD đã censor cho persona preset (chỉ minh họa, đã che)
    sample_cccd = {"A": "001094XXXXXX", "B": "038099XXXXXX", "C": "042081XXXXXX"}
    st.session_state.profile_meta = {
        "full_name": persona["full_name_censored"],
        "cccd_number": sample_cccd.get(persona_letter, ""),
        "profile_id": f"HS-{persona_letter}-{datetime.now().strftime('%Y%m%d')}",
        "submission_date": datetime.now().strftime("%d/%m/%Y"),
    }


def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1


# ============================================================
# HERO HEADER
# ============================================================

def render_hero(scorecard):
    st.markdown(f"""
    <div class="hero-header">
        <div class="hero-badge">Credit Scoring System · Vietnam</div>
        <h1>🏛️ Hệ thống xét duyệt tín dụng</h1>
        <p>{scorecard['product']['name']} · Tự động hóa quy trình chấm điểm theo chuẩn quốc tế</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# SIDEBAR - v3 thêm bước 0.5 vào stepper
# ============================================================

def render_sidebar(scorecard):
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0 1.5rem 0; border-bottom:1px solid #2D4A6B; margin-bottom:1rem;">
            <div style="font-size:2rem;">🏛️</div>
            <div style="font-weight:600; color:white; margin-top:0.3rem;">Credit Scoring</div>
            <div style="font-size:0.8rem; color:#8593A8;">Vietnam Consumer Loan</div>
        </div>
        """, unsafe_allow_html=True)

        # v3: 7 bước thay vì 6
        steps = [
            ("Chọn hồ sơ", "Bước 0"),
            ("Khởi tạo hồ sơ", "Bước 0.5"),
            ("Lịch sử tín dụng", "Bước 1"),
            ("Thu nhập & việc làm", "Bước 2"),
            ("Nhân thân", "Bước 3"),
            ("Tài sản & khoản vay", "Bước 4"),
            ("Kết quả xét duyệt", "Bước 5"),
        ]

        st.markdown("### Tiến trình")
        stepper_html = '<div>'
        for i, (label, sub) in enumerate(steps):
            if i < st.session_state.step:
                cls = "done"
            elif i == st.session_state.step:
                cls = "current"
            else:
                cls = "pending"
            stepper_html += f"""
            <div class="stepper-item {cls}">
                <div style="font-size:0.7rem; opacity:0.7;">{sub}</div>
                {label}
            </div>"""
        stepper_html += "</div>"
        st.markdown(stepper_html, unsafe_allow_html=True)

        # v3: Hiển thị tên/mã hồ sơ nếu đã có
        if st.session_state.profile_meta.get("full_name"):
            st.markdown(f"""
            <div style="margin-top:1.5rem; padding:0.75rem; background:#1B3A5C; border-radius:8px; border-left:3px solid var(--gold);">
                <div style="font-size:0.7rem; color:#8593A8; text-transform:uppercase; letter-spacing:0.05em;">Đang xét duyệt</div>
                <div style="font-weight:600; color:white; margin-top:0.2rem;">{st.session_state.profile_meta['full_name']}</div>
                <div style="font-size:0.78rem; color:#D4DCE8; margin-top:0.2rem;">{st.session_state.profile_meta['profile_id']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Làm lại từ đầu", use_container_width=True, type="secondary"):
            reset_state()
            st.rerun()

        st.markdown("---")
        st.markdown("### Scorecard")
        st.markdown(f"""
        <div style="font-size:0.85rem; color:#D4DCE8;">
            <div style="margin-bottom:0.5rem;">Thang điểm: <b>{scorecard['scoring_system']['max_score']}</b></div>
        """, unsafe_allow_html=True)
        for key, group in scorecard["scoring_groups"].items():
            st.markdown(
                f'<div style="font-size:0.82rem; margin:0.2rem 0;">• {group["name"]}: <b>{group["weight"]*100:.0f}%</b></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# v3 helper: step header
# ============================================================

def render_step_header(step_num, total, title, subtitle, icon=""):
    st.markdown(f'<div class="step-indicator"><span class="step-dot"></span>Bước {step_num} / {total}</div>',
                unsafe_allow_html=True)
    st.markdown(f"## {icon} {title}")
    if subtitle:
        st.markdown(
            f'<p style="color:#5A6B80; margin-bottom:1.5rem;">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def render_section(title, icon=""):
    st.markdown(
        f'<div class="section-title">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


def render_nav_buttons(next_label="Tiếp theo →", allow_back=True):
    col_l, _, col_r = st.columns([1, 2, 1])
    with col_l:
        if allow_back and st.button("← Quay lại", use_container_width=True, type="secondary"):
            prev_step()
            st.rerun()
    with col_r:
        if st.button(next_label, type="primary", use_container_width=True):
            next_step()
            st.rerun()


# ============================================================
# STEP 0: CHOOSE PERSONA
# ============================================================

def render_step0_choose(personas, scorecard):
    render_hero(scorecard)
    st.markdown('<div class="step-indicator"><span class="step-dot"></span>Bước 0 / 6 · Khởi tạo</div>',
                unsafe_allow_html=True)
    st.markdown("## Chọn hồ sơ vay")
    st.markdown(
        "<p style='color:#5A6B80; margin-bottom:1.5rem;'>"
        "Chọn một trong 3 hồ sơ demo có sẵn để xét duyệt nhanh, hoặc nhập thủ công hồ sơ mới. "
        "Các hồ sơ demo được thiết kế để minh họa 3 kịch bản: duyệt ưu tiên, duyệt có điều kiện, và từ chối."
        "</p>",
        unsafe_allow_html=True,
    )

    persona_meta = [
        {"icon": "🟢", "badge": "Duyệt ưu tiên", "badge_cls": "badge-approved"},
        {"icon": "🟡", "badge": "Xem xét thủ công", "badge_cls": "badge-review"},
        {"icon": "🔴", "badge": "Từ chối", "badge_cls": "badge-rejected"},
    ]

    cols = st.columns(4)
    for i, (col, persona) in enumerate(zip(cols[:3], personas)):
        with col:
            meta = persona_meta[i]
            st.markdown(f"""
            <div class="persona-card">
                <div class="persona-card-icon">{meta['icon']}</div>
                <div class="persona-card-name">Persona {persona['persona_id'][0]}</div>
                <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.5rem;">
                    {persona['full_name_censored']}
                </div>
                <div class="persona-card-desc">{persona['description']}</div>
                <div class="persona-card-badge {meta['badge_cls']}">{meta['badge']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Chọn hồ sơ {persona['persona_id'][0]}", key=f"pick_{i}",
                         use_container_width=True, type="primary"):
                load_persona_to_state(persona)
                next_step()
                st.rerun()

    with cols[3]:
        st.markdown("""
        <div class="persona-card">
            <div class="persona-card-icon">✍️</div>
            <div class="persona-card-name">Nhập tự do</div>
            <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.5rem;">
                Hồ sơ mới
            </div>
            <div class="persona-card-desc">
                Nhập thủ công từng trường thông tin cho khách hàng mới.
                Bước tiếp theo bạn sẽ nhập tên và mã hồ sơ.
            </div>
            <div class="persona-card-badge badge-custom">Tùy chỉnh</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Nhập mới", key="pick_custom", use_container_width=True, type="primary"):
            st.session_state.selected_persona = None
            # Reset profile_meta để bước 0.5 nhập mới
            st.session_state.profile_meta = {
                "full_name": "",
                "profile_id": f"HS-CUSTOM-{datetime.now().strftime('%Y%m%d%H%M')}",
                "submission_date": datetime.now().strftime("%d/%m/%Y"),
            }
            next_step()
            st.rerun()


# ============================================================
# STEP 0.5 (v3 NEW): KHỞI TẠO HỒ SƠ
# ============================================================

def render_step_init_profile():
    render_step_header(
        "0.5", 6,
        "Khởi tạo hồ sơ",
        "Nhập thông tin định danh cho hồ sơ trước khi tiến hành kê khai chi tiết",
        "🪪"
    )

    pm = st.session_state.profile_meta

    # v3: Auto-generate profile_id nếu chưa có
    if not pm.get("profile_id"):
        pm["profile_id"] = f"HS-CUSTOM-{datetime.now().strftime('%Y%m%d%H%M')}"

    render_section("Thông tin định danh hồ sơ", "📝")

    col1, col2 = st.columns(2)
    with col1:
        pm["full_name"] = st.text_input(
            "Họ và tên khách hàng *",
            value=pm.get("full_name", ""),
            placeholder="Ví dụ: Nguyễn Văn An",
            help="Họ tên đầy đủ theo CMND/CCCD. Trên báo cáo sẽ hiển thị che mã hoá.",
        )
        pm["cccd_number"] = st.text_input(
            "Số CCCD / CMND *",
            value=pm.get("cccd_number", ""),
            placeholder="Ví dụ: 001094XXXXXX",
            max_chars=12,
            help="Số CCCD 12 chữ số hoặc CMND 9 chữ số. Nên che 6 số cuối bằng X để bảo mật.",
        )
        pm["profile_id"] = st.text_input(
            "Mã hồ sơ vay",
            value=pm.get("profile_id", ""),
            help="Mã định danh nội bộ cho hồ sơ vay này",
        )
    with col2:
        pm["submission_date"] = st.text_input(
            "Ngày nộp hồ sơ",
            value=pm.get("submission_date", datetime.now().strftime("%d/%m/%Y")),
        )
        st.markdown(f"""
        <div style="background:#FDFAF2; padding:0.85rem 1rem; border-radius:8px;
                    border-left:3px solid var(--gold); margin-top:1rem;">
            <div style="font-size:0.78rem; color:var(--text-secondary); font-weight:500;">Trạng thái</div>
            <div style="font-weight:600; color:var(--navy); margin-top:0.2rem;">📋 Đang khởi tạo</div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.4rem;">
                Sau khi hoàn tất, hồ sơ sẽ tự động chuyển sang giai đoạn xét duyệt
            </div>
        </div>
        <div style="background:#E8EEF5; padding:0.75rem 1rem; border-radius:8px;
                    border-left:3px solid var(--navy); margin-top:0.6rem;">
            <div style="font-size:0.8rem; color:var(--navy); line-height:1.5;">
                <b>🔒 Bảo mật:</b> Số CCCD/CMND chỉ dùng để định danh hồ sơ.
                Khuyến nghị che 6 ký tự cuối (ví dụ: 001094XXXXXX).
            </div>
        </div>
        """, unsafe_allow_html=True)

    # v3: Hiển thị summary card với data đã nhập
    if pm.get("full_name"):
        cccd_display = pm.get("cccd_number") or "—"
        st.markdown(f"""
        <div style="background:white; border:1px solid #E5E9F0; border-radius:10px;
                    padding:1.25rem 1.5rem; margin-top:1.5rem;">
            <div style="font-size:0.78rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.05em; margin-bottom:0.5rem;">Tóm tắt thông tin hồ sơ</div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:1rem;">
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">Khách hàng</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem;">{pm['full_name']}</div>
                </div>
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">CCCD/CMND</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem; font-family:'Courier New',monospace;">{cccd_display}</div>
                </div>
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">Mã hồ sơ</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem; font-family:'Courier New',monospace;">{pm['profile_id']}</div>
                </div>
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">Ngày nộp</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem;">{pm['submission_date']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Validation - cần cả tên và CCCD
    missing = []
    if not pm.get("full_name"):
        missing.append("họ và tên")
    if not pm.get("cccd_number"):
        missing.append("số CCCD/CMND")
    if missing:
        st.warning(f"⚠️ Vui lòng nhập {' và '.join(missing)} trước khi tiếp tục")

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, _, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button("← Quay lại", use_container_width=True, type="secondary"):
            prev_step()
            st.rerun()
    with col_r:
        # Disable next button nếu thiếu thông tin bắt buộc
        if pm.get("full_name") and pm.get("cccd_number"):
            if st.button("Tiếp theo →", type="primary", use_container_width=True):
                next_step()
                st.rerun()
        else:
            st.button("Tiếp theo →", type="primary", use_container_width=True, disabled=True)


# ============================================================
# STEP 1-4: FORMS (giữ từ v2, chỉ đổi step number)
# ============================================================

def render_step1_credit(scorecard):
    group_cfg = scorecard['scoring_groups']['credit_history']
    render_step_header(
        1, 6,
        "Lịch sử tín dụng",
        f"Trọng số {group_cfg['weight']*100:.0f}% · Tối đa {group_cfg['max_points']} điểm · "
        "Đây là nhóm quan trọng nhất trong mô hình FICO",
        "📊"
    )

    ch = st.session_state.applicant["credit_history"]

    render_section("Thông tin tín dụng", "🗂️")
    col1, col2 = st.columns(2)
    cic_options = ["no_history", "group1_all_ontime", "group2_once", "group2_multiple",
                   "group3", "group4", "group5"]
    with col1:
        ch["credit_history_cic"] = st.selectbox(
            "Lịch sử CIC 24 tháng gần nhất",
            options=cic_options,
            format_func=lambda x: {
                "no_history": "Không có lịch sử vay",
                "group1_all_ontime": "Nhóm 1 — Trả đúng hạn toàn bộ",
                "group2_once": "Nhóm 2 — Trễ 10-90 ngày (1 lần)",
                "group2_multiple": "Nhóm 2 — Trễ nhiều lần",
                "group3": "Nhóm 3 — Nợ dưới chuẩn ❌",
                "group4": "Nhóm 4 — Nợ nghi ngờ ❌",
                "group5": "Nhóm 5 — Nợ có khả năng mất vốn ❌",
            }[x],
            index=cic_options.index(ch.get("credit_history_cic", "group1_all_ontime")),
            help="Theo TT 11/2021/TT-NHNN: Nhóm 3 trở lên bị từ chối ngay (hard rule)",
        )
        ch["active_loans_count"] = st.number_input(
            "Số khoản vay đang hoạt động",
            min_value=0, max_value=20,
            value=ch.get("active_loans_count", 0),
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
        )

    render_section("Tài liệu chứng minh", "📎")
    st.caption("Báo cáo CIC cá nhân, hợp đồng tín dụng cũ. Nhớ che thông tin cá nhân.")
    uploaded = st.file_uploader(
        "Chọn file", accept_multiple_files=True, type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g1", label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.uploaded_files["group1"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


def render_step2_income(scorecard):
    group_cfg = scorecard['scoring_groups']['income']
    render_step_header(
        2, 6, "Thu nhập & việc làm",
        f"Trọng số {group_cfg['weight']*100:.0f}% · Tối đa {group_cfg['max_points']} điểm",
        "💼"
    )

    emp = st.session_state.applicant["employment"]
    render_section("Thông tin công việc", "🏢")
    col1, col2 = st.columns(2)
    contract_options = ["permanent", "fixed_gte_12m", "fixed_lt_12m", "self_employed_licensed", "freelance"]
    salary_options = ["bank_transfer", "cash_verified", "cash_unverified"]
    with col1:
        emp["employer"] = st.text_input("Tên công ty", value=emp.get("employer", ""),
                                         placeholder="Ví dụ: Công ty TNHH ABC")
        emp["job_title"] = st.text_input("Chức danh", value=emp.get("job_title", ""),
                                          placeholder="Ví dụ: Kỹ sư phần mềm")
        emp["employment_contract"] = st.selectbox(
            "Loại hợp đồng lao động",
            options=contract_options,
            format_func=lambda x: {
                "permanent": "Không thời hạn / biên chế",
                "fixed_gte_12m": "Xác định thời hạn ≥ 12 tháng",
                "fixed_lt_12m": "Xác định thời hạn < 12 tháng",
                "self_employed_licensed": "Tự doanh có giấy phép KD",
                "freelance": "Lao động tự do",
            }[x],
            index=contract_options.index(emp.get("employment_contract", "permanent")),
        )
    with col2:
        emp["employment_duration_months"] = st.number_input(
            "Thời gian làm việc hiện tại (tháng)",
            min_value=0, max_value=600, value=emp.get("employment_duration_months", 12),
        )
        emp["monthly_income_vnd"] = st.number_input(
            "Thu nhập hàng tháng (VNĐ)",
            min_value=0, max_value=500_000_000, step=1_000_000,
            value=emp.get("monthly_income_vnd", 10_000_000),
        )
        emp["salary_method"] = st.selectbox(
            "Hình thức nhận lương",
            options=salary_options,
            format_func=lambda x: {
                "bank_transfer": "Chuyển khoản ngân hàng (có sao kê)",
                "cash_verified": "Tiền mặt — có xác nhận của công ty",
                "cash_unverified": "Tiền mặt — không xác nhận",
            }[x],
            index=salary_options.index(emp.get("salary_method", "bank_transfer")),
        )

    render_section("Tài liệu chứng minh", "📎")
    st.caption("HĐLĐ, sao kê lương 3-6 tháng, xác nhận công tác, phiếu lương.")
    uploaded = st.file_uploader("Chọn file", accept_multiple_files=True,
                                type=["pdf", "jpg", "jpeg", "png"], key="upload_g2",
                                label_visibility="collapsed")
    if uploaded:
        st.session_state.uploaded_files["group2"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


def render_step3_personal(scorecard):
    group_cfg = scorecard['scoring_groups']['personal']
    render_step_header(
        3, 6, "Nhân thân",
        f"Trọng số {group_cfg['weight']*100:.0f}% · Tối đa {group_cfg['max_points']} điểm",
        "👤"
    )

    p = st.session_state.applicant["personal_info"]
    render_section("Thông tin cá nhân", "🪪")
    col1, col2 = st.columns(2)
    marital_options = ["single", "married", "divorced_widowed"]
    education_options = ["below_highschool", "highschool", "bachelor", "postgrad"]
    residency_options = ["owner", "family_home", "renting_gte_2y", "renting_lt_2y"]
    with col1:
        p["age"] = st.number_input("Tuổi", min_value=16, max_value=90, value=p.get("age", 30))
        p["gender"] = st.selectbox(
            "Giới tính", options=["male", "female", "other"],
            format_func=lambda x: {"male":"Nam", "female":"Nữ", "other":"Khác"}[x],
            index=["male","female","other"].index(p.get("gender", "male")),
        )
        p["marital_status"] = st.selectbox(
            "Tình trạng hôn nhân", options=marital_options,
            format_func=lambda x: {"single":"Độc thân", "married":"Đã kết hôn",
                                   "divorced_widowed":"Ly hôn / goá"}[x],
            index=marital_options.index(p.get("marital_status", "single")),
        )
    with col2:
        p["dependents"] = st.number_input("Số người phụ thuộc", min_value=0, max_value=10,
                                          value=p.get("dependents", 0))
        p["education"] = st.selectbox(
            "Trình độ học vấn", options=education_options,
            format_func=lambda x: {
                "below_highschool":"Dưới THPT", "highschool":"THPT / Trung cấp",
                "bachelor":"Đại học / Cao đẳng", "postgrad":"Sau đại học",
            }[x],
            index=education_options.index(p.get("education", "bachelor")),
        )
        p["residency_status"] = st.selectbox(
            "Tình trạng cư trú", options=residency_options,
            format_func=lambda x: {
                "owner":"Sở hữu nhà (có sổ đỏ)", "family_home":"Ở nhà gia đình (có hộ khẩu)",
                "renting_gte_2y":"Thuê nhà ≥ 2 năm", "renting_lt_2y":"Thuê nhà < 2 năm",
            }[x],
            index=residency_options.index(p.get("residency_status", "family_home")),
        )

    render_section("Tài liệu chứng minh", "📎")
    st.caption("CCCD/CMND, sổ hộ khẩu, giấy đăng ký kết hôn, giấy khai sinh con (nếu có).")
    uploaded = st.file_uploader("Chọn file", accept_multiple_files=True,
                                type=["pdf", "jpg", "jpeg", "png"], key="upload_g3",
                                label_visibility="collapsed")
    if uploaded:
        st.session_state.uploaded_files["group3"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


def render_step4_assets_loan(scorecard):
    render_step_header(4, 6, "Tài sản & khoản vay",
                       "Khai báo tài sản sở hữu và thông tin khoản vay mong muốn", "💰")

    a = st.session_state.applicant["assets"]
    loan = st.session_state.applicant["loan_request"]

    render_section("Tài sản sở hữu", "🏠")
    st.caption(f"Trọng số {scorecard['scoring_groups']['assets']['weight']*100:.0f}% · "
               f"Tối đa {scorecard['scoring_groups']['assets']['max_points']} điểm")

    col1, col2, col3 = st.columns(3)
    re_options = ["none", "family_shared", "owned_titled"]
    vehicle_options = ["none", "motorbike", "car"]
    with col1:
        a["real_estate"] = st.selectbox(
            "Bất động sản đứng tên", options=re_options,
            format_func=lambda x: {"none":"Không có BĐS", "family_shared":"Đồng sở hữu",
                                   "owned_titled":"Sở hữu — có sổ đỏ"}[x],
            index=re_options.index(a.get("real_estate", "none")),
        )
    with col2:
        a["vehicle"] = st.selectbox(
            "Phương tiện đi lại", options=vehicle_options,
            format_func=lambda x: {"none":"Không có", "motorbike":"Xe máy", "car":"Ô tô"}[x],
            index=vehicle_options.index(a.get("vehicle", "motorbike")),
        )
    with col3:
        a["savings_vnd"] = st.number_input("Tiền gửi tiết kiệm (VNĐ)", min_value=0,
                                            max_value=10_000_000_000, step=5_000_000,
                                            value=a.get("savings_vnd", 0))

    render_section("Thông tin khoản vay", "💳")
    col1, col2 = st.columns(2)
    term_options = [6, 9, 12, 18, 24, 36]
    with col1:
        loan["vehicle_name"] = st.text_input("Tên xe muốn mua",
                                              value=loan.get("vehicle_name", "Honda Vision 2025"))
        loan["vehicle_price_vnd"] = st.number_input(
            "Giá xe (VNĐ)", min_value=5_000_000, max_value=200_000_000, step=1_000_000,
            value=loan.get("vehicle_price_vnd", 34_000_000),
        )
        loan["down_payment_vnd"] = st.number_input(
            "Số tiền trả trước (VNĐ)", min_value=0,
            max_value=loan.get("vehicle_price_vnd", 34_000_000), step=500_000,
            value=loan.get("down_payment_vnd", 4_000_000),
            help="Tối thiểu 20% giá xe",
        )
    with col2:
        loan["loan_amount_vnd"] = loan["vehicle_price_vnd"] - loan["down_payment_vnd"]
        st.markdown(f"""
        <div style="background:white; border:1px solid var(--gold); border-radius:10px;
                    padding:1rem 1.25rem; margin-bottom:1rem;">
            <div style="font-size:0.78rem; color:var(--text-secondary); text-transform:uppercase;
                        font-weight:500; letter-spacing:0.05em;">Số tiền cần vay</div>
            <div style="font-size:1.6rem; font-weight:600; color:var(--navy); margin-top:0.2rem;">
                {loan['loan_amount_vnd']:,} VNĐ
            </div>
        </div>
        """, unsafe_allow_html=True)

        current_term = loan.get("term_months", 12)
        term_idx = term_options.index(current_term) if current_term in term_options else 2
        loan["term_months"] = st.selectbox("Kỳ hạn vay", options=term_options, index=term_idx,
                                            format_func=lambda x: f"{x} tháng")

        down_ratio = loan["down_payment_vnd"] / max(loan["vehicle_price_vnd"], 1)
        if down_ratio < 0.20:
            st.warning(f"⚠️ Trả trước {down_ratio*100:.1f}% — dưới ngưỡng 20%")
        else:
            st.success(f"✓ Trả trước {down_ratio*100:.1f}% — đạt yêu cầu")

    render_section("Tài liệu chứng minh", "📎")
    st.caption("Sổ đỏ, cà vẹt xe, sổ tiết kiệm, hợp đồng thuê nhà (nếu có).")
    uploaded = st.file_uploader("Chọn file", accept_multiple_files=True,
                                type=["pdf", "jpg", "jpeg", "png"], key="upload_g4",
                                label_visibility="collapsed")
    if uploaded:
        st.session_state.uploaded_files["group4"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons(next_label="🔍 Chạy xét duyệt")


# ============================================================
# STEP 5: RESULT - v3 dashboard gọn + slider lãi suất
# ============================================================

def render_step5_result(scorecard):
    render_step_header(5, 6, "Kết quả xét duyệt", "", "📋")

    pipeline = get_pipeline()
    persona_data = st.session_state.applicant.copy()
    persona_data["persona_id"] = (
        st.session_state.profile_meta.get("profile_id") or
        st.session_state.selected_persona or
        "custom_input"
    )
    decision = pipeline.evaluate(persona_data)

    # Dashboard tích hợp: thông tin hồ sơ + điểm gauge + thanh điểm theo nhóm + hard rules + lý do
    render_consolidated_dashboard(decision, scorecard)

    # Nếu fail hard rules: dừng tại đây (đã hiển thị đủ trong dashboard)
    if not decision.hard_rules_result.all_passed:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Sửa thông tin", use_container_width=True, type="secondary"):
                prev_step()
                st.rerun()
        with col2:
            if st.button("🔄 Xét duyệt hồ sơ khác", type="primary", use_container_width=True):
                reset_state()
                st.rerun()
        return

    # Nếu pass: tabs cho chi tiết bổ sung (không lặp với dashboard)
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([
        "💵  Phương án trả nợ",
        "💡  Cấu thành lãi suất",
        "📎  Chứng từ đã nộp",
    ])

    with tab1:
        render_repayment_with_slider(
            persona_data["loan_request"]["loan_amount_vnd"],
            decision.grade_result,
            persona_data["loan_request"]["term_months"],
            scorecard,
        )

    with tab2:
        render_rate_explanation(decision.grade_result, scorecard)

    with tab3:
        render_uploaded_docs_only()

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Sửa thông tin", use_container_width=True, type="secondary"):
            prev_step()
            st.rerun()
    with col2:
        if st.button("🔄 Xét duyệt hồ sơ khác", type="primary", use_container_width=True):
            reset_state()
            st.rerun()


# ============================================================
# v3: DASHBOARD HERO - tất cả thông tin chính 1 view
# ============================================================

def render_consolidated_dashboard(decision, scorecard):
    pm = st.session_state.profile_meta

    decision_map = {
        "approved_priority": {"label": "DUYỆT ƯU TIÊN", "cls": "approved",
                              "badge_cls": "status-approved", "icon": "✓"},
        "approved": {"label": "DUYỆT", "cls": "approved",
                     "badge_cls": "status-approved", "icon": "✓"},
        "approved_conditional": {"label": "DUYỆT CÓ ĐIỀU KIỆN", "cls": "review",
                                  "badge_cls": "status-review", "icon": "!"},
        "manual_review": {"label": "XEM XÉT THỦ CÔNG", "cls": "review",
                          "badge_cls": "status-review", "icon": "!"},
        "rejected": {"label": "TỪ CHỐI", "cls": "rejected",
                     "badge_cls": "status-rejected", "icon": "✗"},
    }
    m = decision_map.get(decision.final_decision, decision_map["rejected"])

    score_display = (str(decision.scoring_result.total_points)
                     if decision.scoring_result else "—")
    grade_display = (decision.grade_result.grade if decision.grade_result else "—")

    risk_vi_map = {
        "very_low": "Rất thấp", "low": "Thấp", "medium": "Trung bình",
        "medium_high": "Trung bình cao", "high": "Cao",
    }
    risk_display = (risk_vi_map.get(decision.grade_result.risk_level, "—")
                    if decision.grade_result else "—")

    rate_min = getattr(decision.grade_result, "interest_rate_min", None) if decision.grade_result else None
    rate_max = getattr(decision.grade_result, "interest_rate_max", None) if decision.grade_result else None
    if rate_min and rate_max:
        rate_range = f"{rate_min*100:.0f}% – {rate_max*100:.0f}%/năm"
    elif decision.grade_result and decision.grade_result.interest_rate_annual:
        rate_range = f"{decision.grade_result.interest_rate_annual*100:.0f}%/năm"
    else:
        rate_range = "—"

    loan_req = st.session_state.applicant.get("loan_request", {})

    border_color_map = {"approved": "#0F7A5C", "review": "#B87300", "rejected": "#B33A3A"}
    border_color = border_color_map.get(m["cls"], "#B33A3A")

    # Badge background map for hero badge
    badge_bg_map = {"approved": "#E3F4EC", "review": "#FFF4DB", "rejected": "#FCE4E4"}
    badge_text_map = {"approved": "#0F7A5C", "review": "#B87300", "rejected": "#B33A3A"}
    badge_bg = badge_bg_map.get(m["cls"], "#FCE4E4")
    badge_text = badge_text_map.get(m["cls"], "#B33A3A")

    # === HERO - 3 cột: gauge lớn | info + 4 metrics | separator ===
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, #FFFFFF 0%, #F8F9FB 100%);
                border:1.5px solid #E0E4EC; border-top:4px solid {border_color};
                border-radius:12px; padding:1.5rem 1.75rem; margin-bottom:1rem;
                box-shadow:0 2px 8px rgba(10,37,64,0.06);">
        <div style="display:grid; grid-template-columns:200px 1fr; gap:2rem; align-items:center;">

            <!-- Left: Score gauge lớn -->
            <div style="text-align:center; padding-right:1.75rem;
                        border-right:1.5px solid #E0E4EC;">
                <div style="font-size:0.72rem; color:#5A6B80; text-transform:uppercase;
                            letter-spacing:0.08em; font-weight:600; margin-bottom:0.3rem;">
                    Điểm tín dụng
                </div>
                <div style="font-size:3.5rem; font-weight:800; color:#0A2540;
                            line-height:1; letter-spacing:-0.03em;">
                    {score_display}
                </div>
                <div style="font-size:0.9rem; color:#5A6B80; margin-bottom:0.6rem;">/ 1000</div>
                <div style="display:inline-block; background:#0A2540; color:#C9A961;
                            padding:0.3rem 1rem; border-radius:6px; font-weight:800;
                            font-size:1rem; letter-spacing:0.08em; margin-bottom:0.35rem;">
                    HẠNG {grade_display}
                </div>
                <div style="font-size:0.78rem; color:#5A6B80; font-weight:500;">
                    Rủi ro: <b style="color:#0A2540;">{risk_display}</b>
                </div>
            </div>

            <!-- Right: Status + customer info + 4 metrics -->
            <div>
                <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem;">
                    <div style="background:{badge_bg}; color:{badge_text}; font-weight:700;
                                font-size:0.95rem; padding:0.35rem 1rem; border-radius:20px;
                                letter-spacing:0.02em;">
                        {m['icon']}  {m['label']}
                    </div>
                    <span style="font-size:0.88rem; color:#5A6B80;">
                        <b style="color:#0A2540;">{pm.get('full_name', '—')}</b>
                        &nbsp;·&nbsp; CCCD {pm.get('cccd_number', '—')}
                        &nbsp;·&nbsp; {pm.get('profile_id', '—')}
                        &nbsp;·&nbsp; {pm.get('submission_date', '—')}
                    </span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:0.6rem;">
                    <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                                padding:0.6rem 0.85rem;">
                        <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                                    letter-spacing:0.04em; font-weight:600; margin-bottom:0.2rem;">
                            Lãi suất đề xuất
                        </div>
                        <div style="font-size:1.05rem; font-weight:700; color:#C9A961;">{rate_range}</div>
                    </div>
                    <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                                padding:0.6rem 0.85rem;">
                        <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                                    letter-spacing:0.04em; font-weight:600; margin-bottom:0.2rem;">
                            Số tiền vay
                        </div>
                        <div style="font-size:1.05rem; font-weight:700; color:#0A2540;">
                            {loan_req.get('loan_amount_vnd', 0):,} VNĐ
                        </div>
                    </div>
                    <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                                padding:0.6rem 0.85rem;">
                        <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                                    letter-spacing:0.04em; font-weight:600; margin-bottom:0.2rem;">
                            Kỳ hạn
                        </div>
                        <div style="font-size:1.05rem; font-weight:700; color:#0A2540;">
                            {loan_req.get('term_months', 0)} tháng
                        </div>
                    </div>
                    <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                                padding:0.6rem 0.85rem;">
                        <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                                    letter-spacing:0.04em; font-weight:600; margin-bottom:0.2rem;">
                            Sản phẩm vay
                        </div>
                        <div style="font-size:0.95rem; font-weight:700; color:#0A2540;">
                            {loan_req.get('vehicle_name', '—')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === 2 CỘT CHÍNH ===
    col_left, col_right = st.columns([5, 4])

    with col_left:
        if decision.scoring_result:
            _render_score_bars(decision.scoring_result)
        else:
            st.markdown("""
            <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                        padding:1rem; text-align:center; color:#5A6B80; font-size:0.9rem;">
                Không chấm điểm do hồ sơ vi phạm điều kiện loại trực tiếp
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        _render_hard_rules_panel(decision)
        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
        _render_decision_reason_panel(decision)


def _render_score_bars(scoring_result):
    """Score bars dạng grid 2x2 — gọn, không chiếm nhiều chiều cao."""
    total_pct = scoring_result.ratio * 100

    # Header + tổng điểm
    st.markdown(f"""
    <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                padding:0.7rem 1rem; margin-bottom:0.5rem;
                display:flex; justify-content:space-between; align-items:center;">
        <div style="font-weight:700; color:#0A2540; font-size:0.95rem;">📊 Phân tích điểm</div>
        <div>
            <span style="color:#0A2540; font-weight:700; font-size:1.05rem;">{scoring_result.total_points}</span>
            <span style="color:#5A6B80; font-size:0.9rem;"> / {scoring_result.max_total_points}</span>
            <span style="color:#C9A961; font-weight:800; font-size:1.05rem; margin-left:0.5rem;">{total_pct:.1f}%</span>
        </div>
    </div>
    <div style="background:#F0F2F5; height:5px; border-radius:3px; overflow:hidden; margin-bottom:0.6rem;">
        <div style="background:linear-gradient(90deg, #C9A961, #E0C988);
                    height:100%; width:{total_pct}%; border-radius:3px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # 4 nhóm dạng grid 2×2
    groups = scoring_result.groups
    color_label_map = [
        ("#0F7A5C", "Xuất sắc") if g.ratio * 100 >= 80
        else ("#5B8C6E", "Tốt") if g.ratio * 100 >= 65
        else ("#B87300", "Trung bình") if g.ratio * 100 >= 50
        else ("#B33A3A", "Cần cải thiện")
        for g in groups
    ]

    # Row 1
    row1 = list(zip(groups[:2], color_label_map[:2]))
    row2 = list(zip(groups[2:], color_label_map[2:]))

    for row in [row1, row2]:
        cols = st.columns(2)
        for col, (g, (color, label)) in zip(cols, row):
            pct = g.ratio * 100
            with col:
                st.markdown(f"""
                <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                            padding:0.6rem 0.85rem; margin-bottom:0.4rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                        <div>
                            <span style="font-weight:700; color:#0A2540; font-size:0.88rem;">{g.group_name}</span>
                            <span style="color:#5A6B80; font-size:0.72rem; margin-left:0.3rem;">·  {g.weight*100:.0f}%</span>
                        </div>
                        <div style="display:flex; align-items:center; gap:0.4rem;">
                            <span style="background:{color}; color:white; font-size:0.65rem;
                                         padding:0.1rem 0.4rem; border-radius:3px; font-weight:600;">{label}</span>
                            <span style="font-weight:700; color:{color}; font-size:0.9rem;">{pct:.0f}%</span>
                        </div>
                    </div>
                    <div style="background:#F0F2F5; height:6px; border-radius:3px; overflow:hidden; margin-bottom:0.25rem;">
                        <div style="background:{color}; height:100%; width:{pct}%; border-radius:3px;"></div>
                    </div>
                    <div style="font-size:0.75rem; color:#5A6B80; text-align:right;">{g.points} / {g.max_points}</div>
                </div>
                """, unsafe_allow_html=True)

    # Expandable chi tiết
    with st.expander("🔍  Chi tiết điểm từng biến", expanded=False):
        for group in scoring_result.groups:
            st.markdown(f"""
            <div style="font-weight:700; color:#0A2540; font-size:0.88rem;
                        padding:0.35rem 0.6rem; background:#F5F7FA; border-radius:5px;
                        margin:0.4rem 0 0.3rem 0;">
                {group.group_name} · {group.points}/{group.max_points} · {group.ratio*100:.0f}%
            </div>
            """, unsafe_allow_html=True)

            for v in group.variables:
                var_pct = (v.points / v.max_points * 100) if v.max_points > 0 else 0
                var_color = "#0F7A5C" if var_pct >= 80 else ("#B87300" if var_pct >= 50 else "#B33A3A")
                actual_str = str(v.actual_value)[:28].replace("<", "&lt;").replace(">", "&gt;")

                st.markdown(f"""
                <div style="display:grid; grid-template-columns:1.6fr 1.4fr auto auto;
                            gap:0.5rem; align-items:center; padding:0.3rem 0.6rem;
                            font-size:0.82rem; border-bottom:1px solid #F0F2F5;">
                    <span style="color:#0A2540; font-weight:500;">{v.variable_name}</span>
                    <span style="color:#5A6B80;">{actual_str}</span>
                    <span style="color:#0A2540; font-weight:600; text-align:right;">{v.points}/{v.max_points}</span>
                    <span style="color:{var_color}; font-weight:700; text-align:right; min-width:38px;">{var_pct:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)


def _render_hard_rules_panel(decision):
    hard_passed = sum(1 for c in decision.hard_rules_result.checks if c.passed)
    hard_total = len(decision.hard_rules_result.checks)

    if decision.hard_rules_result.all_passed:
        header_color, header_text, header_bg = "#0F7A5C", f"Tất cả {hard_total} điều kiện đạt", "#F5FBF8"
    else:
        n_fail = hard_total - hard_passed
        header_color, header_text, header_bg = "#B33A3A", f"{n_fail} điều kiện không đạt", "#FEF5F5"

    st.markdown(f"""
    <div style="background:{header_bg}; border:1px solid {header_color}33;
                border-left:3px solid {header_color}; border-radius:8px;
                padding:0.6rem 1rem; margin-bottom:0.4rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:700; color:#0A2540; font-size:1rem;">🛡️ Điều kiện loại trực tiếp</div>
            <div style="color:{header_color}; font-weight:700; font-size:0.9rem;">{hard_passed}/{hard_total}</div>
        </div>
        <div style="color:{header_color}; font-size:0.8rem; margin-top:0.15rem;">{header_text}</div>
    </div>
    """, unsafe_allow_html=True)

    desc_vi_map = {
        "age_min": "Tuổi từ 20 trở lên",
        "age_max": "Tuổi không quá 60",
        "min_income": "Thu nhập tối thiểu 5 triệu/tháng",
        "min_employment": "Công tác tối thiểu 3 tháng",
        "cic_not_bad": "Không có nợ xấu CIC nhóm 3, 4, 5",
        "dti_max": "Tỷ lệ DTI sau vay không vượt 60%",
    }

    sorted_checks = sorted(decision.hard_rules_result.checks, key=lambda c: c.passed)

    for check in sorted_checks:
        short_desc = desc_vi_map.get(check.rule_id, check.description)
        short_desc = short_desc.replace("<", "≤").replace(">", "≥")

        if check.passed:
            row_html = f"""
            <div style="display:flex; align-items:center; gap:0.7rem; padding:0.35rem 0.85rem;
                        background:white; border:1px solid #E0E4EC; border-radius:6px;
                        margin-bottom:0.25rem; font-size:0.85rem;">
                <span style="color:#0F7A5C; font-weight:700; font-size:1rem;">✓</span>
                <span style="color:#0A2540; flex-grow:1;">{short_desc}</span>
            </div>
            """
        else:
            actual_human = _humanize_value(check.rule_id, check.actual_value)
            threshold_human = _humanize_threshold(check.rule_id, check.threshold)
            row_html = f"""
            <div style="background:#FEF5F5; border:1px solid #B33A3A33;
                        border-left:3px solid #B33A3A; border-radius:6px;
                        padding:0.4rem 0.85rem; margin-bottom:0.25rem;">
                <div style="display:flex; align-items:center; gap:0.7rem; font-size:0.85rem;">
                    <span style="color:#B33A3A; font-weight:700; font-size:1rem;">✗</span>
                    <span style="color:#B33A3A; font-weight:600; flex-grow:1;">{short_desc}</span>
                </div>
                <div style="font-size:0.75rem; color:#5A6B80; margin-top:0.2rem; padding-left:1.5rem;">
                    Hiện tại: <b style="color:#0A2540;">{actual_human}</b>
                    &nbsp;·&nbsp; Yêu cầu: <b style="color:#0A2540;">{threshold_human}</b>
                </div>
            </div>
            """
        st.markdown(row_html, unsafe_allow_html=True)


def _humanize_value(rule_id, value):
    """Format giá trị thực tế thành tiếng Việt tự nhiên, không dùng code/raw."""
    if value is None:
        return "Chưa có dữ liệu"
    if rule_id == "age_min" or rule_id == "age_max":
        return f"{value} tuổi"
    if rule_id == "min_income":
        return f"{int(value):,} VNĐ/tháng"
    if rule_id == "min_employment":
        return f"{value} tháng"
    if rule_id == "cic_not_bad":
        cic_vi = {
            "no_history": "Không có lịch sử",
            "group1_all_ontime": "Nhóm 1 — Trả đúng hạn",
            "group2_once": "Nhóm 2 — Trễ 1 lần",
            "group2_multiple": "Nhóm 2 — Trễ nhiều lần",
            "group3": "Nhóm 3 — Nợ dưới chuẩn",
            "group4": "Nhóm 4 — Nợ nghi ngờ",
            "group5": "Nhóm 5 — Có khả năng mất vốn",
        }
        return cic_vi.get(value, str(value))
    if rule_id == "dti_max":
        try:
            return f"{float(value)*100:.1f}%"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _humanize_threshold(rule_id, threshold):
    """Format ngưỡng thành tiếng Việt tự nhiên."""
    threshold_str = str(threshold)
    if rule_id == "age_min":
        return "Từ 20 tuổi trở lên"
    if rule_id == "age_max":
        return "Không quá 60 tuổi"
    if rule_id == "min_income":
        return "Tối thiểu 5,000,000 VNĐ/tháng"
    if rule_id == "min_employment":
        return "Tối thiểu 3 tháng"
    if rule_id == "cic_not_bad":
        return "Không thuộc nhóm 3, 4, 5"
    if rule_id == "dti_max":
        return "Không vượt quá 60%"
    return threshold_str.replace("<", "≤").replace(">", "≥")


def _render_decision_reason_panel(decision):
    decision_text_map = {
        "approved_priority": "Lịch sử tín dụng tốt, thu nhập ổn định. Đủ điều kiện duyệt ưu tiên với lãi suất thấp nhất.",
        "approved": "Đáp ứng đầy đủ tiêu chí xét duyệt với mức rủi ro thấp. Duyệt với lãi suất tiêu chuẩn.",
        "approved_conditional": "Đạt ngưỡng nhưng có yếu tố rủi ro trung bình. Duyệt kèm điều kiện bổ sung.",
        "manual_review": "Hồ sơ ở ngưỡng biên giới, cần chuyên viên thẩm định thêm trước khi quyết định.",
        "rejected": "Vi phạm điều kiện loại trực tiếp. Khách hàng cần khắc phục trước khi nộp lại.",
    }
    reason_text = decision_text_map.get(decision.final_decision, "Không xác định")

    if decision.final_decision == "approved_priority":
        next_step_text = "Mời ký hợp đồng và chọn phương án trả nợ."
    elif decision.final_decision == "approved":
        next_step_text = "Tiến hành ký hợp đồng theo lãi suất tiêu chuẩn."
    elif decision.final_decision in ("approved_conditional", "manual_review"):
        next_step_text = "Chuyển hồ sơ cho chuyên viên thẩm định."
    else:
        next_step_text = "Hướng dẫn khách hàng khắc phục điều kiện không đạt."

    st.markdown(f"""
    <div style="background:white; border:1px solid #E0E4EC; border-radius:8px;
                padding:0.7rem 1rem;">
        <div style="font-weight:700; color:#0A2540; font-size:1rem;
                    padding-bottom:0.4rem; margin-bottom:0.5rem;
                    border-bottom:1px solid #E0E4EC;">💡 Lý do quyết định</div>
        <div style="font-size:0.85rem; color:#5A6B80; line-height:1.6; margin-bottom:0.6rem;">
            {reason_text}
        </div>
        <div style="background:#FDFAF2; border-left:3px solid #C9A961;
                    border-radius:4px; padding:0.45rem 0.75rem;">
            <div style="font-size:0.68rem; color:#5A6B80; text-transform:uppercase;
                        letter-spacing:0.04em; font-weight:600;">Bước tiếp theo</div>
            <div style="font-size:0.82rem; color:#0A2540; line-height:1.4; margin-top:0.15rem; font-weight:500;">
                {next_step_text}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_uploaded_docs_only():
    """Tab chỉ hiển thị danh sách chứng từ đã nộp."""
    st.markdown("#### Chứng từ đã nộp theo từng nhóm")
    total = 0
    for group_key, label, icon in [
        ("group1", "Nhóm 1 — Lịch sử tín dụng", "📊"),
        ("group2", "Nhóm 2 — Thu nhập & việc làm", "💼"),
        ("group3", "Nhóm 3 — Nhân thân", "👤"),
        ("group4", "Nhóm 4 — Tài sản sở hữu", "🏠"),
    ]:
        files = st.session_state.uploaded_files.get(group_key, [])
        with st.expander(f"{icon}  {label}  ·  {len(files)} chứng từ"):
            if files:
                for f in files:
                    safe_name = f.replace("<", "&lt;").replace(">", "&gt;")
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:0.6rem;
                                padding:0.4rem 0.6rem; background:#F5F7FA;
                                border-radius:4px; margin-bottom:0.25rem;
                                font-size:0.85rem;">
                        <span>📄</span>
                        <span style="color:#0A2540;">{safe_name}</span>
                    </div>
                    """, unsafe_allow_html=True)
                total += len(files)
            else:
                st.caption("_Chưa có chứng từ nào được tải lên cho nhóm này_")

    st.markdown(f"""
    <div style="background:white; border:1px solid #E5E9F0; border-radius:8px;
                padding:0.85rem 1.25rem; margin-top:0.75rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:#5A6B80; font-size:0.85rem;">Tổng số chứng từ đã nộp</span>
            <span style="color:#C9A961; font-weight:700; font-size:1.2rem;">{total}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)



# ============================================================
# v3: REPAYMENT WITH SLIDER - dynamic
# ============================================================

def render_repayment_with_slider(loan_amount, grade_result, term_months, scorecard):
    if not grade_result or grade_result.interest_rate_annual is None:
        st.info("ℹ️ Hồ sơ bị từ chối, không tính phương án trả nợ.")
        return

    # Fallback nếu engine cũ
    rate_min = getattr(grade_result, "interest_rate_min", None)
    rate_max = getattr(grade_result, "interest_rate_max", None)
    if rate_min is None or rate_max is None:
        base_rate = grade_result.interest_rate_annual
        rate_min = max(0.0, base_rate - 0.02)
        rate_max = base_rate + 0.02

    # Init state
    if st.session_state.selected_rate is None:
        st.session_state.selected_rate = grade_result.interest_rate_annual
    if "calc_loan_amount" not in st.session_state:
        st.session_state.calc_loan_amount = loan_amount
    if "calc_term_months" not in st.session_state:
        st.session_state.calc_term_months = term_months

    # Đảm bảo selected_rate trong khoảng hợp lệ
    if (st.session_state.selected_rate < rate_min or
        st.session_state.selected_rate > rate_max):
        st.session_state.selected_rate = grade_result.interest_rate_annual

    # === HEADER ===
    st.markdown(f"""
    <div style="display:flex; align-items:flex-end; gap:0.6rem; margin-bottom:0.5rem;">
        <h3 style="margin:0; color:#0A2540; font-weight:600; font-size:1.15rem;">
            🧮 Công cụ ước tính khoản vay
        </h3>
        <span style="color:#5A6B80; font-size:0.82rem; padding-bottom:0.2rem;">
            Hạng <b style="color:#C9A961;">{grade_result.grade}</b> · Khoảng lãi suất {rate_min*100:.0f}% – {rate_max*100:.0f}%/năm
        </span>
    </div>
    <div style="height:3px; width:60px; background:linear-gradient(90deg, #C9A961, #E0C988);
                border-radius:2px; margin-bottom:1rem;"></div>
    """, unsafe_allow_html=True)

    # === LAYOUT: 3 sliders trái | Monthly payment + actions phải ===
    col_sliders, col_payment = st.columns([3, 2])

    with col_sliders:
        # === Slider 1: Lãi suất ===
        rate_label_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:baseline;
                    margin-bottom:0.25rem;">
            <span style="font-size:0.92rem; font-weight:600; color:#0A2540;">Lãi suất áp dụng</span>
            <span style="font-size:1.2rem; font-weight:700; color:#C9A961;">
                {st.session_state.selected_rate*100:.1f}<span style="font-size:0.85rem; font-weight:500;">%/năm</span>
            </span>
        </div>
        """
        st.markdown(rate_label_html, unsafe_allow_html=True)
        new_rate = st.slider(
            "Lãi suất",
            min_value=float(rate_min * 100),
            max_value=float(rate_max * 100),
            value=float(st.session_state.selected_rate * 100),
            step=0.1,
            format="%.1f%%",
            key="rate_slider",
            label_visibility="collapsed",
        )
        st.session_state.selected_rate = new_rate / 100

        # === Slider 2: Số tiền vay ===
        amount_label_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:baseline;
                    margin-top:0.5rem; margin-bottom:0.25rem;">
            <span style="font-size:0.88rem; font-weight:600; color:#0A2540;">Số tiền vay</span>
            <span style="font-size:1.1rem; font-weight:700; color:#C9A961;">
                {st.session_state.calc_loan_amount:,.0f}<span style="font-size:0.8rem; font-weight:500;"> VNĐ</span>
            </span>
        </div>
        """
        st.markdown(amount_label_html, unsafe_allow_html=True)
        # Max = giá xe (không vay quá giá xe), min = 5 triệu
        vehicle_price = loan_req.get("vehicle_price_vnd", 0) if "loan_req" in dir() else 0
        # Lấy vehicle_price từ session state
        vehicle_price = st.session_state.applicant.get("loan_request", {}).get("vehicle_price_vnd", 0)
        amount_min = 5_000_000
        # Max = giá xe hoặc 200tr, lấy cái nhỏ hơn
        amount_max = min(int(vehicle_price) if vehicle_price > 0 else 200_000_000, 200_000_000)
        # Đảm bảo loan_amount không vượt max
        if st.session_state.calc_loan_amount > amount_max:
            st.session_state.calc_loan_amount = min(loan_amount, amount_max)
        new_amount = st.slider(
            "Số tiền vay",
            min_value=amount_min,
            max_value=amount_max,
            value=min(int(st.session_state.calc_loan_amount), amount_max),
            step=1_000_000,
            format="%d",
            key="amount_slider",
            label_visibility="collapsed",
        )
        st.session_state.calc_loan_amount = new_amount
        if vehicle_price > 0:
            st.caption(f"Tối đa: {amount_max:,.0f} VNĐ (bằng giá xe {vehicle_price:,.0f} VNĐ)")

        # === Slider 3: Kỳ hạn ===
        term_label_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:baseline;
                    margin-top:0.5rem; margin-bottom:0.25rem;">
            <span style="font-size:0.88rem; font-weight:600; color:#0A2540;">Kỳ hạn vay</span>
            <span style="font-size:1.1rem; font-weight:700; color:#C9A961;">
                {st.session_state.calc_term_months}<span style="font-size:0.8rem; font-weight:500;"> tháng</span>
            </span>
        </div>
        """
        st.markdown(term_label_html, unsafe_allow_html=True)
        new_term = st.slider(
            "Kỳ hạn",
            min_value=6,
            max_value=36,
            value=int(st.session_state.calc_term_months),
            step=3,
            format="%d tháng",
            key="term_slider",
            label_visibility="collapsed",
        )
        st.session_state.calc_term_months = new_term

    # === Tính plans với giá trị hiện tại ===
    annual_rate = st.session_state.selected_rate
    current_loan = st.session_state.calc_loan_amount
    current_term = st.session_state.calc_term_months
    plans = cached_calculate_both_plans(current_loan, annual_rate, current_term)
    p1 = plans["plan_1_annuity"]
    p2 = plans["plan_2_equal_principal"]

    with col_payment:
        # Monthly payment box - PA1 (niên kim, đều mỗi tháng)
        monthly_pmt = p1.payments[0].total_payment

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #FDFAF2 0%, #FFFFFF 100%);
                    border:1.5px solid #C9A961; border-radius:10px;
                    padding:1.1rem 1.25rem; height:100%;
                    box-shadow:0 2px 8px rgba(201,169,97,0.12);">
            <div style="font-size:0.78rem; color:#5A6B80; text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:500;">Khoản trả góp hàng tháng</div>
            <div style="text-align:center; padding:0.75rem 0;">
                <span style="font-size:2rem; font-weight:700; color:#C9A961;
                             letter-spacing:-0.02em; line-height:1;">
                    {monthly_pmt:,.0f}
                </span>
                <span style="font-size:0.95rem; color:#5A6B80; margin-left:0.3rem;">VNĐ</span>
            </div>
            <div style="background:#F5F7FA; border-radius:6px; padding:0.5rem 0.75rem;
                        font-size:0.78rem; color:#5A6B80; line-height:1.5;">
                <div style="display:flex; justify-content:space-between; padding:0.15rem 0;">
                    <span>Tổng tiền lãi</span>
                    <span style="color:#0A2540; font-weight:600;">{p1.total_interest:,.0f} VNĐ</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:0.15rem 0;
                            border-top:1px dashed #E5E9F0; margin-top:0.25rem; padding-top:0.35rem;">
                    <span>Tổng phải trả</span>
                    <span style="color:#0A2540; font-weight:600;">{p1.total_paid:,.0f} VNĐ</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # === Ghi chú ===
    st.markdown(f"""
    <div style="margin-top:0.75rem; padding:0.6rem 0.85rem; background:#F5F7FA;
                border-left:3px solid #5A6B80; border-radius:4px;
                font-size:0.78rem; color:#5A6B80; font-style:italic; line-height:1.5;">
        <b style="color:#0A2540; font-style:normal;">*Ghi chú:</b>
        Khoản trả tháng hiển thị theo phương án niên kim (gốc + lãi đều).
        Kết quả tính toán mang tính chất tham khảo và có thể sai lệch nhỏ với kết quả thực tế tại các điểm giao dịch.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1.2rem;"></div>', unsafe_allow_html=True)

    # === SO SÁNH 2 PHƯƠNG ÁN - 3 cột metrics ===
    saving = p1.total_interest - p2.total_interest
    saving_pct = (saving / p1.total_interest * 100) if p1.total_interest > 0 else 0
    p2_first = p2.payments[0].total_payment
    p2_last = p2.payments[-1].total_payment

    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
        <div style="background:white; border:1px solid #E5E9F0; border-left:3px solid #0A2540;
                    border-radius:8px; padding:0.85rem 1rem;">
            <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:500;">📘 PA1 · Niên kim</div>
            <div style="font-size:0.78rem; color:#5A6B80; margin-top:0.2rem;">Trả đều mỗi kỳ</div>
            <div style="font-size:1.1rem; font-weight:700; color:#0A2540; margin-top:0.3rem;">
                {monthly_pmt:,.0f} VNĐ
            </div>
            <div style="font-size:0.72rem; color:#5A6B80; margin-top:0.15rem;">
                Tổng lãi: <b style="color:#0A2540;">{p1.total_interest:,.0f} VNĐ</b>
            </div>
        </div>
        <div style="background:white; border:1px solid #E5E9F0; border-left:3px solid #C9A961;
                    border-radius:8px; padding:0.85rem 1rem;">
            <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:500;">📙 PA2 · Gốc đều</div>
            <div style="font-size:0.78rem; color:#5A6B80; margin-top:0.2rem;">Trả giảm dần</div>
            <div style="font-size:1.1rem; font-weight:700; color:#0A2540; margin-top:0.3rem;">
                {p2_first:,.0f} → {p2_last:,.0f}
            </div>
            <div style="font-size:0.72rem; color:#5A6B80; margin-top:0.15rem;">
                Tổng lãi: <b style="color:#0F7A5C;">{p2.total_interest:,.0f} VNĐ</b>
            </div>
        </div>
        <div style="background:linear-gradient(135deg, #F5FBF8 0%, #FFFFFF 100%);
                    border:1px solid #0F7A5C33; border-left:3px solid #0F7A5C;
                    border-radius:8px; padding:0.85rem 1rem;">
            <div style="font-size:0.7rem; color:#5A6B80; text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:500;">💰 PA2 tiết kiệm so với PA1</div>
            <div style="font-size:0.78rem; color:#5A6B80; margin-top:0.2rem;">Số lãi giảm được</div>
            <div style="font-size:1.1rem; font-weight:700; color:#0F7A5C; margin-top:0.3rem;">
                {saving:,.0f} VNĐ
            </div>
            <div style="font-size:0.72rem; color:#5A6B80; margin-top:0.15rem;">
                Tương đương <b style="color:#0F7A5C;">{saving_pct:.1f}%</b> tổng lãi
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # === Tabs: Chart | Bảng PA1 | Bảng PA2 | Tải file ===
    tab_chart, tab_p1, tab_p2, tab_download = st.tabs([
        "📈  Biểu đồ so sánh",
        "📘  Lịch trả PA1",
        "📙  Lịch trả PA2",
        "⬇️  Tải file",
    ])

    with tab_chart:
        # 2 charts: dòng tiền mỗi kỳ + dư nợ giảm dần
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                '<div style="font-weight:600; color:#0A2540; font-size:0.9rem; margin-bottom:0.4rem;">'
                'Dòng tiền trả mỗi kỳ</div>',
                unsafe_allow_html=True,
            )
            cashflow_df = pd.DataFrame({
                "Kỳ": [p.period for p in p1.payments],
                "PA1 — Niên kim": [p.total_payment for p in p1.payments],
                "PA2 — Gốc đều": [p.total_payment for p in p2.payments],
            }).set_index("Kỳ")
            st.line_chart(cashflow_df, height=240, color=["#0A2540", "#C9A961"])
        with col_b:
            st.markdown(
                '<div style="font-weight:600; color:#0A2540; font-size:0.9rem; margin-bottom:0.4rem;">'
                'Dư nợ còn lại theo thời gian</div>',
                unsafe_allow_html=True,
            )
            balance_df = pd.DataFrame({
                "Kỳ": [p.period for p in p1.payments],
                "PA1 — Niên kim": [p.closing_balance for p in p1.payments],
                "PA2 — Gốc đều": [p.closing_balance for p in p2.payments],
            }).set_index("Kỳ")
            st.area_chart(balance_df, height=240, color=["#0A2540", "#C9A961"])

    with tab_p1:
        df1 = schedule_to_df(p1)
        st.dataframe(df1, use_container_width=True, hide_index=True, height=380)

    with tab_p2:
        df2 = schedule_to_df(p2)
        st.dataframe(df2, use_container_width=True, hide_index=True, height=380)

    with tab_download:
        st.markdown(
            '<p style="color:#5A6B80; font-size:0.85rem; margin-bottom:0.75rem;">'
            'Tải lịch trả nợ về máy để chia sẻ hoặc lưu trữ.</p>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            df1 = schedule_to_df(p1)
            excel_bytes = export_to_excel(p1, p2, current_loan, annual_rate, current_term)
            st.download_button(
                "📊  Tải Excel (cả 2 phương án)",
                data=excel_bytes,
                file_name=f"lich_tra_no_{current_loan//1_000_000}trieu_{current_term}thang_{annual_rate*100:.0f}%.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            csv1 = df1.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📄  Tải CSV (chỉ PA1)",
                data=csv1,
                file_name=f"pa1_nien_kim_{current_loan//1_000_000}trieu.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ============================================================
# v3: RATE EXPLANATION - khoa học, có công thức
# ============================================================

def render_rate_explanation(grade_result, scorecard):
    if not grade_result or grade_result.interest_rate_annual is None:
        st.info("ℹ️ Hồ sơ bị từ chối, không có lãi suất đề xuất.")
        return

    # Fallback: nếu engine cũ chưa có interest_rate_components hoặc risk_premium
    components = scorecard["scoring_system"].get("interest_rate_components")
    if not components:
        st.warning(
            "⚠️ File `scorecard.json` trên server chưa được cập nhật phiên bản v3 "
            "(thiếu `interest_rate_components`). Vui lòng push file mới lên repo và đợi redeploy."
        )
        return

    risk_premium = getattr(grade_result, "risk_premium", None)
    if risk_premium is None:
        st.warning(
            "⚠️ File `engine/scoring_engine.py` trên server chưa được cập nhật phiên bản v3 "
            "(thiếu `risk_premium`). Vui lòng push file mới lên repo và đợi redeploy."
        )
        return

    selected_rate = st.session_state.selected_rate or grade_result.interest_rate_annual

    st.markdown("#### Cấu thành lãi suất theo phương pháp khoa học")
    st.markdown("""
    <p style="color:var(--text-secondary); font-size:0.9rem;">
    Lãi suất cho vay được tính dựa trên 4 thành phần chính, theo thông lệ quốc tế và quy định
    của NHNN Việt Nam.
    </p>
    """, unsafe_allow_html=True)

    # Card công thức
    st.markdown(f"""
    <div class="rate-explain-card">
        <div style="font-weight:600; color:var(--navy); font-size:1rem; margin-bottom:0.5rem;">
            🧮 Công thức tính lãi suất
        </div>
        <div class="rate-formula">
            r = LS_điều_hành + Chi_phí_vốn + Biên_rủi_ro<sub>(theo hạng)</sub> + Phí_dịch_vụ
        </div>
        <div style="margin-top:1rem;">
            <div class="rate-component">
                <span class="label">{components['policy_rate_label']}</span>
                <span class="value">+ {components['policy_rate']*100:.2f}%</span>
            </div>
            <div class="rate-component">
                <span class="label">{components['cost_of_fund_label']}</span>
                <span class="value">+ {components['cost_of_fund']*100:.2f}%</span>
            </div>
            <div class="rate-component">
                <span class="label">Biên rủi ro hạng <b>{grade_result.grade}</b> ({grade_result.risk_level.replace('_', ' ')})</span>
                <span class="value">+ {risk_premium*100:.2f}%</span>
            </div>
            <div class="rate-component">
                <span class="label">{components['service_fee_label']}</span>
                <span class="value">+ {components['service_fee']*100:.2f}%</span>
            </div>
            <div class="rate-component">
                <span class="label">Tổng lãi suất đề xuất (mức trung bình)</span>
                <span class="value">{(components['policy_rate'] + components['cost_of_fund'] + risk_premium + components['service_fee'])*100:.2f}%/năm</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Explanation
    st.markdown(f"""
    <div style="background:white; border:1px solid #E5E9F0; border-radius:10px;
                padding:1.25rem 1.5rem; margin-top:1rem;">
        <div style="font-weight:600; color:var(--navy); margin-bottom:0.6rem;">
            📚 Giải thích từng thành phần
        </div>
        <div style="font-size:0.88rem; color:var(--text-secondary); line-height:1.7;">
            <p><b style="color:var(--navy);">1. Lãi suất điều hành NHNN ({components['policy_rate']*100:.1f}%):</b>
            Lãi suất tái cấp vốn do Ngân hàng Nhà nước Việt Nam công bố,
            là chuẩn cho toàn hệ thống. Nguồn: {components['policy_rate_source']}.</p>
            <p><b style="color:var(--navy);">2. Chi phí huy động vốn ({components['cost_of_fund']*100:.1f}%):</b>
            Chi phí thực tế ngân hàng phải trả cho người gửi tiết kiệm để có vốn cho vay lại.
            Phụ thuộc vào kỳ hạn huy động và cạnh tranh thị trường.</p>
            <p><b style="color:var(--navy);">3. Biên rủi ro ({risk_premium*100:.1f}% cho hạng {grade_result.grade}):</b>
            Phần bù rủi ro tương ứng với khả năng vỡ nợ của khách hàng.
            Hạng càng cao biên càng thấp. Đây là cấu phần <i>quan trọng nhất</i> của scorecard —
            nó biến điểm tín dụng thành con số thực tế khách hàng phải trả.</p>
            <p><b style="color:var(--navy);">4. Phí dịch vụ và lợi nhuận ({components['service_fee']*100:.1f}%):</b>
            Bao gồm chi phí vận hành, công nghệ, nhân sự, và lợi nhuận kỳ vọng của ngân hàng.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Bảng tham chiếu
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Bảng tham chiếu lãi suất theo hạng tín dụng")

    ref_data = []
    for t in scorecard["scoring_system"]["grade_thresholds"]:
        if t["interest_rate_annual"] is None:
            continue
        is_current = t["grade"] == grade_result.grade
        rmin = t.get("interest_rate_min", t["interest_rate_annual"] - 0.02)
        rmax = t.get("interest_rate_max", t["interest_rate_annual"] + 0.02)
        rprem = t.get("risk_premium", 0)
        ref_data.append({
            "Hạng": ("👉 " if is_current else "") + t["grade"],
            "Điểm tối thiểu": t["min_score"],
            "Mức rủi ro": t["risk_level"].replace("_", " ").title(),
            "Biên rủi ro": f"{rprem*100:.1f}%",
            "Khoảng lãi suất": f"{rmin*100:.1f}% - {rmax*100:.1f}%",
            "Trung bình": f"{t['interest_rate_annual']*100:.1f}%",
        })
    df_ref = pd.DataFrame(ref_data)
    st.dataframe(df_ref, use_container_width=True, hide_index=True)

    st.caption(f"💡 Hồ sơ này hạng **{grade_result.grade}**, đang chọn lãi suất **{selected_rate*100:.1f}%/năm** — kéo slider ở tab 'Phương án trả nợ' để điều chỉnh.")



# ============================================================
# UTILS
# ============================================================

def schedule_to_df(schedule):
    return pd.DataFrame([
        {"Kỳ": p.period, "Dư nợ đầu kỳ": f"{p.opening_balance:,.0f}",
         "Gốc": f"{p.principal:,.0f}", "Lãi": f"{p.interest:,.0f}",
         "Tổng trả": f"{p.total_payment:,.0f}", "Dư nợ cuối": f"{p.closing_balance:,.0f}"}
        for p in schedule.payments
    ])


def export_to_excel(p1, p2, loan_amount, annual_rate, term_months):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
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
        df1 = pd.DataFrame([
            {"Kỳ": p.period, "Dư nợ đầu kỳ": p.opening_balance, "Gốc": p.principal,
             "Lãi": p.interest, "Tổng trả": p.total_payment, "Dư nợ cuối": p.closing_balance}
            for p in p1.payments])
        df1.to_excel(writer, sheet_name="PA1 - Niên kim", index=False)
        df2 = pd.DataFrame([
            {"Kỳ": p.period, "Dư nợ đầu kỳ": p.opening_balance, "Gốc": p.principal,
             "Lãi": p.interest, "Tổng trả": p.total_payment, "Dư nợ cuối": p.closing_balance}
            for p in p2.payments])
        df2.to_excel(writer, sheet_name="PA2 - Gốc đều", index=False)
    output.seek(0)
    return output.getvalue()


# ============================================================
# MAIN ROUTER - v3 thêm step 0.5
# ============================================================

def main():
    init_state()
    scorecard = load_scorecard()
    personas = load_personas()

    render_sidebar(scorecard)

    step = st.session_state.step
    if step == 0:
        render_step0_choose(personas, scorecard)
    elif step == 1:
        render_step_init_profile()  # v3 NEW
    elif step == 2:
        render_step1_credit(scorecard)
    elif step == 3:
        render_step2_income(scorecard)
    elif step == 4:
        render_step3_personal(scorecard)
    elif step == 5:
        render_step4_assets_loan(scorecard)
    elif step == 6:
        render_step5_result(scorecard)


if __name__ == "__main__":
    main()
