"""
Streamlit App v2 - Hệ thống xét duyệt hồ sơ vay tiêu dùng cá nhân
UI redesign: Navy + Gold, phong cách ngân hàng trang trọng.

Chạy: streamlit run app.py

Thay đổi so với v1:
  - Typography Inter, palette navy #0A2540 + gold #C9A961
  - Hero header, persona cards redesign, tab bar gold underline
  - Result card dashboard-style với metric row
  - Sidebar stepper với connector lines
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
    page_title="Hệ thống xét duyệt tín dụng",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# v2: CUSTOM CSS - Navy + Gold theme
# ============================================================

st.markdown("""
<style>
    /* v2: Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* v2: Global typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* v2: Palette variables */
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

    /* v2: Page background */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* v2: Headings in navy */
    h1, h2, h3, h4 {
        color: var(--navy) !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }
    h1 { font-size: 1.75rem !important; }
    h2 { font-size: 1.4rem !important; }
    h3 { font-size: 1.15rem !important; }

    /* v2: Hero header card */
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

    /* v2: Step label */
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

    /* v2: Persona cards */
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

    /* v2: Section header inside forms */
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

    /* v2: Button styles */
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

    /* v2: Input focus state */
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(201, 169, 97, 0.2) !important;
    }

    /* v2: Result hero card */
    .result-hero {
        background: linear-gradient(135deg, #FFFFFF 0%, #F5F7FA 100%);
        border: 1px solid #E5E9F0;
        border-top: 4px solid;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0 1.5rem 0;
        box-shadow: 0 2px 8px rgba(10, 37, 64, 0.04);
    }
    .result-hero.approved { border-top-color: var(--success); }
    .result-hero.review   { border-top-color: var(--warning); }
    .result-hero.rejected { border-top-color: var(--danger); }

    .result-status-badge {
        display: inline-block;
        padding: 0.35rem 0.9rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-bottom: 0.75rem;
    }
    .status-approved { background: #E3F4EC; color: var(--success); }
    .status-review   { background: #FFF4DB; color: var(--warning); }
    .status-rejected { background: #FCE4E4; color: var(--danger); }

    .big-number {
        font-family: 'Inter', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        line-height: 1;
        color: var(--navy);
        letter-spacing: -0.02em;
    }
    .big-number-suffix {
        font-size: 1.5rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    /* v2: Metric card row */
    .metric-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        border: 1px solid #E5E9F0;
        border-radius: 10px;
        padding: 1rem 1.25rem;
    }
    .metric-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-bottom: 0.3rem;
        font-weight: 500;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--navy);
    }

    /* v2: Tab styling */
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

    /* v2: Alert/info boxes */
    div[data-testid="stAlert"] {
        border-radius: 8px !important;
        border-left-width: 3px !important;
    }

    /* v2: Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--navy) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #D4DCE8 !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: white !important;
    }

    /* v2: Sidebar stepper */
    .sidebar-stepper {
        position: relative;
        padding-left: 1rem;
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

    /* v2: Remove default Streamlit styling artifacts */
    [data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    /* v2: Table improvements */
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
            "group1": [], "group2": [], "group3": [], "group4": [],
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


def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1


# ============================================================
# v2: HERO HEADER
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
# v2: SIDEBAR với stepper đẹp
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

        # v2: Stepper
        steps = [
            ("Chọn hồ sơ", "Bước 0"),
            ("Lịch sử tín dụng", "Bước 1"),
            ("Thu nhập & việc làm", "Bước 2"),
            ("Nhân thân", "Bước 3"),
            ("Tài sản & khoản vay", "Bước 4"),
            ("Kết quả xét duyệt", "Bước 5"),
        ]

        st.markdown("### Tiến trình")
        stepper_html = '<div class="sidebar-stepper">'
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

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Làm lại từ đầu", use_container_width=True, type="secondary"):
            reset_state()
            st.rerun()

        # Info
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
# STEP 0: CHOOSE PERSONA - v2 card design
# ============================================================

def render_step0_choose(personas, scorecard):
    render_hero(scorecard)
    st.markdown('<div class="step-indicator"><span class="step-dot"></span>Bước 0 / 5 · Khởi tạo</div>', unsafe_allow_html=True)
    st.markdown("## Chọn hồ sơ vay")
    st.markdown(
        "<p style='color:#5A6B80; margin-bottom:1.5rem;'>"
        "Chọn một trong 3 hồ sơ demo có sẵn để xét duyệt nhanh, hoặc nhập thủ công hồ sơ mới. "
        "Các hồ sơ demo được thiết kế để minh họa 3 kịch bản: duyệt ưu tiên, duyệt có điều kiện, và từ chối."
        "</p>",
        unsafe_allow_html=True,
    )

    # v2: 4 cards in grid
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
            if st.button(f"Chọn hồ sơ {persona['persona_id'][0]}", key=f"pick_{i}", use_container_width=True, type="primary"):
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
                Nhập thủ công từng trường thông tin cho một khách hàng mới để hệ thống xét duyệt.
                Phù hợp để test logic với hồ sơ tùy chỉnh.
            </div>
            <div class="persona-card-badge badge-custom">Tùy chỉnh</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Nhập mới", key="pick_custom", use_container_width=True, type="primary"):
            st.session_state.selected_persona = None
            next_step()
            st.rerun()


# ============================================================
# v2: Helper - section title & step header
# ============================================================

def render_step_header(step_num, total, title, subtitle, icon=""):
    st.markdown(f'<div class="step-indicator"><span class="step-dot"></span>Bước {step_num} / {total}</div>', unsafe_allow_html=True)
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
# STEP 1: CREDIT HISTORY
# ============================================================

def render_step1_credit(scorecard):
    group_cfg = scorecard['scoring_groups']['credit_history']
    render_step_header(
        1, 5,
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
            help="Tỷ lệ tổng nợ phải trả hàng tháng / thu nhập",
        )

    render_section("Tài liệu chứng minh", "📎")
    st.caption("Báo cáo CIC cá nhân, hợp đồng tín dụng cũ (nếu có). Nhớ che thông tin cá nhân trước khi upload.")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g1",
        label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.uploaded_files["group1"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file: {', '.join(f.name for f in uploaded)}")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


# ============================================================
# STEP 2: INCOME
# ============================================================

def render_step2_income(scorecard):
    group_cfg = scorecard['scoring_groups']['income']
    render_step_header(
        2, 5,
        "Thu nhập & việc làm",
        f"Trọng số {group_cfg['weight']*100:.0f}% · Tối đa {group_cfg['max_points']} điểm · "
        "Chứng minh khả năng trả nợ của khách hàng",
        "💼"
    )

    emp = st.session_state.applicant["employment"]

    render_section("Thông tin công việc", "🏢")
    col1, col2 = st.columns(2)
    contract_options = ["permanent", "fixed_gte_12m", "fixed_lt_12m", "self_employed_licensed", "freelance"]
    salary_options = ["bank_transfer", "cash_verified", "cash_unverified"]
    with col1:
        emp["employer"] = st.text_input(
            "Tên công ty / nơi làm việc",
            value=emp.get("employer", ""),
            placeholder="Ví dụ: Công ty TNHH ABC",
        )
        emp["job_title"] = st.text_input(
            "Chức danh / nghề nghiệp",
            value=emp.get("job_title", ""),
            placeholder="Ví dụ: Kỹ sư phần mềm",
        )
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
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g2",
        label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.uploaded_files["group2"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


# ============================================================
# STEP 3: PERSONAL
# ============================================================

def render_step3_personal(scorecard):
    group_cfg = scorecard['scoring_groups']['personal']
    render_step_header(
        3, 5,
        "Nhân thân",
        f"Trọng số {group_cfg['weight']*100:.0f}% · Tối đa {group_cfg['max_points']} điểm · "
        "Đánh giá ổn định cá nhân và gia đình",
        "👤"
    )

    p = st.session_state.applicant["personal_info"]

    render_section("Thông tin cá nhân", "🪪")
    col1, col2 = st.columns(2)
    marital_options = ["single", "married", "divorced_widowed"]
    education_options = ["below_highschool", "highschool", "bachelor", "postgrad"]
    residency_options = ["owner", "family_home", "renting_gte_2y", "renting_lt_2y"]
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
            options=marital_options,
            format_func=lambda x: {
                "single":"Độc thân",
                "married":"Đã kết hôn",
                "divorced_widowed":"Ly hôn / goá",
            }[x],
            index=marital_options.index(p.get("marital_status", "single")),
        )
    with col2:
        p["dependents"] = st.number_input(
            "Số người phụ thuộc",
            min_value=0, max_value=10,
            value=p.get("dependents", 0),
        )
        p["education"] = st.selectbox(
            "Trình độ học vấn",
            options=education_options,
            format_func=lambda x: {
                "below_highschool":"Dưới THPT",
                "highschool":"THPT / Trung cấp",
                "bachelor":"Đại học / Cao đẳng",
                "postgrad":"Sau đại học",
            }[x],
            index=education_options.index(p.get("education", "bachelor")),
        )
        p["residency_status"] = st.selectbox(
            "Tình trạng cư trú",
            options=residency_options,
            format_func=lambda x: {
                "owner":"Sở hữu nhà (có sổ đỏ)",
                "family_home":"Ở nhà gia đình (có hộ khẩu)",
                "renting_gte_2y":"Thuê nhà ≥ 2 năm",
                "renting_lt_2y":"Thuê nhà < 2 năm",
            }[x],
            index=residency_options.index(p.get("residency_status", "family_home")),
        )

    render_section("Tài liệu chứng minh", "📎")
    st.caption("CCCD/CMND, sổ hộ khẩu, giấy đăng ký kết hôn, giấy khai sinh con (nếu có).")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g3",
        label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.uploaded_files["group3"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


# ============================================================
# STEP 4: ASSETS + LOAN
# ============================================================

def render_step4_assets_loan(scorecard):
    render_step_header(
        4, 5,
        "Tài sản & khoản vay",
        "Khai báo tài sản sở hữu và thông tin khoản vay mong muốn",
        "💰"
    )

    a = st.session_state.applicant["assets"]
    loan = st.session_state.applicant["loan_request"]

    render_section("Tài sản sở hữu", "🏠")
    st.caption(
        f"Trọng số {scorecard['scoring_groups']['assets']['weight']*100:.0f}% · "
        f"Tối đa {scorecard['scoring_groups']['assets']['max_points']} điểm"
    )

    col1, col2, col3 = st.columns(3)
    re_options = ["none", "family_shared", "owned_titled"]
    vehicle_options = ["none", "motorbike", "car"]
    with col1:
        a["real_estate"] = st.selectbox(
            "Bất động sản đứng tên",
            options=re_options,
            format_func=lambda x: {
                "none":"Không có BĐS",
                "family_shared":"Đồng sở hữu với gia đình",
                "owned_titled":"Sở hữu — có sổ đỏ",
            }[x],
            index=re_options.index(a.get("real_estate", "none")),
        )
    with col2:
        a["vehicle"] = st.selectbox(
            "Phương tiện đi lại",
            options=vehicle_options,
            format_func=lambda x: {"none":"Không có", "motorbike":"Xe máy", "car":"Ô tô"}[x],
            index=vehicle_options.index(a.get("vehicle", "motorbike")),
        )
    with col3:
        a["savings_vnd"] = st.number_input(
            "Tiền gửi tiết kiệm (VNĐ)",
            min_value=0, max_value=10_000_000_000, step=5_000_000,
            value=a.get("savings_vnd", 0),
        )

    render_section("Thông tin khoản vay", "💳")
    col1, col2 = st.columns(2)
    term_options = [6, 9, 12, 18, 24, 36]
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

        # v2: Custom metric card
        st.markdown(f"""
        <div class="metric-card" style="border-color:var(--gold); margin-bottom:1rem;">
            <div class="metric-label">Số tiền cần vay</div>
            <div class="metric-value" style="color:var(--navy); font-size:1.6rem;">{loan['loan_amount_vnd']:,} VNĐ</div>
        </div>
        """, unsafe_allow_html=True)

        current_term = loan.get("term_months", 12)
        term_idx = term_options.index(current_term) if current_term in term_options else 2
        loan["term_months"] = st.selectbox(
            "Kỳ hạn vay",
            options=term_options,
            index=term_idx,
            format_func=lambda x: f"{x} tháng",
        )

        down_ratio = loan["down_payment_vnd"] / max(loan["vehicle_price_vnd"], 1)
        if down_ratio < 0.20:
            st.warning(f"⚠️ Trả trước {down_ratio*100:.1f}% — dưới ngưỡng tối thiểu 20%")
        else:
            st.success(f"✓ Trả trước {down_ratio*100:.1f}% — đạt yêu cầu")

    render_section("Tài liệu chứng minh", "📎")
    st.caption("Sổ đỏ, cà vẹt xe, sổ tiết kiệm, hợp đồng thuê nhà (nếu có).")
    uploaded = st.file_uploader(
        "Chọn file",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g4",
        label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.uploaded_files["group4"] = [f.name for f in uploaded]
        st.success(f"✓ Đã tải lên {len(uploaded)} file")

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons(next_label="🔍 Chạy xét duyệt")


# ============================================================
# STEP 5: RESULT - v2 dashboard style
# ============================================================

def render_step5_result(scorecard):
    render_step_header(5, 5, "Kết quả xét duyệt", "", "📋")

    pipeline = get_pipeline()
    persona_data = st.session_state.applicant.copy()
    persona_data["persona_id"] = st.session_state.selected_persona or "custom_input"

    decision = pipeline.evaluate(persona_data)

    # v2: Result hero card with dashboard layout
    render_result_hero(decision, scorecard)

    # v2: Detail tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🛡️  Hard Rules",
        "📊  Điểm chi tiết",
        "💵  Phương án trả nợ",
        "📎  Chứng từ",
    ])

    with tab1:
        render_hard_rules_tab(decision)

    with tab2:
        if decision.scoring_result is None:
            st.info("ℹ️ Hồ sơ bị từ chối ở bước hard rules, không chấm điểm.")
        else:
            render_scoring_detail(decision.scoring_result)

    with tab3:
        if decision.grade_result is None or decision.grade_result.interest_rate_annual is None:
            st.info("ℹ️ Hồ sơ bị từ chối, không tính phương án trả nợ.")
        else:
            render_repayment_plans(
                persona_data["loan_request"]["loan_amount_vnd"],
                decision.grade_result.interest_rate_annual,
                persona_data["loan_request"]["term_months"],
            )

    with tab4:
        render_uploaded_docs_tab()

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


def render_result_hero(decision, scorecard):
    decision_map = {
        "approved_priority": {"label": "DUYỆT ƯU TIÊN", "cls": "approved", "badge_cls": "status-approved", "icon": "✓"},
        "approved": {"label": "DUYỆT", "cls": "approved", "badge_cls": "status-approved", "icon": "✓"},
        "approved_conditional": {"label": "DUYỆT CÓ ĐIỀU KIỆN", "cls": "review", "badge_cls": "status-review", "icon": "!"},
        "manual_review": {"label": "XEM XÉT THỦ CÔNG", "cls": "review", "badge_cls": "status-review", "icon": "!"},
        "rejected": {"label": "TỪ CHỐI", "cls": "rejected", "badge_cls": "status-rejected", "icon": "✗"},
    }
    m = decision_map.get(decision.final_decision, decision_map["rejected"])

    score_display = (
        str(decision.scoring_result.total_points)
        if decision.scoring_result else "—"
    )
    grade_display = (
        decision.grade_result.grade
        if decision.grade_result else "N/A"
    )
    risk_display = (
        decision.grade_result.risk_level.replace("_", " ").title()
        if decision.grade_result else "—"
    )
    rate_display = (
        f"{decision.grade_result.interest_rate_annual*100:.1f}%/năm"
        if decision.grade_result and decision.grade_result.interest_rate_annual
        else "—"
    )

    st.markdown(f"""
    <div class="result-hero {m['cls']}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
            <div>
                <div class="result-status-badge {m['badge_cls']}">{m['icon']}  {m['label']}</div>
                <div style="color:var(--text-secondary); font-size:0.9rem;">
                    Mã hồ sơ: <b style="color:var(--navy);">{decision.persona_id}</b>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.2rem;">Điểm tín dụng</div>
                <div class="big-number">{score_display}<span class="big-number-suffix"> / {scorecard['scoring_system']['max_score']}</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # v2: Metric row
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-label">Hạng tín dụng</div>
            <div class="metric-value">{grade_display}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Mức rủi ro</div>
            <div class="metric-value">{risk_display}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Lãi suất đề xuất</div>
            <div class="metric-value" style="color:var(--gold);">{rate_display}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Trạng thái</div>
            <div class="metric-value" style="color:var(--navy);">{m['label']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_hard_rules_tab(decision):
    st.markdown("#### Kết quả kiểm tra 6 điều kiện loại trực tiếp")
    st.caption("Các điều kiện này được kiểm tra trước khi chấm điểm. Nếu vi phạm bất kỳ điều kiện nào, hồ sơ bị từ chối ngay.")
    st.markdown("<br>", unsafe_allow_html=True)

    for check in decision.hard_rules_result.checks:
        if check.passed:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; padding:0.75rem; background:#F5FBF8; border-left:3px solid var(--success); border-radius:4px; margin-bottom:0.5rem;">
                <div style="color:var(--success); font-size:1.3rem; font-weight:700;">✓</div>
                <div style="flex-grow:1;">
                    <div style="font-weight:500; color:var(--navy);">{check.description}</div>
                    <div style="font-size:0.85rem; color:var(--text-secondary);">
                        Giá trị thực tế: <code>{check.actual_value}</code> · Ngưỡng: <code>{check.threshold}</code>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; padding:0.75rem; background:#FEF5F5; border-left:3px solid var(--danger); border-radius:4px; margin-bottom:0.5rem;">
                <div style="color:var(--danger); font-size:1.3rem; font-weight:700;">✗</div>
                <div style="flex-grow:1;">
                    <div style="font-weight:500; color:var(--danger);">{check.description}</div>
                    <div style="font-size:0.85rem; color:var(--text-secondary);">
                        Giá trị thực tế: <code>{check.actual_value}</code> · Ngưỡng: <code>{check.threshold}</code>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    if not decision.hard_rules_result.all_passed:
        st.markdown("<br>", unsafe_allow_html=True)
        st.error("**Hồ sơ không đủ điều kiện xét duyệt**")
        st.markdown("**Lý do từ chối:**")
        for reason in decision.rejection_reasons:
            st.markdown(f"- {reason}")


def render_scoring_detail(scoring_result):
    # v2: Metric summary
    st.markdown("#### Tổng quan điểm")

    total_display = f"{scoring_result.total_points} / {scoring_result.max_total_points}"
    ratio_display = f"{scoring_result.ratio*100:.1f}%"

    cols = st.columns(len(scoring_result.groups) + 1)
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card" style="border-color:var(--gold); background:#FDFAF2;">
            <div class="metric-label">Tổng điểm</div>
            <div class="metric-value" style="color:var(--gold);">{total_display}</div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:0.2rem;">{ratio_display}</div>
        </div>
        """, unsafe_allow_html=True)
    for i, g in enumerate(scoring_result.groups, 1):
        with cols[i]:
            pct = g.ratio * 100
            color = "#0F7A5C" if pct >= 75 else ("#B87300" if pct >= 50 else "#B33A3A")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label" style="font-size:0.75rem;">{g.group_name}</div>
                <div class="metric-value" style="color:{color};">{g.points}/{g.max_points}</div>
                <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:0.2rem;">{pct:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Chart
    st.markdown("#### Phân tích điểm theo nhóm")
    group_data = pd.DataFrame([
        {
            "Nhóm": g.group_name,
            "Điểm đạt": g.points,
            "Điểm tối đa": g.max_points,
        }
        for g in scoring_result.groups
    ])
    st.bar_chart(
        group_data.set_index("Nhóm")[["Điểm đạt", "Điểm tối đa"]],
        height=280,
        color=["#0A2540", "#C9A961"],
    )

    # Detail
    st.markdown("#### Chi tiết từng biến")
    for group in scoring_result.groups:
        with st.expander(f"{group.group_name} · {group.points}/{group.max_points} điểm ({group.ratio*100:.0f}%)"):
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

    # v2: Metric row with navy + gold
    st.markdown("#### Thông số khoản vay")
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-label">Số tiền vay</div>
            <div class="metric-value">{loan_amount:,.0f}</div>
            <div style="font-size:0.8rem; color:var(--text-secondary);">VNĐ</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Lãi suất</div>
            <div class="metric-value" style="color:var(--gold);">{annual_rate*100:.1f}%</div>
            <div style="font-size:0.8rem; color:var(--text-secondary);">mỗi năm</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Kỳ hạn</div>
            <div class="metric-value">{term_months}</div>
            <div style="font-size:0.8rem; color:var(--text-secondary);">tháng</div>
        </div>
        <div class="metric-card" style="border-color:var(--gold);">
            <div class="metric-label">PA2 tiết kiệm</div>
            <div class="metric-value" style="color:var(--success);">{(p1.total_interest - p2.total_interest):,.0f}</div>
            <div style="font-size:0.8rem; color:var(--text-secondary);">VNĐ so với PA1</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two plans side by side
    st.markdown("#### Lịch trả nợ chi tiết")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:#F5F7FA; padding:1rem; border-radius:8px; border-left:3px solid var(--navy); margin-bottom:0.5rem;">
            <div style="font-weight:600; color:var(--navy); font-size:1rem;">📘 Phương án 1: Niên kim</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">Gốc + lãi đều — dòng tiền ổn định</div>
        </div>
        """, unsafe_allow_html=True)
        df1 = schedule_to_df(p1)
        st.dataframe(df1, use_container_width=True, hide_index=True, height=320)
        st.markdown(f"""
        <div style="background:#FDFAF2; padding:0.75rem; border-radius:6px; border:1px solid var(--gold-light);">
            <div style="font-size:0.85rem; color:var(--text-secondary);">Tổng lãi</div>
            <div style="font-weight:600; color:var(--navy); font-size:1.1rem;">{p1.total_interest:,.0f} VNĐ</div>
            <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.5rem;">Tổng phải trả</div>
            <div style="font-weight:600; color:var(--navy); font-size:1.1rem;">{p1.total_paid:,.0f} VNĐ</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#F5F7FA; padding:1rem; border-radius:8px; border-left:3px solid var(--gold); margin-bottom:0.5rem;">
            <div style="font-weight:600; color:var(--navy); font-size:1rem;">📙 Phương án 2: Gốc đều</div>
            <div style="font-size:0.85rem; color:var(--text-secondary);">Gốc cố định, lãi giảm dần — tiết kiệm lãi</div>
        </div>
        """, unsafe_allow_html=True)
        df2 = schedule_to_df(p2)
        st.dataframe(df2, use_container_width=True, hide_index=True, height=320)
        st.markdown(f"""
        <div style="background:#FDFAF2; padding:0.75rem; border-radius:6px; border:1px solid var(--gold-light);">
            <div style="font-size:0.85rem; color:var(--text-secondary);">Tổng lãi</div>
            <div style="font-weight:600; color:var(--success); font-size:1.1rem;">{p2.total_interest:,.0f} VNĐ</div>
            <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.5rem;">Tổng phải trả</div>
            <div style="font-weight:600; color:var(--navy); font-size:1.1rem;">{p2.total_paid:,.0f} VNĐ</div>
        </div>
        """, unsafe_allow_html=True)

    # Comparison chart
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### So sánh dòng tiền mỗi kỳ")
    compare_df = pd.DataFrame({
        "Kỳ": [p.period for p in p1.payments],
        "PA1 — Niên kim": [p.total_payment for p in p1.payments],
        "PA2 — Gốc đều": [p.total_payment for p in p2.payments],
    }).set_index("Kỳ")
    st.line_chart(compare_df, height=280, color=["#0A2540", "#C9A961"])

    # Download
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Tải xuống")
    col1, col2 = st.columns(2)
    with col1:
        excel_bytes = export_to_excel(p1, p2, loan_amount, annual_rate, term_months)
        st.download_button(
            "📊  Tải file Excel (cả 2 phương án)",
            data=excel_bytes,
            file_name=f"lich_tra_no_{loan_amount//1_000_000}trieu_{term_months}thang.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col2:
        csv1 = df1.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📄  Tải CSV (chỉ PA1)",
            data=csv1,
            file_name="pa1_nien_kim.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render_uploaded_docs_tab():
    st.markdown("#### Chứng từ đã upload")
    total = 0
    for group_key, label, icon in [
        ("group1", "Nhóm 1 — Lịch sử tín dụng", "📊"),
        ("group2", "Nhóm 2 — Thu nhập", "💼"),
        ("group3", "Nhóm 3 — Nhân thân", "👤"),
        ("group4", "Nhóm 4 — Tài sản", "🏠"),
    ]:
        files = st.session_state.uploaded_files.get(group_key, [])
        with st.expander(f"{icon}  {label} · {len(files)} file"):
            if files:
                for f in files:
                    st.markdown(f"- 📄 `{f}`")
                total += len(files)
            else:
                st.caption("_Chưa upload file nào_")

    st.markdown(f"""
    <div class="metric-card" style="border-color:var(--gold); margin-top:1rem;">
        <div class="metric-label">Tổng số file đã tải lên</div>
        <div class="metric-value" style="color:var(--gold);">{total}</div>
    </div>
    """, unsafe_allow_html=True)


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
            for p in p1.payments
        ])
        df1.to_excel(writer, sheet_name="PA1 - Niên kim", index=False)
        df2 = pd.DataFrame([
            {"Kỳ": p.period, "Dư nợ đầu kỳ": p.opening_balance, "Gốc": p.principal,
             "Lãi": p.interest, "Tổng trả": p.total_payment, "Dư nợ cuối": p.closing_balance}
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

    step = st.session_state.step
    if step == 0:
        render_step0_choose(personas, scorecard)
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
