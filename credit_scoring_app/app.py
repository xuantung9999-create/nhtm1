"""
Streamlit App v4 - Credit Scoring System (Vietnamese consumer loan)
UI: Navy + Gold, banking dashboard style.

v4 changes:
  1. Bilingual EN/VI toggle (default: Vietnamese)
  2. Improved dashboard balance: bigger score hero, compact analysis bars
  3. Loan amount slider capped at vehicle price (giá xe)
  4. Refined typography, spacing and polish for professional/elegant look

Wizard 7 steps (0..6):
  0   - Choose profile (preset or custom)
  0.5 - Initialize profile (name, profile id)
  1-4 - Form steps
  5   - Result dashboard

Run: streamlit run app.py
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
ASSETS_DIR = BASE_DIR / "assets"
LOGO_FULL_PATH = ASSETS_DIR / "logo_cropped.png"
LOGO_ICON_PATH = ASSETS_DIR / "logo_icon.png"


@st.cache_data
def _encode_image_b64(path: Path) -> str:
    """Encode an image file as base64 for embedding in HTML/markdown."""
    import base64
    if not path.exists():
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


LOGO_FULL_B64 = _encode_image_b64(LOGO_FULL_PATH)
LOGO_ICON_B64 = _encode_image_b64(LOGO_ICON_PATH)

st.set_page_config(
    page_title="Khá Bank · Credit Scoring",
    page_icon=str(LOGO_ICON_PATH) if LOGO_ICON_PATH.exists() else "🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# I18N - TRANSLATION DICTIONARY
# ============================================================

TRANSLATIONS = {
    # Generic / shared
    "lang_label":             {"vi": "Ngôn ngữ",                                  "en": "Language"},
    "app_title":              {"vi": "Hệ thống xét duyệt tín dụng",               "en": "Credit Scoring System"},
    "app_subtitle":           {"vi": "Tự động hóa quy trình chấm điểm theo chuẩn quốc tế",
                               "en": "Automated credit assessment to international standards"},
    "app_badge":              {"vi": "Hệ thống chấm điểm tín dụng · Việt Nam",
                               "en": "Credit Scoring System · Vietnam"},
    "sidebar_title":          {"vi": "Chấm điểm tín dụng",                        "en": "Credit Scoring"},
    "sidebar_sub":            {"vi": "Vay tiêu dùng — Việt Nam",                  "en": "Vietnam Consumer Loan"},
    "sidebar_progress":       {"vi": "Tiến trình",                                "en": "Progress"},
    "sidebar_evaluating":     {"vi": "Đang xét duyệt",                            "en": "Currently reviewing"},
    "sidebar_scorecard":      {"vi": "Scorecard",                                 "en": "Scorecard"},
    "sidebar_max_score":      {"vi": "Thang điểm",                                "en": "Max score"},
    "btn_reset":              {"vi": "🔄 Làm lại từ đầu",                         "en": "🔄 Restart"},
    "btn_back":               {"vi": "← Quay lại",                                "en": "← Back"},
    "btn_next":               {"vi": "Tiếp theo →",                               "en": "Next →"},
    "btn_run":                {"vi": "🔍 Chạy xét duyệt",                          "en": "🔍 Run assessment"},
    "btn_edit":               {"vi": "← Sửa thông tin",                           "en": "← Edit information"},
    "btn_review_other":       {"vi": "🔄 Xét duyệt hồ sơ khác",                    "en": "🔄 Review another profile"},

    # Step labels (sidebar / steppers)
    "step_choose":            {"vi": "Chọn hồ sơ",                                "en": "Select profile"},
    "step_init":              {"vi": "Khởi tạo hồ sơ",                            "en": "Initialize profile"},
    "step_credit":            {"vi": "Lịch sử tín dụng",                          "en": "Credit history"},
    "step_income":            {"vi": "Thu nhập & việc làm",                       "en": "Income & employment"},
    "step_personal":          {"vi": "Nhân thân",                                  "en": "Personal info"},
    "step_assets":            {"vi": "Tài sản & khoản vay",                       "en": "Assets & loan"},
    "step_result":            {"vi": "Kết quả xét duyệt",                         "en": "Assessment result"},
    "step_word":              {"vi": "Bước",                                       "en": "Step"},

    # Step 0
    "s0_indicator":           {"vi": "Bước 0 / 6 · Khởi tạo",                     "en": "Step 0 / 6 · Setup"},
    "s0_title":               {"vi": "Chọn hồ sơ vay",                            "en": "Select a loan profile"},
    "s0_intro":               {"vi": "Chọn một trong 3 hồ sơ demo có sẵn để xét duyệt nhanh, hoặc nhập thủ công hồ sơ mới. "
                                     "Các hồ sơ demo được thiết kế để minh họa 3 kịch bản: duyệt ưu tiên, duyệt có điều kiện, và từ chối.",
                               "en": "Choose one of the three demo profiles for a quick assessment, or enter a new profile manually. "
                                     "The demo profiles illustrate three scenarios: priority approval, conditional review, and rejection."},
    "s0_priority":            {"vi": "Duyệt ưu tiên",                             "en": "Priority approval"},
    "s0_manual":              {"vi": "Xem xét thủ công",                          "en": "Manual review"},
    "s0_rejected":            {"vi": "Từ chối",                                    "en": "Rejected"},
    "s0_persona":             {"vi": "Hồ sơ",                                      "en": "Profile"},
    "s0_pick":                {"vi": "Chọn hồ sơ",                                 "en": "Select profile"},
    "s0_custom_title":        {"vi": "Nhập tự do",                                 "en": "Custom input"},
    "s0_custom_short":        {"vi": "Hồ sơ mới",                                  "en": "New profile"},
    "s0_custom_desc":         {"vi": "Nhập thủ công từng trường thông tin cho khách hàng mới. "
                                     "Bước tiếp theo bạn sẽ nhập tên và mã hồ sơ.",
                               "en": "Manually enter each field for a new customer. "
                                     "In the next step you will enter the customer name and profile ID."},
    "s0_custom_badge":        {"vi": "Tùy chỉnh",                                  "en": "Custom"},
    "s0_pick_custom":         {"vi": "Nhập mới",                                   "en": "Start new"},

    # Step 0.5 - init
    "s05_title":              {"vi": "Khởi tạo hồ sơ",                             "en": "Initialize profile"},
    "s05_subtitle":           {"vi": "Nhập thông tin định danh cho hồ sơ trước khi tiến hành kê khai chi tiết",
                               "en": "Enter identifying information before completing the detailed application"},
    "s05_section":            {"vi": "Thông tin định danh hồ sơ",                  "en": "Profile identification"},
    "s05_full_name":          {"vi": "Họ và tên khách hàng *",                     "en": "Customer full name *"},
    "s05_full_name_ph":       {"vi": "Ví dụ: Nguyễn Văn An",                       "en": "Example: Nguyen Van An"},
    "s05_full_name_help":     {"vi": "Họ tên đầy đủ theo CMND/CCCD. Trên báo cáo sẽ hiển thị che mã hoá.",
                               "en": "Full legal name as on the ID card. The report will display a masked version."},
    "s05_id_num":             {"vi": "Số CCCD / CMND *",                            "en": "ID card number *"},
    "s05_id_num_ph":          {"vi": "Ví dụ: 001094XXXXXX",                         "en": "Example: 001094XXXXXX"},
    "s05_id_num_help":        {"vi": "Số CCCD 12 chữ số hoặc CMND 9 chữ số. Nên che 6 số cuối bằng X để bảo mật.",
                               "en": "12-digit citizen ID or 9-digit national ID. Mask the last 6 digits with X for privacy."},
    "s05_profile_id":         {"vi": "Mã hồ sơ vay",                                "en": "Loan profile ID"},
    "s05_profile_id_help":    {"vi": "Mã định danh nội bộ cho hồ sơ vay này",       "en": "Internal identifier for this loan profile"},
    "s05_submission_date":    {"vi": "Ngày nộp hồ sơ",                              "en": "Submission date"},
    "s05_status_label":       {"vi": "Trạng thái",                                  "en": "Status"},
    "s05_status_value":       {"vi": "📋 Đang khởi tạo",                            "en": "📋 Initializing"},
    "s05_status_desc":        {"vi": "Sau khi hoàn tất, hồ sơ sẽ tự động chuyển sang giai đoạn xét duyệt",
                               "en": "Once complete, the profile automatically advances to the assessment phase"},
    "s05_security":           {"vi": "<b>🔒 Bảo mật:</b> Số CCCD/CMND chỉ dùng để định danh hồ sơ. "
                                     "Khuyến nghị che 6 ký tự cuối (ví dụ: 001094XXXXXX).",
                               "en": "<b>🔒 Privacy:</b> The ID number is used only to identify the profile. "
                                     "We recommend masking the last 6 characters (e.g. 001094XXXXXX)."},
    "s05_summary_title":      {"vi": "Tóm tắt thông tin hồ sơ",                     "en": "Profile summary"},
    "s05_customer":           {"vi": "Khách hàng",                                  "en": "Customer"},
    "s05_id_short":           {"vi": "CCCD/CMND",                                   "en": "ID number"},
    "s05_profile_id_short":   {"vi": "Mã hồ sơ",                                    "en": "Profile ID"},
    "s05_submission_short":   {"vi": "Ngày nộp",                                    "en": "Submitted"},
    "s05_warn_missing":       {"vi": "⚠️ Vui lòng nhập {} trước khi tiếp tục",      "en": "⚠️ Please enter {} before continuing"},
    "s05_field_name":         {"vi": "họ và tên",                                   "en": "the full name"},
    "s05_field_id":           {"vi": "số CCCD/CMND",                                "en": "the ID number"},
    "s05_field_and":          {"vi": " và ",                                        "en": " and "},

    # Step 1 - credit
    "s1_title":               {"vi": "Lịch sử tín dụng",                            "en": "Credit history"},
    "s1_subtitle":            {"vi": "Trọng số {weight}% · Tối đa {max} điểm · Đây là nhóm quan trọng nhất trong mô hình FICO",
                               "en": "Weight {weight}% · Max {max} points · This is the most important group in the FICO model"},
    "s1_section":             {"vi": "Thông tin tín dụng",                          "en": "Credit information"},
    "s1_cic":                 {"vi": "Lịch sử CIC 24 tháng gần nhất",               "en": "CIC history (last 24 months)"},
    "s1_cic_help":            {"vi": "Theo TT 11/2021/TT-NHNN: Nhóm 3 trở lên bị từ chối ngay (hard rule)",
                               "en": "Per Circular 11/2021/TT-NHNN: Group 3 and above are auto-rejected (hard rule)"},
    "s1_active_loans":        {"vi": "Số khoản vay đang hoạt động",                 "en": "Number of active loans"},
    "s1_history_years":       {"vi": "Thời gian có lịch sử tín dụng (năm)",         "en": "Length of credit history (years)"},
    "s1_dti_current":         {"vi": "DTI hiện tại (trước khi vay mới)",            "en": "Current DTI (before new loan)"},
    "s1_doc_section":         {"vi": "Tài liệu chứng minh",                         "en": "Supporting documents"},
    "s1_doc_caption":         {"vi": "Báo cáo CIC cá nhân, hợp đồng tín dụng cũ. Nhớ che thông tin cá nhân.",
                               "en": "Personal CIC report, prior credit contracts. Remember to redact personal information."},
    "s1_doc_chooser":         {"vi": "Chọn file",                                   "en": "Select files"},
    "s1_doc_uploaded":        {"vi": "✓ Đã tải lên {} file",                        "en": "✓ Uploaded {} file(s)"},

    # CIC options
    "cic_no_history":         {"vi": "Không có lịch sử vay",                        "en": "No credit history"},
    "cic_group1_all_ontime":  {"vi": "Nhóm 1 — Trả đúng hạn toàn bộ",                "en": "Group 1 — Always on time"},
    "cic_group2_once":        {"vi": "Nhóm 2 — Trễ 10-90 ngày (1 lần)",             "en": "Group 2 — Late 10-90 days (once)"},
    "cic_group2_multiple":    {"vi": "Nhóm 2 — Trễ nhiều lần",                      "en": "Group 2 — Late multiple times"},
    "cic_group3":             {"vi": "Nhóm 3 — Nợ dưới chuẩn ❌",                    "en": "Group 3 — Substandard debt ❌"},
    "cic_group4":             {"vi": "Nhóm 4 — Nợ nghi ngờ ❌",                       "en": "Group 4 — Doubtful debt ❌"},
    "cic_group5":             {"vi": "Nhóm 5 — Nợ có khả năng mất vốn ❌",            "en": "Group 5 — Loss-likely debt ❌"},

    # Step 2 - income
    "s2_title":               {"vi": "Thu nhập & việc làm",                          "en": "Income & employment"},
    "s2_subtitle":            {"vi": "Trọng số {weight}% · Tối đa {max} điểm",        "en": "Weight {weight}% · Max {max} points"},
    "s2_section":             {"vi": "Thông tin công việc",                          "en": "Employment details"},
    "s2_employer":            {"vi": "Tên công ty",                                   "en": "Company name"},
    "s2_employer_ph":         {"vi": "Ví dụ: Công ty TNHH ABC",                      "en": "Example: ABC Co., Ltd."},
    "s2_job_title":           {"vi": "Chức danh",                                     "en": "Job title"},
    "s2_job_title_ph":        {"vi": "Ví dụ: Kỹ sư phần mềm",                         "en": "Example: Software engineer"},
    "s2_contract":            {"vi": "Loại hợp đồng lao động",                        "en": "Employment contract type"},
    "s2_duration":            {"vi": "Thời gian làm việc hiện tại (tháng)",           "en": "Current employment duration (months)"},
    "s2_income":              {"vi": "Thu nhập hàng tháng (VNĐ)",                     "en": "Monthly income (VND)"},
    "s2_salary_method":       {"vi": "Hình thức nhận lương",                          "en": "Salary payment method"},
    "s2_doc_caption":         {"vi": "HĐLĐ, sao kê lương 3-6 tháng, xác nhận công tác, phiếu lương.",
                               "en": "Employment contract, 3–6 month salary statements, employment confirmation, payslips."},
    "ct_permanent":           {"vi": "Không thời hạn / biên chế",                    "en": "Permanent / civil-service"},
    "ct_fixed_gte_12m":       {"vi": "Xác định thời hạn ≥ 12 tháng",                 "en": "Fixed term ≥ 12 months"},
    "ct_fixed_lt_12m":        {"vi": "Xác định thời hạn < 12 tháng",                 "en": "Fixed term < 12 months"},
    "ct_self_employed":       {"vi": "Tự doanh có giấy phép KD",                     "en": "Self-employed (licensed)"},
    "ct_freelance":           {"vi": "Lao động tự do",                                "en": "Freelance"},
    "sm_bank":                {"vi": "Chuyển khoản ngân hàng (có sao kê)",            "en": "Bank transfer (with statement)"},
    "sm_cash_verified":       {"vi": "Tiền mặt — có xác nhận của công ty",            "en": "Cash — with company confirmation"},
    "sm_cash_unverified":     {"vi": "Tiền mặt — không xác nhận",                     "en": "Cash — unverified"},

    # Step 3 - personal
    "s3_title":               {"vi": "Nhân thân",                                     "en": "Personal information"},
    "s3_section":             {"vi": "Thông tin cá nhân",                             "en": "Personal details"},
    "s3_age":                 {"vi": "Tuổi",                                          "en": "Age"},
    "s3_gender":              {"vi": "Giới tính",                                     "en": "Gender"},
    "g_male":                 {"vi": "Nam",                                           "en": "Male"},
    "g_female":               {"vi": "Nữ",                                            "en": "Female"},
    "g_other":                {"vi": "Khác",                                          "en": "Other"},
    "s3_marital":             {"vi": "Tình trạng hôn nhân",                           "en": "Marital status"},
    "ms_single":              {"vi": "Độc thân",                                      "en": "Single"},
    "ms_married":             {"vi": "Đã kết hôn",                                    "en": "Married"},
    "ms_divorced":            {"vi": "Ly hôn / goá",                                  "en": "Divorced / widowed"},
    "s3_dependents":          {"vi": "Số người phụ thuộc",                            "en": "Number of dependents"},
    "s3_education":           {"vi": "Trình độ học vấn",                              "en": "Education level"},
    "ed_below":               {"vi": "Dưới THPT",                                     "en": "Below high school"},
    "ed_highschool":          {"vi": "THPT / Trung cấp",                              "en": "High school / vocational"},
    "ed_bachelor":            {"vi": "Đại học / Cao đẳng",                            "en": "Bachelor / college"},
    "ed_postgrad":            {"vi": "Sau đại học",                                   "en": "Post-graduate"},
    "s3_residency":           {"vi": "Tình trạng cư trú",                             "en": "Residency status"},
    "rs_owner":               {"vi": "Sở hữu nhà (có sổ đỏ)",                          "en": "Owner (with land title)"},
    "rs_family":              {"vi": "Ở nhà gia đình (có hộ khẩu)",                   "en": "Family home (registered)"},
    "rs_renting_gte_2y":      {"vi": "Thuê nhà ≥ 2 năm",                              "en": "Renting ≥ 2 years"},
    "rs_renting_lt_2y":       {"vi": "Thuê nhà < 2 năm",                              "en": "Renting < 2 years"},
    "s3_doc_caption":         {"vi": "CCCD/CMND, sổ hộ khẩu, giấy đăng ký kết hôn, giấy khai sinh con (nếu có).",
                               "en": "ID card, household registration, marriage certificate, child birth certificate (if any)."},

    # Step 4 - assets & loan
    "s4_title":               {"vi": "Tài sản & khoản vay",                            "en": "Assets & loan request"},
    "s4_subtitle":            {"vi": "Khai báo tài sản sở hữu và thông tin khoản vay mong muốn",
                               "en": "Declare owned assets and the desired loan terms"},
    "s4_assets_section":      {"vi": "Tài sản sở hữu",                                "en": "Owned assets"},
    "s4_assets_caption":      {"vi": "Trọng số {weight}% · Tối đa {max} điểm",         "en": "Weight {weight}% · Max {max} points"},
    "s4_real_estate":         {"vi": "Bất động sản đứng tên",                          "en": "Real estate (titled)"},
    "re_none":                {"vi": "Không có BĐS",                                   "en": "No real estate"},
    "re_family":              {"vi": "Đồng sở hữu",                                    "en": "Co-owned"},
    "re_owned":               {"vi": "Sở hữu — có sổ đỏ",                              "en": "Sole owner — titled"},
    "s4_vehicle":             {"vi": "Phương tiện đi lại",                             "en": "Vehicle"},
    "v_none":                 {"vi": "Không có",                                       "en": "None"},
    "v_motorbike":            {"vi": "Xe máy",                                         "en": "Motorbike"},
    "v_car":                  {"vi": "Ô tô",                                           "en": "Car"},
    "s4_savings":             {"vi": "Tiền gửi tiết kiệm (VNĐ)",                       "en": "Savings deposits (VND)"},
    "s4_loan_section":        {"vi": "Thông tin khoản vay",                            "en": "Loan information"},
    "s4_vehicle_name":        {"vi": "Tên xe muốn mua",                                "en": "Vehicle to purchase"},
    "s4_vehicle_price":       {"vi": "Giá xe (VNĐ)",                                   "en": "Vehicle price (VND)"},
    "s4_down_payment":        {"vi": "Số tiền trả trước (VNĐ)",                         "en": "Down payment (VND)"},
    "s4_down_payment_help":   {"vi": "Tối thiểu 20% giá xe",                            "en": "Minimum 20% of vehicle price"},
    "s4_loan_amount_label":   {"vi": "Số tiền cần vay",                                 "en": "Loan amount needed"},
    "s4_term":                {"vi": "Kỳ hạn vay",                                      "en": "Loan term"},
    "s4_term_unit":           {"vi": "{} tháng",                                        "en": "{} months"},
    "s4_down_warn":           {"vi": "⚠️ Trả trước {pct:.1f}% — dưới ngưỡng 20%",        "en": "⚠️ Down payment {pct:.1f}% — below the 20% threshold"},
    "s4_down_ok":             {"vi": "✓ Trả trước {pct:.1f}% — đạt yêu cầu",            "en": "✓ Down payment {pct:.1f}% — meets requirement"},
    "s4_doc_caption":         {"vi": "Sổ đỏ, cà vẹt xe, sổ tiết kiệm, hợp đồng thuê nhà (nếu có).",
                               "en": "Land title, vehicle registration, savings book, rental agreement (if any)."},

    # Step 5 - result
    "s5_title":               {"vi": "Kết quả xét duyệt",                              "en": "Assessment result"},
    "tab_repayment":          {"vi": "💵  Phương án trả nợ",                            "en": "💵  Repayment plans"},
    "tab_rate":               {"vi": "💡  Cấu thành lãi suất",                           "en": "💡  Interest rate breakdown"},
    "tab_docs":               {"vi": "📎  Chứng từ đã nộp",                              "en": "📎  Submitted documents"},

    # Decision labels
    "dec_approved_priority":  {"vi": "DUYỆT ƯU TIÊN",                                  "en": "PRIORITY APPROVED"},
    "dec_approved":           {"vi": "DUYỆT",                                          "en": "APPROVED"},
    "dec_approved_cond":      {"vi": "DUYỆT CÓ ĐIỀU KIỆN",                              "en": "CONDITIONALLY APPROVED"},
    "dec_manual":             {"vi": "XEM XÉT THỦ CÔNG",                                "en": "MANUAL REVIEW"},
    "dec_rejected":           {"vi": "TỪ CHỐI",                                         "en": "REJECTED"},
    "grade_word":             {"vi": "HẠNG",                                            "en": "GRADE"},
    "risk_word":              {"vi": "Rủi ro",                                          "en": "Risk"},
    "rl_very_low":            {"vi": "Rất thấp",                                        "en": "Very low"},
    "rl_low":                 {"vi": "Thấp",                                            "en": "Low"},
    "rl_medium":              {"vi": "Trung bình",                                      "en": "Medium"},
    "rl_medium_high":         {"vi": "Trung bình cao",                                   "en": "Medium-high"},
    "rl_high":                {"vi": "Cao",                                              "en": "High"},

    # Hero info-grid labels
    "hg_rate":                {"vi": "Lãi suất đề xuất",                                "en": "Suggested rate"},
    "hg_amount":              {"vi": "Số tiền vay",                                      "en": "Loan amount"},
    "hg_term":                {"vi": "Kỳ hạn",                                           "en": "Term"},
    "hg_product":             {"vi": "Sản phẩm vay",                                     "en": "Loan product"},
    "hg_term_months":         {"vi": "{} tháng",                                         "en": "{} months"},

    # Score panel
    "score_panel_title":      {"vi": "Phân tích điểm",                                  "en": "Score breakdown"},
    "score_excellent":        {"vi": "Xuất sắc",                                         "en": "Excellent"},
    "score_good":             {"vi": "Tốt",                                              "en": "Good"},
    "score_average":          {"vi": "Trung bình",                                       "en": "Average"},
    "score_needs_work":       {"vi": "Cần cải thiện",                                    "en": "Needs work"},
    "score_detail_expand":    {"vi": "🔍  Xem chi tiết điểm từng biến",                    "en": "🔍  View detailed variable scores"},
    "score_no_data":          {"vi": "Không chấm điểm do hồ sơ vi phạm điều kiện loại trực tiếp",
                               "en": "Not scored — profile violates a knockout rule"},

    # Hard rules panel
    "hr_panel_title":         {"vi": "Điều kiện loại trực tiếp",                          "en": "Knockout conditions"},
    "hr_all_pass":            {"vi": "Tất cả {} điều kiện đạt",                            "en": "All {} conditions met"},
    "hr_n_fail":              {"vi": "{} điều kiện không đạt",                              "en": "{} condition(s) not met"},
    "hr_current":             {"vi": "Hiện tại",                                           "en": "Current"},
    "hr_required":            {"vi": "Yêu cầu",                                            "en": "Required"},

    # Decision reason
    "reason_panel_title":     {"vi": "Lý do quyết định",                                   "en": "Decision rationale"},
    "next_step_label":        {"vi": "BƯỚC TIẾP THEO",                                    "en": "NEXT STEP"},
    "reason_approved_priority":{"vi": "Lịch sử tín dụng tốt, thu nhập ổn định. Đủ điều kiện duyệt ưu tiên với lãi suất thấp nhất.",
                               "en": "Strong credit history and stable income. Eligible for priority approval at the lowest rate."},
    "reason_approved":        {"vi": "Đáp ứng đầy đủ tiêu chí xét duyệt với mức rủi ro thấp. Duyệt với lãi suất tiêu chuẩn.",
                               "en": "Fully meets the approval criteria at low risk. Approved at the standard rate."},
    "reason_approved_cond":   {"vi": "Đạt ngưỡng nhưng có yếu tố rủi ro trung bình. Duyệt kèm điều kiện bổ sung.",
                               "en": "Meets the threshold but with medium-risk factors. Approved with additional conditions."},
    "reason_manual":          {"vi": "Hồ sơ ở ngưỡng biên giới, cần chuyên viên thẩm định thêm trước khi quyết định.",
                               "en": "Profile is borderline; an underwriter needs to review further before deciding."},
    "reason_rejected":        {"vi": "Vi phạm điều kiện loại trực tiếp. Khách hàng cần khắc phục trước khi nộp lại.",
                               "en": "Violates a knockout rule. The customer must remedy this before reapplying."},
    "next_approved_priority": {"vi": "Mời ký hợp đồng và chọn phương án trả nợ.",
                               "en": "Sign the contract and choose a repayment plan."},
    "next_approved":          {"vi": "Tiến hành ký hợp đồng theo lãi suất tiêu chuẩn.",
                               "en": "Proceed to signing at the standard rate."},
    "next_manual":             {"vi": "Chuyển hồ sơ cho chuyên viên thẩm định.",
                               "en": "Forward the profile to an underwriter."},
    "next_rejected":          {"vi": "Hướng dẫn khách hàng khắc phục điều kiện không đạt.",
                               "en": "Guide the customer on resolving the failing conditions."},

    # Hard rule descriptions (humanized)
    "hr_age_min":             {"vi": "Tuổi từ 20 trở lên",                                "en": "Age 20 or above"},
    "hr_age_max":             {"vi": "Tuổi không quá 60",                                  "en": "Age no greater than 60"},
    "hr_min_income":          {"vi": "Thu nhập tối thiểu 5 triệu/tháng",                   "en": "Minimum income 5M VND/month"},
    "hr_min_employment":      {"vi": "Công tác tối thiểu 3 tháng",                         "en": "Minimum employment 3 months"},
    "hr_cic_not_bad":         {"vi": "Không có nợ xấu CIC nhóm 3, 4, 5",                   "en": "No bad debt (CIC groups 3, 4, 5)"},
    "hr_dti_max":             {"vi": "Tỷ lệ DTI sau vay không vượt 60%",                    "en": "Post-loan DTI does not exceed 60%"},
    "hr_thr_age_min":         {"vi": "Từ 20 tuổi trở lên",                                  "en": "20 years or older"},
    "hr_thr_age_max":         {"vi": "Không quá 60 tuổi",                                   "en": "No older than 60"},
    "hr_thr_min_income":      {"vi": "Tối thiểu 5,000,000 VNĐ/tháng",                       "en": "At least 5,000,000 VND/month"},
    "hr_thr_min_employment":  {"vi": "Tối thiểu 3 tháng",                                   "en": "At least 3 months"},
    "hr_thr_cic":             {"vi": "Không thuộc nhóm 3, 4, 5",                            "en": "Not in groups 3, 4, 5"},
    "hr_thr_dti":             {"vi": "Không vượt quá 60%",                                  "en": "Not exceeding 60%"},
    "hr_age_unit":             {"vi": "{} tuổi",                                            "en": "{} years"},
    "hr_month_unit":           {"vi": "{} tháng",                                           "en": "{} months"},
    "hr_no_data":             {"vi": "Chưa có dữ liệu",                                    "en": "No data"},
    "hr_vnd_month":           {"vi": "{} VNĐ/tháng",                                       "en": "{} VND/month"},

    # Repayment slider
    "rep_title":              {"vi": "🧮 Công cụ ước tính khoản vay",                       "en": "🧮 Loan estimator"},
    "rep_grade_label":        {"vi": "Hạng",                                                "en": "Grade"},
    "rep_rate_range":         {"vi": "Khoảng lãi suất {min:.0f}% – {max:.0f}%/năm",          "en": "Rate range {min:.0f}% – {max:.0f}%/year"},
    "rep_applied_rate":       {"vi": "Lãi suất áp dụng",                                    "en": "Applied rate"},
    "rep_loan_amount":        {"vi": "Số tiền vay",                                          "en": "Loan amount"},
    "rep_term":               {"vi": "Kỳ hạn vay",                                           "en": "Loan term"},
    "rep_per_year":           {"vi": "%/năm",                                                "en": "%/year"},
    "rep_months":             {"vi": "tháng",                                                "en": "months"},
    "rep_monthly_label":      {"vi": "Khoản trả góp hàng tháng",                              "en": "Monthly payment"},
    "rep_total_interest":     {"vi": "Tổng tiền lãi",                                         "en": "Total interest"},
    "rep_total_paid":         {"vi": "Tổng phải trả",                                         "en": "Total payable"},
    "rep_note":               {"vi": "<b>*Ghi chú:</b> Khoản trả tháng hiển thị theo phương án niên kim (gốc + lãi đều). "
                                     "Kết quả tính toán mang tính chất tham khảo và có thể sai lệch nhỏ với kết quả thực tế tại các điểm giao dịch.",
                               "en": "<b>*Note:</b> The monthly payment shown is based on the annuity plan (level principal + interest). "
                                     "Calculations are indicative and may differ slightly from actual figures at the branch."},
    "rep_max_eq_price":       {"vi": "Tối đa = giá xe",                                       "en": "Max = vehicle price"},
    "rep_pa1_title":          {"vi": "📘 PA1 · Niên kim",                                      "en": "📘 Plan 1 · Annuity"},
    "rep_pa1_desc":           {"vi": "Trả đều mỗi kỳ",                                        "en": "Equal each period"},
    "rep_pa2_title":          {"vi": "📙 PA2 · Gốc đều",                                       "en": "📙 Plan 2 · Equal principal"},
    "rep_pa2_desc":           {"vi": "Trả giảm dần",                                          "en": "Decreasing payments"},
    "rep_pa2_savings":        {"vi": "💰 PA2 tiết kiệm so với PA1",                            "en": "💰 Plan 2 savings vs Plan 1"},
    "rep_pa2_savings_desc":   {"vi": "Số lãi giảm được",                                       "en": "Interest reduced"},
    "rep_pa2_savings_eq":     {"vi": "Tương đương <b style=\"color:#0F7A5C;\">{:.1f}%</b> tổng lãi",
                               "en": "Equivalent to <b style=\"color:#0F7A5C;\">{:.1f}%</b> of total interest"},
    "rep_total_int_short":    {"vi": "Tổng lãi:",                                              "en": "Total interest:"},
    "rep_tab_chart":          {"vi": "📈  Biểu đồ so sánh",                                     "en": "📈  Comparison charts"},
    "rep_tab_p1":             {"vi": "📘  Lịch trả PA1",                                        "en": "📘  Plan 1 schedule"},
    "rep_tab_p2":             {"vi": "📙  Lịch trả PA2",                                        "en": "📙  Plan 2 schedule"},
    "rep_tab_dl":             {"vi": "⬇️  Tải file",                                            "en": "⬇️  Download"},
    "rep_chart_cashflow":     {"vi": "Dòng tiền trả mỗi kỳ",                                   "en": "Cashflow per period"},
    "rep_chart_balance":      {"vi": "Dư nợ còn lại theo thời gian",                           "en": "Outstanding balance over time"},
    "rep_dl_intro":            {"vi": "Tải lịch trả nợ về máy để chia sẻ hoặc lưu trữ.",
                               "en": "Download the repayment schedule for sharing or archiving."},
    "rep_dl_excel":           {"vi": "📊  Tải Excel (cả 2 phương án)",                          "en": "📊  Download Excel (both plans)"},
    "rep_dl_csv":             {"vi": "📄  Tải CSV (chỉ PA1)",                                   "en": "📄  Download CSV (Plan 1 only)"},
    "rep_rejected_info":      {"vi": "ℹ️ Hồ sơ bị từ chối, không tính phương án trả nợ.",        "en": "ℹ️ Profile rejected — no repayment plan calculated."},
    "rep_period":             {"vi": "Kỳ",                                                     "en": "Period"},
    "rep_p1_legend":          {"vi": "PA1 — Niên kim",                                          "en": "Plan 1 — Annuity"},
    "rep_p2_legend":          {"vi": "PA2 — Gốc đều",                                           "en": "Plan 2 — Equal principal"},
    "rep_df_opening":         {"vi": "Dư nợ đầu kỳ",                                            "en": "Opening balance"},
    "rep_df_principal":       {"vi": "Gốc",                                                     "en": "Principal"},
    "rep_df_interest":        {"vi": "Lãi",                                                     "en": "Interest"},
    "rep_df_total":           {"vi": "Tổng trả",                                                "en": "Total payment"},
    "rep_df_closing":         {"vi": "Dư nợ cuối",                                              "en": "Closing balance"},

    # Rate explanation
    "rate_explain_title":     {"vi": "Cấu thành lãi suất theo phương pháp khoa học",            "en": "Scientific interest-rate decomposition"},
    "rate_explain_intro":     {"vi": "Lãi suất cho vay được tính dựa trên 4 thành phần chính, theo thông lệ quốc tế và quy định của NHNN Việt Nam.",
                               "en": "The lending rate is built from four components, in line with international practice and the State Bank of Vietnam's regulations."},
    "rate_formula_title":     {"vi": "🧮 Công thức tính lãi suất",                              "en": "🧮 Rate formula"},
    "rate_formula":           {"vi": "r = LS_điều_hành + Chi_phí_vốn + Biên_rủi_ro<sub>(theo hạng)</sub> + Phí_dịch_vụ",
                               "en": "r = Policy_rate + Cost_of_funds + Risk_premium<sub>(by grade)</sub> + Service_fee"},
    "rate_risk_premium":      {"vi": "Biên rủi ro hạng <b>{grade}</b> ({risk})",                "en": "Risk premium for grade <b>{grade}</b> ({risk})"},
    "rate_total_label":       {"vi": "Tổng lãi suất đề xuất (mức trung bình)",                  "en": "Total suggested rate (mid-point)"},
    "rate_per_year":          {"vi": "%/năm",                                                   "en": "%/year"},
    "rate_explain_card":      {"vi": "📚 Giải thích từng thành phần",                            "en": "📚 Component explanations"},
    "rate_exp_1":             {"vi": "<b>1. Lãi suất điều hành NHNN ({rate}%):</b> Lãi suất tái cấp vốn do Ngân hàng Nhà nước Việt Nam công bố, là chuẩn cho toàn hệ thống. Nguồn: {src}.",
                               "en": "<b>1. Policy rate ({rate}%):</b> The refinancing rate published by the State Bank of Vietnam — the system-wide benchmark. Source: {src}."},
    "rate_exp_2":             {"vi": "<b>2. Chi phí huy động vốn ({rate}%):</b> Chi phí thực tế ngân hàng phải trả cho người gửi tiết kiệm để có vốn cho vay lại. Phụ thuộc vào kỳ hạn huy động và cạnh tranh thị trường.",
                               "en": "<b>2. Cost of funds ({rate}%):</b> The actual cost the bank pays depositors to have funds available to lend. Depends on funding tenor and market competition."},
    "rate_exp_3":             {"vi": "<b>3. Biên rủi ro ({rate}% cho hạng {grade}):</b> Phần bù rủi ro tương ứng với khả năng vỡ nợ của khách hàng. Hạng càng cao biên càng thấp. Đây là cấu phần <i>quan trọng nhất</i> của scorecard — nó biến điểm tín dụng thành con số thực tế khách hàng phải trả.",
                               "en": "<b>3. Risk premium ({rate}% for grade {grade}):</b> The premium that compensates for the customer's default probability. Higher grades imply lower premiums. This is the <i>most important</i> output of the scorecard — it turns the credit score into a real cost the customer pays."},
    "rate_exp_4":             {"vi": "<b>4. Phí dịch vụ và lợi nhuận ({rate}%):</b> Bao gồm chi phí vận hành, công nghệ, nhân sự, và lợi nhuận kỳ vọng của ngân hàng.",
                               "en": "<b>4. Service fee & profit ({rate}%):</b> Operating, technology and staffing costs plus the bank's target profit margin."},
    "rate_ref_title":         {"vi": "Bảng tham chiếu lãi suất theo hạng tín dụng",              "en": "Reference rate table by credit grade"},
    "rate_ref_grade":         {"vi": "Hạng",                                                    "en": "Grade"},
    "rate_ref_minscore":      {"vi": "Điểm tối thiểu",                                          "en": "Min score"},
    "rate_ref_risk":          {"vi": "Mức rủi ro",                                              "en": "Risk level"},
    "rate_ref_premium":       {"vi": "Biên rủi ro",                                             "en": "Risk premium"},
    "rate_ref_range":         {"vi": "Khoảng lãi suất",                                         "en": "Rate range"},
    "rate_ref_avg":           {"vi": "Trung bình",                                              "en": "Average"},
    "rate_caption":           {"vi": "💡 Hồ sơ này hạng **{grade}**, đang chọn lãi suất **{rate:.1f}%/năm** — kéo slider ở tab 'Phương án trả nợ' để điều chỉnh.",
                               "en": "💡 This profile is grade **{grade}**, currently selected rate **{rate:.1f}%/year** — drag the slider in the 'Repayment plans' tab to adjust."},

    # Rejected
    "rate_rejected_info":     {"vi": "ℹ️ Hồ sơ bị từ chối, không có lãi suất đề xuất.",         "en": "ℹ️ Profile rejected — no suggested rate."},

    # Documents tab
    "docs_title":             {"vi": "Chứng từ đã nộp theo từng nhóm",                          "en": "Submitted documents by category"},
    "docs_g1":                {"vi": "Nhóm 1 — Lịch sử tín dụng",                                "en": "Category 1 — Credit history"},
    "docs_g2":                {"vi": "Nhóm 2 — Thu nhập & việc làm",                              "en": "Category 2 — Income & employment"},
    "docs_g3":                {"vi": "Nhóm 3 — Nhân thân",                                       "en": "Category 3 — Personal info"},
    "docs_g4":                {"vi": "Nhóm 4 — Tài sản sở hữu",                                   "en": "Category 4 — Owned assets"},
    "docs_count":             {"vi": "{} chứng từ",                                              "en": "{} document(s)"},
    "docs_none":              {"vi": "_Chưa có chứng từ nào được tải lên cho nhóm này_",          "en": "_No documents uploaded for this category yet_"},
    "docs_total":             {"vi": "Tổng số chứng từ đã nộp",                                  "en": "Total submitted documents"},

    # Group names (for translation when echoing back results)
    "group_credit_history":   {"vi": "Lịch sử tín dụng",                                        "en": "Credit history"},
    "group_income":           {"vi": "Thu nhập & việc làm",                                      "en": "Income & employment"},
    "group_personal":         {"vi": "Nhân thân",                                                 "en": "Personal information"},
    "group_assets":           {"vi": "Tài sản sở hữu",                                            "en": "Owned assets"},

    # Variable names
    "var_credit_history_cic": {"vi": "Lịch sử CIC 24 tháng",                                    "en": "CIC history (24 months)"},
    "var_active_loans_count": {"vi": "Số khoản vay đang hoạt động",                              "en": "Active loans count"},
    "var_dti_after_loan":     {"vi": "DTI sau khi vay mới",                                      "en": "DTI after new loan"},
    "var_credit_history_length_years": {"vi": "Thời gian có lịch sử tín dụng",                     "en": "Length of credit history"},
    "var_monthly_income_vnd": {"vi": "Thu nhập hàng tháng",                                      "en": "Monthly income"},
    "var_employment_contract":{"vi": "Loại hợp đồng lao động",                                   "en": "Employment contract type"},
    "var_employment_duration_months":{"vi": "Thời gian làm việc hiện tại",                        "en": "Current employment duration"},
    "var_salary_method":      {"vi": "Hình thức nhận lương",                                     "en": "Salary payment method"},
    "var_age":                {"vi": "Tuổi",                                                     "en": "Age"},
    "var_marital_status":     {"vi": "Tình trạng hôn nhân",                                      "en": "Marital status"},
    "var_dependents":         {"vi": "Số người phụ thuộc",                                       "en": "Number of dependents"},
    "var_education":          {"vi": "Trình độ học vấn",                                         "en": "Education level"},
    "var_residency_status":   {"vi": "Tình trạng cư trú",                                        "en": "Residency status"},
    "var_real_estate":        {"vi": "Bất động sản đứng tên",                                    "en": "Titled real estate"},
    "var_vehicle":            {"vi": "Phương tiện sở hữu",                                       "en": "Vehicle ownership"},
    "var_savings_vnd":        {"vi": "Tiền gửi tiết kiệm",                                        "en": "Savings deposits"},

    # Misc
    "loading_dots":           {"vi": "—",                                                       "en": "—"},
    "persona_letter_label":   {"vi": "Persona {}",                                              "en": "Persona {}"},
    "section_doc":            {"vi": "Tài liệu chứng minh",                                     "en": "Supporting documents"},
}


def t(key: str, **fmt) -> str:
    """Translate a key to current language; format with kwargs if provided."""
    lang = st.session_state.get("language", "vi")
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    s = entry.get(lang) or entry.get("vi") or key
    if fmt:
        try:
            return s.format(**fmt)
        except (KeyError, IndexError):
            return s
    return s


def t_pos(key: str, *args) -> str:
    """Like t() but uses positional .format()."""
    lang = st.session_state.get("language", "vi")
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    s = entry.get(lang) or entry.get("vi") or key
    if args:
        try:
            return s.format(*args)
        except (KeyError, IndexError):
            return s
    return s


def translate_group_name(group_key: str, fallback: str) -> str:
    """Translate scoring group name based on key."""
    key = f"group_{group_key}"
    entry = TRANSLATIONS.get(key)
    if entry:
        return t(key)
    return fallback


def translate_variable_name(var_key: str, fallback: str) -> str:
    """Translate variable name based on key."""
    key = f"var_{var_key}"
    entry = TRANSLATIONS.get(key)
    if entry:
        return t(key)
    return fallback


def translate_risk_level(risk_level: str) -> str:
    """Translate risk_level enum -> human readable in current language."""
    mapping = {
        "very_low":    t("rl_very_low"),
        "low":         t("rl_low"),
        "medium":      t("rl_medium"),
        "medium_high": t("rl_medium_high"),
        "high":        t("rl_high"),
    }
    return mapping.get(risk_level, "—")


def translate_decision(dec: str) -> str:
    mapping = {
        "approved_priority":    t("dec_approved_priority"),
        "approved":             t("dec_approved"),
        "approved_conditional": t("dec_approved_cond"),
        "manual_review":        t("dec_manual"),
        "rejected":             t("dec_rejected"),
    }
    return mapping.get(dec, dec)


# ============================================================
# CSS - Navy + Gold (refined for v4)
# ============================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    :root {
        --navy: #0A2540;
        --navy-light: #1B3A5C;
        --gold: #C9A961;
        --gold-light: #E0C988;
        --gold-deep: #A88A47;
        --bg-soft: #F5F7FA;
        --bg-cream: #FDFAF2;
        --text-primary: #0A2540;
        --text-secondary: #5A6B80;
        --text-muted: #8593A8;
        --border-soft: #E5E9F0;
        --success: #0F7A5C;
        --success-bg: #E3F4EC;
        --warning: #B87300;
        --warning-bg: #FFF4DB;
        --danger: #B33A3A;
        --danger-bg: #FCE4E4;
    }

    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1240px;
    }

    h1, h2, h3, h4 {
        color: var(--navy) !important;
        font-weight: 600 !important;
        letter-spacing: -0.012em;
    }
    h1 { font-size: 1.75rem !important; }
    h2 { font-size: 1.4rem !important; }
    h3 { font-size: 1.15rem !important; }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #0A2540 0%, #1B3A5C 100%);
        color: white;
        padding: 1.5rem 2rem 1.75rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 18px rgba(10, 37, 64, 0.10);
        position: relative;
        overflow: hidden;
    }
    .hero-header::after {
        content: "";
        position: absolute;
        top: 0; right: 0;
        width: 220px; height: 100%;
        background: radial-gradient(circle at top right, rgba(201,169,97,0.18), transparent 70%);
        pointer-events: none;
    }
    .hero-logo-wrap {
        background: rgba(255,255,255,0.97);
        border-radius: 10px;
        padding: 0.55rem 1.1rem;
        display: inline-block;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.18),
                    0 0 0 1px rgba(201,169,97,0.35);
        position: relative;
        z-index: 1;
    }
    .hero-logo {
        height: 54px;
        width: auto;
        display: block;
    }
    .hero-header h1 {
        color: white !important;
        margin: 0 0 0.3rem 0 !important;
        font-size: 1.7rem !important;
        letter-spacing: -0.02em;
    }
    .hero-header p {
        color: #D4DCE8;
        margin: 0;
        font-size: 0.95rem;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(201, 169, 97, 0.18);
        color: #E0C988;
        padding: 0.22rem 0.75rem;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-secondary);
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.5rem;
    }
    .step-indicator .step-dot {
        width: 6px; height: 6px;
        background: var(--gold);
        border-radius: 50%;
    }

    .persona-card {
        background: white;
        border: 1px solid var(--border-soft);
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
    .persona-card-icon { font-size: 2rem; margin-bottom: 0.5rem; }
    .persona-card-name { font-weight: 600; color: var(--navy); font-size: 1.05rem; margin-bottom: 0.3rem; }
    .persona-card-desc { color: var(--text-secondary); font-size: 0.85rem; line-height: 1.45; flex-grow: 1; }
    .persona-card-badge {
        font-size: 0.72rem; font-weight: 600;
        padding: 0.3rem 0.65rem;
        border-radius: 6px;
        margin-top: 0.5rem;
        display: inline-block;
        letter-spacing: 0.02em;
    }
    .badge-approved { background: var(--success-bg); color: var(--success); }
    .badge-review   { background: var(--warning-bg); color: var(--warning); }
    .badge-rejected { background: var(--danger-bg); color: var(--danger); }
    .badge-custom   { background: #E8EEF5; color: var(--navy); }

    .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-left: 3px solid var(--gold);
        padding-left: 0.75rem;
        color: var(--navy);
        font-weight: 600;
        font-size: 1.08rem;
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
        border: 1px solid var(--border-soft) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--navy) !important;
        background: var(--bg-soft) !important;
    }

    .result-status-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .status-approved { background: var(--success-bg); color: var(--success); }
    .status-review   { background: var(--warning-bg); color: var(--warning); }
    .status-rejected { background: var(--danger-bg); color: var(--danger); }

    /* Rate explain card */
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
        border-bottom: 1px dotted var(--border-soft);
    }
    .rate-component:last-child {
        border-bottom: 2px solid var(--gold);
        padding-top: 0.6rem;
        margin-top: 0.3rem;
        font-weight: 600;
    }
    .rate-component .label { color: var(--text-secondary); }
    .rate-component .value { color: var(--navy); font-weight: 500; }
    .rate-component:last-child .value { color: var(--gold-deep); font-size: 1.05rem; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-bottom: 1px solid var(--border-soft);
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

    section[data-testid="stSidebar"] { background: var(--navy) !important; }
    section[data-testid="stSidebar"] * { color: #D4DCE8 !important; }
    section[data-testid="stSidebar"] h3 { color: white !important; }

    /* Language switcher inside sidebar */
    .lang-switcher {
        display: flex;
        gap: 0.4rem;
        background: rgba(255,255,255,0.06);
        padding: 0.25rem;
        border-radius: 8px;
        margin: 0.5rem 0 1.25rem 0;
    }

    .stepper-item {
        position: relative;
        padding: 0.5rem 0 0.5rem 1.5rem;
        font-size: 0.9rem;
    }
    .stepper-item::before {
        content: '';
        position: absolute; left: 0; top: 0.75rem;
        width: 10px; height: 10px;
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
        border: 1px solid var(--border-soft) !important;
        border-radius: 8px !important;
    }

    /* === v4: Result dashboard polish === */

    /* Score gauge — bigger and more elegant */
    .score-hero {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid var(--border-soft);
        border-top: 4px solid;
        border-radius: 14px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 14px rgba(10,37,64,0.06);
    }
    .score-hero.approved { border-top-color: var(--success); }
    .score-hero.review   { border-top-color: var(--warning); }
    .score-hero.rejected { border-top-color: var(--danger); }

    .score-hero-grid {
        display: grid;
        grid-template-columns: minmax(220px, 280px) 1fr;
        gap: 2rem;
        align-items: center;
    }

    .gauge-block {
        text-align: center;
        padding: 1rem 1.25rem;
        background: linear-gradient(180deg, #FDFAF2 0%, #FFFFFF 100%);
        border: 1px solid var(--gold-light);
        border-radius: 12px;
        box-shadow: 0 1px 6px rgba(201,169,97,0.10);
    }
    .gauge-number {
        font-size: 3.6rem;
        font-weight: 800;
        line-height: 1;
        color: var(--navy);
        letter-spacing: -0.03em;
        font-feature-settings: "tnum";
    }
    .gauge-suffix {
        font-size: 1.05rem;
        color: var(--text-secondary);
        font-weight: 500;
        margin-left: 0.15rem;
    }
    .gauge-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-top: 0.4rem;
    }
    .gauge-grade {
        display: inline-block;
        background: var(--navy);
        color: var(--gold);
        padding: 0.45rem 1.1rem;
        border-radius: 7px;
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.06em;
        margin-top: 0.85rem;
        font-feature-settings: "tnum";
    }
    .gauge-risk {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-top: 0.55rem;
        letter-spacing: 0.02em;
    }

    .hero-meta {
        display: flex;
        flex-direction: column;
        gap: 0.85rem;
    }
    .hero-meta-top {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        flex-wrap: wrap;
    }
    .hero-customer-line {
        font-size: 0.86rem;
        color: var(--text-secondary);
    }
    .hero-customer-line b { color: var(--navy); font-weight: 600; }

    .info-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.65rem;
    }
    .info-card {
        background: white;
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 0.6rem 0.85rem;
        transition: all 0.15s ease;
    }
    .info-card:hover {
        border-color: var(--gold-light);
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(10,37,64,0.04);
    }
    .info-card-label {
        font-size: 0.65rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    .info-card-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--navy);
        margin-top: 0.2rem;
        font-feature-settings: "tnum";
    }
    .info-card-value.gold { color: var(--gold-deep); }
    .info-card-product { font-size: 0.85rem !important; }

    /* Score panel - more compact */
    .score-panel {
        background: white;
        border: 1px solid var(--border-soft);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
    }
    .score-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.55rem;
    }
    .score-panel-title {
        font-weight: 600;
        color: var(--navy);
        font-size: 0.95rem;
    }
    .score-panel-value {
        font-feature-settings: "tnum";
    }
    .score-panel-value .num {
        color: var(--navy);
        font-weight: 700;
        font-size: 1.05rem;
    }
    .score-panel-value .sep {
        color: var(--text-secondary);
        font-size: 0.85rem;
    }
    .score-panel-value .pct {
        color: var(--gold-deep);
        font-weight: 700;
        font-size: 1.05rem;
        margin-left: 0.5rem;
    }

    .progress-rail {
        background: #F0F2F5;
        height: 8px;
        border-radius: 4px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .group-row {
        background: white;
        border: 1px solid var(--border-soft);
        border-radius: 7px;
        padding: 0.55rem 0.85rem;
        margin-bottom: 0.4rem;
    }
    .group-row-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.4rem;
    }
    .group-row-name {
        font-weight: 600;
        color: var(--navy);
        font-size: 0.85rem;
    }
    .group-row-weight {
        color: var(--text-secondary);
        font-size: 0.7rem;
        margin-left: 0.3rem;
        font-weight: 500;
    }
    .group-row-meta {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        font-feature-settings: "tnum";
    }
    .group-row-tag {
        color: white;
        font-size: 0.62rem;
        padding: 0.12rem 0.4rem;
        border-radius: 3px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .group-row-points {
        font-size: 0.78rem;
        color: var(--navy);
        font-weight: 500;
    }
    .group-row-pct {
        font-weight: 700;
        font-size: 0.9rem;
        min-width: 40px;
        text-align: right;
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
    if "language" not in st.session_state:
        st.session_state.language = "vi"  # default Vietnamese
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
    if "selected_rate" not in st.session_state:
        st.session_state.selected_rate = None


def reset_state():
    # Preserve language across reset
    lang = st.session_state.get("language", "vi")
    keys_to_clear = ["step", "applicant", "profile_meta", "uploaded_files",
                     "selected_persona", "selected_rate",
                     "calc_loan_amount", "calc_term_months",
                     "rate_slider", "amount_slider", "term_slider"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    init_state()
    st.session_state.language = lang


def load_persona_to_state(persona):
    st.session_state.applicant = {
        "personal_info": persona["personal_info"].copy(),
        "employment": persona["employment"].copy(),
        "credit_history": persona["credit_history"].copy(),
        "assets": persona["assets"].copy(),
        "loan_request": persona["loan_request"].copy(),
    }
    st.session_state.selected_persona = persona["persona_id"]
    persona_letter = persona["persona_id"][0]
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
import streamlit.components.v1 as components

def render_hero(scorecard):
    logo_html = ""
    if LOGO_FULL_B64:
        logo_html = f"""
        <div class="hero-logo-wrap">
            <img src="data:image/png;base64,{LOGO_FULL_B64}" class="hero-logo"/>
        </div>
        """

    html = f"""
    <style>
    .hero-header {{
        background: linear-gradient(135deg, #0f2a44, #1e3a5f);
        padding: 28px 20px;
        border-radius: 18px;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }}

    .hero-logo-wrap {{
        display: flex;
        justify-content: center;
        margin-bottom: 16px;
    }}

    .hero-logo {{
        max-width: 260px;
        height: auto;
        filter: drop-shadow(0 4px 10px rgba(0,0,0,0.4));
    }}

    .hero-badge {{
        font-size: 13px;
        opacity: 0.75;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }}

    h1 {{
        margin: 6px 0;
        font-size: 30px;
        font-weight: 600;
    }}

    p {{
        margin: 0;
        font-size: 15px;
        color: #d1d5db;
    }}
    </style>

    <div class="hero-header">
        {logo_html}
        <div class="hero-badge">{t('app_badge')}</div>
        <h1>{t('app_title')}</h1>
        <p>{scorecard['product']['name']} · {t('app_subtitle')}</p>
    </div>
    """

    components.html(html, height=320)

# ============================================================
# SIDEBAR (with language switcher)
# ============================================================

def render_sidebar(scorecard):
    with st.sidebar:
        if LOGO_ICON_B64:
            st.markdown(f"""
            <div style="text-align:center; padding:1rem 0 0.75rem 0;">
                <img src="data:image/png;base64,{LOGO_ICON_B64}" alt="Khá Bank"
                     style="height:72px; width:auto; display:inline-block;
                            filter: drop-shadow(0 4px 12px rgba(0,0,0,0.35));"/>
                <div style="font-weight:700; color:white; margin-top:0.5rem;
                            letter-spacing:0.04em; font-size:1.05rem;">KHÁ BANK</div>
                <div style="font-size:0.72rem; color:#C9A961; margin-top:0.15rem;
                            letter-spacing:0.18em; text-transform:uppercase;
                            font-weight:600;">Bảnh Bao — Tin Cậy</div>
                <div style="font-size:0.78rem; color:#8593A8; margin-top:0.5rem;">{t('sidebar_sub')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align:center; padding:1rem 0 0.75rem 0;">
                <div style="font-size:2rem;">🏛️</div>
                <div style="font-weight:600; color:white; margin-top:0.3rem;">{t('sidebar_title')}</div>
                <div style="font-size:0.8rem; color:#8593A8;">{t('sidebar_sub')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Language switcher
        st.markdown(f"""
        <div style="font-size:0.7rem; color:#8593A8; text-transform:uppercase; letter-spacing:0.1em;
                    font-weight:600; margin-top:0.5rem; margin-bottom:0.3rem; text-align:center;">
            🌐 {t('lang_label')}
        </div>
        """, unsafe_allow_html=True)
        col_vi, col_en = st.columns(2)
        with col_vi:
            vi_type = "primary" if st.session_state.language == "vi" else "secondary"
            if st.button("🇻🇳 Tiếng Việt", key="lang_vi", use_container_width=True, type=vi_type):
                if st.session_state.language != "vi":
                    st.session_state.language = "vi"
                    st.rerun()
        with col_en:
            en_type = "primary" if st.session_state.language == "en" else "secondary"
            if st.button("🇬🇧 English", key="lang_en", use_container_width=True, type=en_type):
                if st.session_state.language != "en":
                    st.session_state.language = "en"
                    st.rerun()

        st.markdown('<div style="border-bottom:1px solid #2D4A6B; margin:0.75rem 0 1rem 0;"></div>',
                    unsafe_allow_html=True)

        # 7 steps stepper
        steps = [
            (t("step_choose"),    f"{t('step_word')} 0"),
            (t("step_init"),      f"{t('step_word')} 0.5"),
            (t("step_credit"),    f"{t('step_word')} 1"),
            (t("step_income"),    f"{t('step_word')} 2"),
            (t("step_personal"),  f"{t('step_word')} 3"),
            (t("step_assets"),    f"{t('step_word')} 4"),
            (t("step_result"),    f"{t('step_word')} 5"),
        ]

        st.markdown(f"### {t('sidebar_progress')}")
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

        if st.session_state.profile_meta.get("full_name"):
            st.markdown(f"""
            <div style="margin-top:1.5rem; padding:0.75rem; background:#1B3A5C; border-radius:8px; border-left:3px solid var(--gold);">
                <div style="font-size:0.7rem; color:#8593A8; text-transform:uppercase; letter-spacing:0.05em;">{t('sidebar_evaluating')}</div>
                <div style="font-weight:600; color:white; margin-top:0.2rem;">{st.session_state.profile_meta['full_name']}</div>
                <div style="font-size:0.78rem; color:#D4DCE8; margin-top:0.2rem;">{st.session_state.profile_meta['profile_id']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t("btn_reset"), use_container_width=True, type="secondary"):
            reset_state()
            st.rerun()

        st.markdown("---")
        st.markdown(f"### {t('sidebar_scorecard')}")
        st.markdown(f"""
        <div style="font-size:0.85rem; color:#D4DCE8;">
            <div style="margin-bottom:0.5rem;">{t('sidebar_max_score')}: <b>{scorecard['scoring_system']['max_score']}</b></div>
        """, unsafe_allow_html=True)
        for key, group in scorecard["scoring_groups"].items():
            group_name_translated = translate_group_name(key, group["name"])
            st.markdown(
                f'<div style="font-size:0.82rem; margin:0.2rem 0;">• {group_name_translated}: <b>{group["weight"]*100:.0f}%</b></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# Helpers: step header / nav
# ============================================================

def render_step_header(step_num, total, title, subtitle, icon=""):
    st.markdown(
        f'<div class="step-indicator"><span class="step-dot"></span>{t("step_word")} {step_num} / {total}</div>',
        unsafe_allow_html=True,
    )
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


def render_nav_buttons(next_label=None, allow_back=True):
    if next_label is None:
        next_label = t("btn_next")
    col_l, _, col_r = st.columns([1, 2, 1])
    with col_l:
        if allow_back and st.button(t("btn_back"), use_container_width=True, type="secondary"):
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
    st.markdown(
        f'<div class="step-indicator"><span class="step-dot"></span>{t("s0_indicator")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {t('s0_title')}")
    st.markdown(
        f"<p style='color:#5A6B80; margin-bottom:1.5rem;'>{t('s0_intro')}</p>",
        unsafe_allow_html=True,
    )

    persona_meta = [
        {"icon": "🟢", "badge": t("s0_priority"), "badge_cls": "badge-approved"},
        {"icon": "🟡", "badge": t("s0_manual"),   "badge_cls": "badge-review"},
        {"icon": "🔴", "badge": t("s0_rejected"), "badge_cls": "badge-rejected"},
    ]

    cols = st.columns(4)
    for i, (col, persona) in enumerate(zip(cols[:3], personas)):
        with col:
            meta = persona_meta[i]
            persona_letter = persona["persona_id"][0]
            st.markdown(f"""
            <div class="persona-card">
                <div class="persona-card-icon">{meta['icon']}</div>
                <div class="persona-card-name">{t_pos('persona_letter_label', persona_letter)}</div>
                <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.5rem;">
                    {persona['full_name_censored']}
                </div>
                <div class="persona-card-desc">{persona['description']}</div>
                <div class="persona-card-badge {meta['badge_cls']}">{meta['badge']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{t('s0_pick')} {persona_letter}", key=f"pick_{i}",
                         use_container_width=True, type="primary"):
                load_persona_to_state(persona)
                next_step()
                st.rerun()

    with cols[3]:
        st.markdown(f"""
        <div class="persona-card">
            <div class="persona-card-icon">✍️</div>
            <div class="persona-card-name">{t('s0_custom_title')}</div>
            <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.5rem;">
                {t('s0_custom_short')}
            </div>
            <div class="persona-card-desc">{t('s0_custom_desc')}</div>
            <div class="persona-card-badge badge-custom">{t('s0_custom_badge')}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("s0_pick_custom"), key="pick_custom", use_container_width=True, type="primary"):
            st.session_state.selected_persona = None
            st.session_state.profile_meta = {
                "full_name": "",
                "profile_id": f"HS-CUSTOM-{datetime.now().strftime('%Y%m%d%H%M')}",
                "submission_date": datetime.now().strftime("%d/%m/%Y"),
            }
            next_step()
            st.rerun()


# ============================================================
# STEP 0.5: INIT PROFILE
# ============================================================

def render_step_init_profile():
    render_step_header("0.5", 6, t("s05_title"), t("s05_subtitle"), "🪪")

    pm = st.session_state.profile_meta

    if not pm.get("profile_id"):
        pm["profile_id"] = f"HS-CUSTOM-{datetime.now().strftime('%Y%m%d%H%M')}"

    render_section(t("s05_section"), "📝")

    col1, col2 = st.columns(2)
    with col1:
        pm["full_name"] = st.text_input(
            t("s05_full_name"),
            value=pm.get("full_name", ""),
            placeholder=t("s05_full_name_ph"),
            help=t("s05_full_name_help"),
        )
        pm["cccd_number"] = st.text_input(
            t("s05_id_num"),
            value=pm.get("cccd_number", ""),
            placeholder=t("s05_id_num_ph"),
            max_chars=12,
            help=t("s05_id_num_help"),
        )
        pm["profile_id"] = st.text_input(
            t("s05_profile_id"),
            value=pm.get("profile_id", ""),
            help=t("s05_profile_id_help"),
        )
    with col2:
        pm["submission_date"] = st.text_input(
            t("s05_submission_date"),
            value=pm.get("submission_date", datetime.now().strftime("%d/%m/%Y")),
        )
        st.markdown(f"""
        <div style="background:var(--bg-cream); padding:0.85rem 1rem; border-radius:8px;
                    border-left:3px solid var(--gold); margin-top:1rem;">
            <div style="font-size:0.78rem; color:var(--text-secondary); font-weight:500;">{t('s05_status_label')}</div>
            <div style="font-weight:600; color:var(--navy); margin-top:0.2rem;">{t('s05_status_value')}</div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.4rem;">
                {t('s05_status_desc')}
            </div>
        </div>
        <div style="background:#E8EEF5; padding:0.75rem 1rem; border-radius:8px;
                    border-left:3px solid var(--navy); margin-top:0.6rem;">
            <div style="font-size:0.8rem; color:var(--navy); line-height:1.5;">
                {t('s05_security')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    if pm.get("full_name"):
        cccd_display = pm.get("cccd_number") or "—"
        st.markdown(f"""
        <div style="background:white; border:1px solid var(--border-soft); border-radius:10px;
                    padding:1.25rem 1.5rem; margin-top:1.5rem;">
            <div style="font-size:0.78rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.05em; margin-bottom:0.5rem;">{t('s05_summary_title')}</div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:1rem;">
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">{t('s05_customer')}</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem;">{pm['full_name']}</div>
                </div>
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">{t('s05_id_short')}</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem; font-family:'Courier New',monospace;">{cccd_display}</div>
                </div>
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">{t('s05_profile_id_short')}</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem; font-family:'Courier New',monospace;">{pm['profile_id']}</div>
                </div>
                <div>
                    <div style="font-size:0.78rem; color:var(--text-secondary);">{t('s05_submission_short')}</div>
                    <div style="font-weight:600; color:var(--navy); margin-top:0.2rem;">{pm['submission_date']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    missing = []
    if not pm.get("full_name"):
        missing.append(t("s05_field_name"))
    if not pm.get("cccd_number"):
        missing.append(t("s05_field_id"))
    if missing:
        st.warning(t_pos("s05_warn_missing", t("s05_field_and").join(missing)))

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, _, col_r = st.columns([1, 2, 1])
    with col_l:
        if st.button(t("btn_back"), use_container_width=True, type="secondary"):
            prev_step()
            st.rerun()
    with col_r:
        if pm.get("full_name") and pm.get("cccd_number"):
            if st.button(t("btn_next"), type="primary", use_container_width=True):
                next_step()
                st.rerun()
        else:
            st.button(t("btn_next"), type="primary", use_container_width=True, disabled=True)


# ============================================================
# STEP 1: CREDIT
# ============================================================

def render_step1_credit(scorecard):
    group_cfg = scorecard['scoring_groups']['credit_history']
    render_step_header(
        1, 6,
        t("s1_title"),
        t("s1_subtitle", weight=int(group_cfg['weight']*100), max=group_cfg['max_points']),
        "📊",
    )

    ch = st.session_state.applicant["credit_history"]

    render_section(t("s1_section"), "🗂️")
    col1, col2 = st.columns(2)
    cic_options = ["no_history", "group1_all_ontime", "group2_once", "group2_multiple",
                   "group3", "group4", "group5"]
    cic_label_map = {
        "no_history":         t("cic_no_history"),
        "group1_all_ontime":  t("cic_group1_all_ontime"),
        "group2_once":        t("cic_group2_once"),
        "group2_multiple":    t("cic_group2_multiple"),
        "group3":             t("cic_group3"),
        "group4":             t("cic_group4"),
        "group5":             t("cic_group5"),
    }
    with col1:
        ch["credit_history_cic"] = st.selectbox(
            t("s1_cic"),
            options=cic_options,
            format_func=lambda x: cic_label_map[x],
            index=cic_options.index(ch.get("credit_history_cic", "group1_all_ontime")),
            help=t("s1_cic_help"),
        )
        ch["active_loans_count"] = st.number_input(
            t("s1_active_loans"),
            min_value=0, max_value=20,
            value=ch.get("active_loans_count", 0),
        )
    with col2:
        ch["credit_history_length_years"] = st.number_input(
            t("s1_history_years"),
            min_value=0, max_value=50,
            value=ch.get("credit_history_length_years", 0),
        )
        ch["dti_current"] = st.slider(
            t("s1_dti_current"),
            min_value=0.0, max_value=1.0, step=0.01,
            value=ch.get("dti_current", 0.0),
            format="%.2f",
        )

    render_section(t("section_doc"), "📎")
    st.caption(t("s1_doc_caption"))
    uploaded = st.file_uploader(
        t("s1_doc_chooser"), accept_multiple_files=True, type=["pdf", "jpg", "jpeg", "png"],
        key="upload_g1", label_visibility="collapsed",
    )
    if uploaded:
        st.session_state.uploaded_files["group1"] = [f.name for f in uploaded]
        st.success(t_pos("s1_doc_uploaded", len(uploaded)))

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


# ============================================================
# STEP 2: INCOME
# ============================================================

def render_step2_income(scorecard):
    group_cfg = scorecard['scoring_groups']['income']
    render_step_header(
        2, 6, t("s2_title"),
        t("s2_subtitle", weight=int(group_cfg['weight']*100), max=group_cfg['max_points']),
        "💼",
    )

    emp = st.session_state.applicant["employment"]
    render_section(t("s2_section"), "🏢")
    col1, col2 = st.columns(2)
    contract_options = ["permanent", "fixed_gte_12m", "fixed_lt_12m", "self_employed_licensed", "freelance"]
    salary_options = ["bank_transfer", "cash_verified", "cash_unverified"]
    ct_label_map = {
        "permanent":              t("ct_permanent"),
        "fixed_gte_12m":          t("ct_fixed_gte_12m"),
        "fixed_lt_12m":           t("ct_fixed_lt_12m"),
        "self_employed_licensed": t("ct_self_employed"),
        "freelance":              t("ct_freelance"),
    }
    sm_label_map = {
        "bank_transfer":   t("sm_bank"),
        "cash_verified":   t("sm_cash_verified"),
        "cash_unverified": t("sm_cash_unverified"),
    }
    with col1:
        emp["employer"] = st.text_input(t("s2_employer"), value=emp.get("employer", ""),
                                         placeholder=t("s2_employer_ph"))
        emp["job_title"] = st.text_input(t("s2_job_title"), value=emp.get("job_title", ""),
                                          placeholder=t("s2_job_title_ph"))
        emp["employment_contract"] = st.selectbox(
            t("s2_contract"),
            options=contract_options,
            format_func=lambda x: ct_label_map[x],
            index=contract_options.index(emp.get("employment_contract", "permanent")),
        )
    with col2:
        emp["employment_duration_months"] = st.number_input(
            t("s2_duration"),
            min_value=0, max_value=600, value=emp.get("employment_duration_months", 12),
        )
        emp["monthly_income_vnd"] = st.number_input(
            t("s2_income"),
            min_value=0, max_value=500_000_000, step=1_000_000,
            value=emp.get("monthly_income_vnd", 10_000_000),
        )
        emp["salary_method"] = st.selectbox(
            t("s2_salary_method"),
            options=salary_options,
            format_func=lambda x: sm_label_map[x],
            index=salary_options.index(emp.get("salary_method", "bank_transfer")),
        )

    render_section(t("section_doc"), "📎")
    st.caption(t("s2_doc_caption"))
    uploaded = st.file_uploader(t("s1_doc_chooser"), accept_multiple_files=True,
                                type=["pdf", "jpg", "jpeg", "png"], key="upload_g2",
                                label_visibility="collapsed")
    if uploaded:
        st.session_state.uploaded_files["group2"] = [f.name for f in uploaded]
        st.success(t_pos("s1_doc_uploaded", len(uploaded)))

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


# ============================================================
# STEP 3: PERSONAL
# ============================================================

def render_step3_personal(scorecard):
    group_cfg = scorecard['scoring_groups']['personal']
    render_step_header(
        3, 6, t("s3_title"),
        t("s2_subtitle", weight=int(group_cfg['weight']*100), max=group_cfg['max_points']),
        "👤",
    )

    p = st.session_state.applicant["personal_info"]
    render_section(t("s3_section"), "🪪")
    col1, col2 = st.columns(2)
    marital_options = ["single", "married", "divorced_widowed"]
    education_options = ["below_highschool", "highschool", "bachelor", "postgrad"]
    residency_options = ["owner", "family_home", "renting_gte_2y", "renting_lt_2y"]

    g_map = {"male": t("g_male"), "female": t("g_female"), "other": t("g_other")}
    ms_map = {"single": t("ms_single"), "married": t("ms_married"), "divorced_widowed": t("ms_divorced")}
    ed_map = {"below_highschool": t("ed_below"), "highschool": t("ed_highschool"),
              "bachelor": t("ed_bachelor"), "postgrad": t("ed_postgrad")}
    rs_map = {"owner": t("rs_owner"), "family_home": t("rs_family"),
              "renting_gte_2y": t("rs_renting_gte_2y"), "renting_lt_2y": t("rs_renting_lt_2y")}

    with col1:
        p["age"] = st.number_input(t("s3_age"), min_value=16, max_value=90,
                                    value=p.get("age", 30))
        p["gender"] = st.selectbox(
            t("s3_gender"), options=["male", "female", "other"],
            format_func=lambda x: g_map[x],
            index=["male","female","other"].index(p.get("gender", "male")),
        )
        p["marital_status"] = st.selectbox(
            t("s3_marital"), options=marital_options,
            format_func=lambda x: ms_map[x],
            index=marital_options.index(p.get("marital_status", "single")),
        )
    with col2:
        p["dependents"] = st.number_input(t("s3_dependents"), min_value=0, max_value=10,
                                          value=p.get("dependents", 0))
        p["education"] = st.selectbox(
            t("s3_education"), options=education_options,
            format_func=lambda x: ed_map[x],
            index=education_options.index(p.get("education", "bachelor")),
        )
        p["residency_status"] = st.selectbox(
            t("s3_residency"), options=residency_options,
            format_func=lambda x: rs_map[x],
            index=residency_options.index(p.get("residency_status", "family_home")),
        )

    render_section(t("section_doc"), "📎")
    st.caption(t("s3_doc_caption"))
    uploaded = st.file_uploader(t("s1_doc_chooser"), accept_multiple_files=True,
                                type=["pdf", "jpg", "jpeg", "png"], key="upload_g3",
                                label_visibility="collapsed")
    if uploaded:
        st.session_state.uploaded_files["group3"] = [f.name for f in uploaded]
        st.success(t_pos("s1_doc_uploaded", len(uploaded)))

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons()


# ============================================================
# STEP 4: ASSETS & LOAN — note: loan max = vehicle price
# ============================================================

def render_step4_assets_loan(scorecard):
    render_step_header(4, 6, t("s4_title"), t("s4_subtitle"), "💰")

    a = st.session_state.applicant["assets"]
    loan = st.session_state.applicant["loan_request"]

    render_section(t("s4_assets_section"), "🏠")
    st.caption(t("s4_assets_caption",
                 weight=int(scorecard['scoring_groups']['assets']['weight']*100),
                 max=scorecard['scoring_groups']['assets']['max_points']))

    col1, col2, col3 = st.columns(3)
    re_options = ["none", "family_shared", "owned_titled"]
    vehicle_options = ["none", "motorbike", "car"]
    re_map = {"none": t("re_none"), "family_shared": t("re_family"), "owned_titled": t("re_owned")}
    v_map = {"none": t("v_none"), "motorbike": t("v_motorbike"), "car": t("v_car")}
    with col1:
        a["real_estate"] = st.selectbox(
            t("s4_real_estate"), options=re_options,
            format_func=lambda x: re_map[x],
            index=re_options.index(a.get("real_estate", "none")),
        )
    with col2:
        a["vehicle"] = st.selectbox(
            t("s4_vehicle"), options=vehicle_options,
            format_func=lambda x: v_map[x],
            index=vehicle_options.index(a.get("vehicle", "motorbike")),
        )
    with col3:
        a["savings_vnd"] = st.number_input(
            t("s4_savings"), min_value=0,
            max_value=10_000_000_000, step=5_000_000,
            value=a.get("savings_vnd", 0),
        )

    render_section(t("s4_loan_section"), "💳")
    col1, col2 = st.columns(2)
    term_options = [6, 9, 12, 18, 24, 36]
    with col1:
        loan["vehicle_name"] = st.text_input(t("s4_vehicle_name"),
                                              value=loan.get("vehicle_name", "Honda Vision 2025"))
        loan["vehicle_price_vnd"] = st.number_input(
            t("s4_vehicle_price"), min_value=5_000_000, max_value=200_000_000, step=1_000_000,
            value=loan.get("vehicle_price_vnd", 34_000_000),
        )
        loan["down_payment_vnd"] = st.number_input(
            t("s4_down_payment"), min_value=0,
            max_value=loan.get("vehicle_price_vnd", 34_000_000), step=500_000,
            value=loan.get("down_payment_vnd", 4_000_000),
            help=t("s4_down_payment_help"),
        )
    with col2:
        loan["loan_amount_vnd"] = loan["vehicle_price_vnd"] - loan["down_payment_vnd"]
        st.markdown(f"""
        <div style="background:white; border:1px solid var(--gold); border-radius:10px;
                    padding:1rem 1.25rem; margin-bottom:1rem;
                    box-shadow:0 1px 6px rgba(201,169,97,0.10);">
            <div style="font-size:0.78rem; color:var(--text-secondary); text-transform:uppercase;
                        font-weight:600; letter-spacing:0.05em;">{t('s4_loan_amount_label')}</div>
            <div style="font-size:1.6rem; font-weight:700; color:var(--navy); margin-top:0.2rem;
                        letter-spacing:-0.02em; font-feature-settings:'tnum';">
                {loan['loan_amount_vnd']:,} VNĐ
            </div>
        </div>
        """, unsafe_allow_html=True)

        current_term = loan.get("term_months", 12)
        term_idx = term_options.index(current_term) if current_term in term_options else 2
        loan["term_months"] = st.selectbox(t("s4_term"), options=term_options, index=term_idx,
                                            format_func=lambda x: t_pos("s4_term_unit", x))

        down_ratio = loan["down_payment_vnd"] / max(loan["vehicle_price_vnd"], 1)
        if down_ratio < 0.20:
            st.warning(t("s4_down_warn", pct=down_ratio*100))
        else:
            st.success(t("s4_down_ok", pct=down_ratio*100))

    render_section(t("section_doc"), "📎")
    st.caption(t("s4_doc_caption"))
    uploaded = st.file_uploader(t("s1_doc_chooser"), accept_multiple_files=True,
                                type=["pdf", "jpg", "jpeg", "png"], key="upload_g4",
                                label_visibility="collapsed")
    if uploaded:
        st.session_state.uploaded_files["group4"] = [f.name for f in uploaded]
        st.success(t_pos("s1_doc_uploaded", len(uploaded)))

    st.markdown("<br>", unsafe_allow_html=True)
    render_nav_buttons(next_label=t("btn_run"))


# ============================================================
# STEP 5: RESULT
# ============================================================

def render_step5_result(scorecard):
    render_step_header(5, 6, t("s5_title"), "", "📋")

    pipeline = get_pipeline()
    persona_data = st.session_state.applicant.copy()
    persona_data["persona_id"] = (
        st.session_state.profile_meta.get("profile_id") or
        st.session_state.selected_persona or
        "custom_input"
    )
    decision = pipeline.evaluate(persona_data)

    render_consolidated_dashboard(decision, scorecard)

    if not decision.hard_rules_result.all_passed:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("btn_edit"), use_container_width=True, type="secondary"):
                prev_step()
                st.rerun()
        with col2:
            if st.button(t("btn_review_other"), type="primary", use_container_width=True):
                reset_state()
                st.rerun()
        return

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs([t("tab_repayment"), t("tab_rate"), t("tab_docs")])

    with tab1:
        render_repayment_with_slider(
            persona_data["loan_request"]["loan_amount_vnd"],
            decision.grade_result,
            persona_data["loan_request"]["term_months"],
            scorecard,
            persona_data["loan_request"].get("vehicle_price_vnd"),
        )

    with tab2:
        render_rate_explanation(decision.grade_result, scorecard)

    with tab3:
        render_uploaded_docs_only()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("btn_edit"), use_container_width=True, type="secondary"):
            prev_step()
            st.rerun()
    with col2:
        if st.button(t("btn_review_other"), type="primary", use_container_width=True):
            reset_state()
            st.rerun()


# ============================================================
# DASHBOARD - rebalanced (gauge bigger, bars more compact)
# ============================================================

def render_consolidated_dashboard(decision, scorecard):
    """Dashboard with prominent score gauge + compact analysis."""
    pm = st.session_state.profile_meta

    decision_map = {
        "approved_priority":    {"label": t("dec_approved_priority"), "cls": "approved", "badge_cls": "status-approved", "icon": "✓"},
        "approved":             {"label": t("dec_approved"),          "cls": "approved", "badge_cls": "status-approved", "icon": "✓"},
        "approved_conditional": {"label": t("dec_approved_cond"),     "cls": "review",   "badge_cls": "status-review",   "icon": "!"},
        "manual_review":        {"label": t("dec_manual"),            "cls": "review",   "badge_cls": "status-review",   "icon": "!"},
        "rejected":             {"label": t("dec_rejected"),          "cls": "rejected", "badge_cls": "status-rejected", "icon": "✗"},
    }
    m = decision_map.get(decision.final_decision, decision_map["rejected"])

    score_display = (str(decision.scoring_result.total_points)
                     if decision.scoring_result else "—")
    grade_display = (decision.grade_result.grade if decision.grade_result else "—")
    risk_display = (translate_risk_level(decision.grade_result.risk_level)
                    if decision.grade_result else "—")

    rate_min = getattr(decision.grade_result, "interest_rate_min", None) if decision.grade_result else None
    rate_max = getattr(decision.grade_result, "interest_rate_max", None) if decision.grade_result else None
    if rate_min and rate_max:
        rate_range = f"{rate_min*100:.0f}% – {rate_max*100:.0f}%/{t('rep_per_year').replace('%','').strip() or 'năm'}"
    elif decision.grade_result and decision.grade_result.interest_rate_annual:
        rate_range = f"{decision.grade_result.interest_rate_annual*100:.0f}%/{t('rep_per_year').replace('%','').strip() or 'năm'}"
    else:
        rate_range = "—"

    loan_req = st.session_state.applicant.get("loan_request", {})

    # === Score Hero (now more prominent) ===
    st.markdown(f"""
    <div class="score-hero {m['cls']}">
      <div class="score-hero-grid">
        <div class="gauge-block">
          <div class="gauge-number">{score_display}<span class="gauge-suffix"> / 1000</span></div>
          <div class="gauge-label">{t('score_panel_title').upper()}</div>
          <div class="gauge-grade">{t('grade_word')} {grade_display}</div>
          <div class="gauge-risk">{t('risk_word')}: <b style="color:var(--navy);">{risk_display}</b></div>
        </div>
        <div class="hero-meta">
          <div class="hero-meta-top">
            <span class="result-status-badge {m['badge_cls']}">
              {m['icon']}  {m['label']}
            </span>
            <span class="hero-customer-line">
              <b>{pm.get('full_name', '—')}</b>
              &nbsp;·&nbsp; CCCD {pm.get('cccd_number', '—')}
              &nbsp;·&nbsp; {pm.get('profile_id', '—')}
              &nbsp;·&nbsp; {pm.get('submission_date', '—')}
            </span>
          </div>
          <div class="info-grid">
            <div class="info-card">
              <div class="info-card-label">{t('hg_rate')}</div>
              <div class="info-card-value gold">{rate_range}</div>
            </div>
            <div class="info-card">
              <div class="info-card-label">{t('hg_amount')}</div>
              <div class="info-card-value">{loan_req.get('loan_amount_vnd', 0):,} VNĐ</div>
            </div>
            <div class="info-card">
              <div class="info-card-label">{t('hg_term')}</div>
              <div class="info-card-value">{t_pos('hg_term_months', loan_req.get('term_months', 0))}</div>
            </div>
            <div class="info-card">
              <div class="info-card-label">{t('hg_product')}</div>
              <div class="info-card-value info-card-product">{loan_req.get('vehicle_name', '—')}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # === Two columns: Score bars (LEFT) | Hard rules + Reason (RIGHT) ===
    # Rebalanced: gave the right column more weight so score-bars don't feel oversize
    col_left, col_right = st.columns([1, 1])

    with col_left:
        if decision.scoring_result:
            _render_score_bars(decision.scoring_result, scorecard)
        else:
            st.markdown(f"""
            <div style="background:white; border:1px solid var(--border-soft); border-radius:8px;
                        padding:1rem; text-align:center; color:var(--text-secondary); font-size:0.85rem;">
                {t('score_no_data')}
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        _render_hard_rules_panel(decision)
        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
        _render_decision_reason_panel(decision)


def _render_score_bars(scoring_result, scorecard):
    """Compact score bars — translated group names."""
    total_pct = scoring_result.ratio * 100
    st.markdown(f"""
    <div class="score-panel">
      <div class="score-panel-header">
        <div class="score-panel-title">📊 {t('score_panel_title')}</div>
        <div class="score-panel-value">
          <span class="num">{scoring_result.total_points}</span>
          <span class="sep"> / {scoring_result.max_total_points}</span>
          <span class="pct">{total_pct:.1f}%</span>
        </div>
      </div>
      <div class="progress-rail">
        <div class="progress-fill" style="background:linear-gradient(90deg, #C9A961, #E0C988); width:{total_pct}%;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    for g in scoring_result.groups:
        pct = g.ratio * 100
        if pct >= 80:
            color, label = "#0F7A5C", t("score_excellent")
        elif pct >= 65:
            color, label = "#5B8C6E", t("score_good")
        elif pct >= 50:
            color, label = "#B87300", t("score_average")
        else:
            color, label = "#B33A3A", t("score_needs_work")

        group_name = translate_group_name(g.group_key, g.group_name)

        st.markdown(f"""
        <div class="group-row">
          <div class="group-row-head">
            <div>
              <span class="group-row-name">{group_name}</span>
              <span class="group-row-weight">{g.weight*100:.0f}%</span>
            </div>
            <div class="group-row-meta">
              <span class="group-row-tag" style="background:{color};">{label}</span>
              <span class="group-row-points">{g.points}/{g.max_points}</span>
              <span class="group-row-pct" style="color:{color};">{pct:.0f}%</span>
            </div>
          </div>
          <div class="progress-rail" style="height:6px;">
            <div class="progress-fill" style="background:{color}; width:{pct}%;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander(t("score_detail_expand"), expanded=False):
        for group in scoring_result.groups:
            group_name = translate_group_name(group.group_key, group.group_name)
            st.markdown(f"""
            <div style="font-weight:600; color:var(--navy); font-size:0.85rem;
                        padding:0.4rem 0.6rem; background:var(--bg-soft); border-radius:5px;
                        margin:0.5rem 0 0.4rem 0;">
                {group_name}  ·  {group.points}/{group.max_points}  ·  {group.ratio*100:.0f}%
            </div>
            """, unsafe_allow_html=True)

            for v in group.variables:
                var_pct = (v.points / v.max_points * 100) if v.max_points > 0 else 0
                if var_pct >= 80:
                    var_color = "#0F7A5C"
                elif var_pct >= 50:
                    var_color = "#B87300"
                else:
                    var_color = "#B33A3A"

                actual_str = str(v.actual_value)
                if len(actual_str) > 28:
                    actual_str = actual_str[:25] + "..."
                actual_str = actual_str.replace("<", "&lt;").replace(">", "&gt;")

                var_name = translate_variable_name(v.variable_key, v.variable_name)

                st.markdown(f"""
                <div style="display:grid; grid-template-columns:1.5fr 1.5fr auto auto;
                            gap:0.6rem; align-items:center; padding:0.3rem 0.6rem;
                            font-size:0.78rem; border-bottom:1px solid #F0F2F5;">
                    <span style="color:var(--navy);">{var_name}</span>
                    <span style="color:var(--text-secondary); font-size:0.75rem;">{actual_str}</span>
                    <span style="color:var(--navy); font-weight:500; min-width:50px; text-align:right;">{v.points}/{v.max_points}</span>
                    <span style="color:{var_color}; font-weight:700; min-width:38px; text-align:right;">{var_pct:.0f}%</span>
                </div>
                """, unsafe_allow_html=True)


def _render_hard_rules_panel(decision):
    """Compact hard-rules panel."""
    hard_passed = sum(1 for c in decision.hard_rules_result.checks if c.passed)
    hard_total = len(decision.hard_rules_result.checks)

    if decision.hard_rules_result.all_passed:
        header_color = "#0F7A5C"
        header_text = t_pos("hr_all_pass", hard_total)
        header_bg = "#F5FBF8"
    else:
        header_color = "#B33A3A"
        n_fail = hard_total - hard_passed
        header_text = t_pos("hr_n_fail", n_fail)
        header_bg = "#FEF5F5"

    st.markdown(f"""
    <div style="background:{header_bg}; border:1px solid {header_color}33;
                border-left:3px solid {header_color}; border-radius:7px;
                padding:0.6rem 0.9rem; margin-bottom:0.45rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:600; color:var(--navy); font-size:0.92rem;">🛡️ {t('hr_panel_title')}</div>
            <div style="color:{header_color}; font-weight:700; font-size:0.92rem;
                        font-feature-settings:'tnum';">{hard_passed}/{hard_total}</div>
        </div>
        <div style="color:{header_color}; font-size:0.76rem; margin-top:0.15rem; font-weight:500;">{header_text}</div>
    </div>
    """, unsafe_allow_html=True)

    desc_map = {
        "age_min":         t("hr_age_min"),
        "age_max":         t("hr_age_max"),
        "min_income":      t("hr_min_income"),
        "min_employment": t("hr_min_employment"),
        "cic_not_bad":     t("hr_cic_not_bad"),
        "dti_max":         t("hr_dti_max"),
    }

    sorted_checks = sorted(decision.hard_rules_result.checks, key=lambda c: c.passed)

    for check in sorted_checks:
        short_desc = desc_map.get(check.rule_id, check.description)
        short_desc = short_desc.replace("<", "≤").replace(">", "≥")

        if check.passed:
            icon, color = "✓", "#0F7A5C"
            row_html = f"""
            <div style="display:flex; align-items:center; gap:0.6rem; padding:0.35rem 0.7rem;
                        background:white; border:1px solid var(--border-soft); border-radius:5px;
                        margin-bottom:0.22rem; font-size:0.78rem;">
                <span style="color:{color}; font-weight:700;">{icon}</span>
                <span style="color:var(--navy); flex-grow:1;">{short_desc}</span>
            </div>
            """
        else:
            icon, color = "✗", "#B33A3A"
            actual_human = _humanize_value(check.rule_id, check.actual_value)
            threshold_human = _humanize_threshold(check.rule_id, check.threshold)
            row_html = f"""
            <div style="background:#FEF5F5; border:1px solid {color}33; border-left:3px solid {color};
                        border-radius:5px; padding:0.4rem 0.7rem; margin-bottom:0.22rem;">
                <div style="display:flex; align-items:center; gap:0.6rem; font-size:0.78rem;">
                    <span style="color:{color}; font-weight:700;">{icon}</span>
                    <span style="color:{color}; font-weight:500; flex-grow:1;">{short_desc}</span>
                </div>
                <div style="font-size:0.7rem; color:var(--text-secondary); margin-top:0.2rem; padding-left:1.3rem;">
                    {t('hr_current')}: <b style="color:var(--navy);">{actual_human}</b>
                    &nbsp;·&nbsp; {t('hr_required')}: <b style="color:var(--navy);">{threshold_human}</b>
                </div>
            </div>
            """
        st.markdown(row_html, unsafe_allow_html=True)


def _humanize_value(rule_id, value):
    """Format actual value, language-aware."""
    if value is None:
        return t("hr_no_data")
    if rule_id in ("age_min", "age_max"):
        return t_pos("hr_age_unit", value)
    if rule_id == "min_income":
        return t_pos("hr_vnd_month", f"{int(value):,}")
    if rule_id == "min_employment":
        return t_pos("hr_month_unit", value)
    if rule_id == "cic_not_bad":
        cic_map = {
            "no_history":         t("cic_no_history"),
            "group1_all_ontime":  t("cic_group1_all_ontime"),
            "group2_once":        t("cic_group2_once"),
            "group2_multiple":    t("cic_group2_multiple"),
            "group3":             t("cic_group3"),
            "group4":             t("cic_group4"),
            "group5":             t("cic_group5"),
        }
        return cic_map.get(value, str(value))
    if rule_id == "dti_max":
        try:
            return f"{float(value)*100:.1f}%"
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _humanize_threshold(rule_id, threshold):
    """Format threshold, language-aware."""
    threshold_str = str(threshold)
    if rule_id == "age_min":         return t("hr_thr_age_min")
    if rule_id == "age_max":         return t("hr_thr_age_max")
    if rule_id == "min_income":      return t("hr_thr_min_income")
    if rule_id == "min_employment": return t("hr_thr_min_employment")
    if rule_id == "cic_not_bad":     return t("hr_thr_cic")
    if rule_id == "dti_max":         return t("hr_thr_dti")
    return threshold_str.replace("<", "≤").replace(">", "≥")


def _render_decision_reason_panel(decision):
    """Decision reason panel."""
    reason_map = {
        "approved_priority":    t("reason_approved_priority"),
        "approved":             t("reason_approved"),
        "approved_conditional": t("reason_approved_cond"),
        "manual_review":        t("reason_manual"),
        "rejected":             t("reason_rejected"),
    }
    next_map = {
        "approved_priority":    t("next_approved_priority"),
        "approved":             t("next_approved"),
        "approved_conditional": t("next_manual"),
        "manual_review":        t("next_manual"),
        "rejected":             t("next_rejected"),
    }
    reason_text = reason_map.get(decision.final_decision, "—")
    next_step_text = next_map.get(decision.final_decision, "—")

    st.markdown(f"""
    <div style="background:white; border:1px solid var(--border-soft); border-radius:7px;
                padding:0.7rem 0.9rem;">
        <div style="font-weight:600; color:var(--navy); font-size:0.92rem;
                    padding-bottom:0.45rem; margin-bottom:0.45rem;
                    border-bottom:1px solid var(--border-soft);">💡 {t('reason_panel_title')}</div>
        <div style="font-size:0.8rem; color:var(--text-secondary); line-height:1.55;
                    margin-bottom:0.55rem;">
            {reason_text}
        </div>
        <div style="background:var(--bg-cream); border-left:3px solid var(--gold);
                    border-radius:4px; padding:0.45rem 0.7rem;">
            <div style="font-size:0.65rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:600;">{t('next_step_label')}</div>
            <div style="font-size:0.78rem; color:var(--navy); line-height:1.45; margin-top:0.15rem;">
                {next_step_text}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_uploaded_docs_only():
    """Documents tab."""
    st.markdown(f"#### {t('docs_title')}")
    total = 0
    for group_key, label, icon in [
        ("group1", t("docs_g1"), "📊"),
        ("group2", t("docs_g2"), "💼"),
        ("group3", t("docs_g3"), "👤"),
        ("group4", t("docs_g4"), "🏠"),
    ]:
        files = st.session_state.uploaded_files.get(group_key, [])
        with st.expander(f"{icon}  {label}  ·  {t_pos('docs_count', len(files))}"):
            if files:
                for f in files:
                    safe_name = f.replace("<", "&lt;").replace(">", "&gt;")
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:0.6rem;
                                padding:0.4rem 0.6rem; background:var(--bg-soft);
                                border-radius:4px; margin-bottom:0.25rem;
                                font-size:0.85rem;">
                        <span>📄</span>
                        <span style="color:var(--navy);">{safe_name}</span>
                    </div>
                    """, unsafe_allow_html=True)
                total += len(files)
            else:
                st.caption(t("docs_none"))

    st.markdown(f"""
    <div style="background:white; border:1px solid var(--border-soft); border-radius:8px;
                padding:0.85rem 1.25rem; margin-top:0.75rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:var(--text-secondary); font-size:0.85rem;">{t('docs_total')}</span>
            <span style="color:var(--gold-deep); font-weight:700; font-size:1.2rem;
                         font-feature-settings:'tnum';">{total}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# REPAYMENT SLIDER — loan amount slider max = vehicle price
# ============================================================

def render_repayment_with_slider(loan_amount, grade_result, term_months, scorecard, vehicle_price=None):
    if not grade_result or grade_result.interest_rate_annual is None:
        st.info(t("rep_rejected_info"))
        return

    rate_min = getattr(grade_result, "interest_rate_min", None)
    rate_max = getattr(grade_result, "interest_rate_max", None)
    if rate_min is None or rate_max is None:
        base_rate = grade_result.interest_rate_annual
        rate_min = max(0.0, base_rate - 0.02)
        rate_max = base_rate + 0.02

    if st.session_state.selected_rate is None:
        st.session_state.selected_rate = grade_result.interest_rate_annual
    if "calc_loan_amount" not in st.session_state:
        st.session_state.calc_loan_amount = loan_amount
    if "calc_term_months" not in st.session_state:
        st.session_state.calc_term_months = term_months

    if (st.session_state.selected_rate < rate_min or
        st.session_state.selected_rate > rate_max):
        st.session_state.selected_rate = grade_result.interest_rate_annual

    # Header
    st.markdown(f"""
    <div style="display:flex; align-items:flex-end; gap:0.6rem; margin-bottom:0.5rem;">
        <h3 style="margin:0; color:var(--navy); font-weight:600; font-size:1.15rem;">
            {t('rep_title')}
        </h3>
        <span style="color:var(--text-secondary); font-size:0.82rem; padding-bottom:0.2rem;">
            {t('rep_grade_label')} <b style="color:var(--gold-deep);">{grade_result.grade}</b> ·
            {t('rep_rate_range', min=rate_min*100, max=rate_max*100)}
        </span>
    </div>
    <div style="height:3px; width:60px; background:linear-gradient(90deg, #C9A961, #E0C988);
                border-radius:2px; margin-bottom:1rem;"></div>
    """, unsafe_allow_html=True)

    col_sliders, col_payment = st.columns([3, 2])

    with col_sliders:
        # Slider 1: Rate
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:baseline;
                    margin-bottom:0.25rem;">
            <span style="font-size:0.88rem; font-weight:600; color:var(--navy);">{t('rep_applied_rate')}</span>
            <span style="font-size:1.1rem; font-weight:700; color:var(--gold-deep);">
                {st.session_state.selected_rate*100:.1f}<span style="font-size:0.8rem; font-weight:500;">{t('rep_per_year')}</span>
            </span>
        </div>
        """, unsafe_allow_html=True)
        new_rate = st.slider(
            "rate",
            min_value=float(rate_min * 100),
            max_value=float(rate_max * 100),
            value=float(st.session_state.selected_rate * 100),
            step=0.1,
            format="%.1f%%",
            key="rate_slider",
            label_visibility="collapsed",
        )
        st.session_state.selected_rate = new_rate / 100

        # Slider 2: Loan amount — MAX is vehicle_price (giá xe)
        max_label = ""
        if vehicle_price:
            amount_max = int(vehicle_price)
            max_label = f' &nbsp;<span style="color:var(--gold-deep); font-size:0.7rem; font-weight:500;">({t("rep_max_eq_price")}: {amount_max:,} VNĐ)</span>'
        else:
            amount_max = min(200_000_000, int(loan_amount * 2))

        # Floor — sensible minimum
        amount_min = min(5_000_000, max(1_000_000, int(loan_amount * 0.5)))
        # Make sure step doesn't break sliders
        if amount_max <= amount_min:
            amount_max = amount_min + 1_000_000

        # Clamp current value
        if st.session_state.calc_loan_amount > amount_max:
            st.session_state.calc_loan_amount = amount_max
        if st.session_state.calc_loan_amount < amount_min:
            st.session_state.calc_loan_amount = amount_min

        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:baseline;
                    margin-top:0.5rem; margin-bottom:0.25rem;">
            <span style="font-size:0.88rem; font-weight:600; color:var(--navy);">{t('rep_loan_amount')}{max_label}</span>
            <span style="font-size:1.1rem; font-weight:700; color:var(--gold-deep);">
                {st.session_state.calc_loan_amount:,.0f}<span style="font-size:0.8rem; font-weight:500;"> VNĐ</span>
            </span>
        </div>
        """, unsafe_allow_html=True)
        new_amount = st.slider(
            "amount",
            min_value=int(amount_min),
            max_value=int(amount_max),
            value=int(st.session_state.calc_loan_amount),
            step=1_000_000,
            format="%d",
            key="amount_slider",
            label_visibility="collapsed",
        )
        st.session_state.calc_loan_amount = new_amount

        # Slider 3: Term
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:baseline;
                    margin-top:0.5rem; margin-bottom:0.25rem;">
            <span style="font-size:0.88rem; font-weight:600; color:var(--navy);">{t('rep_term')}</span>
            <span style="font-size:1.1rem; font-weight:700; color:var(--gold-deep);">
                {st.session_state.calc_term_months}<span style="font-size:0.8rem; font-weight:500;"> {t('rep_months')}</span>
            </span>
        </div>
        """, unsafe_allow_html=True)
        term_format = "%d " + t("rep_months")
        new_term = st.slider(
            "term",
            min_value=6,
            max_value=36,
            value=int(st.session_state.calc_term_months),
            step=3,
            format=term_format,
            key="term_slider",
            label_visibility="collapsed",
        )
        st.session_state.calc_term_months = new_term

    annual_rate = st.session_state.selected_rate
    current_loan = st.session_state.calc_loan_amount
    current_term = st.session_state.calc_term_months
    plans = cached_calculate_both_plans(current_loan, annual_rate, current_term)
    p1 = plans["plan_1_annuity"]
    p2 = plans["plan_2_equal_principal"]

    with col_payment:
        monthly_pmt = p1.payments[0].total_payment

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, var(--bg-cream) 0%, #FFFFFF 100%);
                    border:1.5px solid var(--gold); border-radius:10px;
                    padding:1.1rem 1.25rem; height:100%;
                    box-shadow:0 2px 10px rgba(201,169,97,0.14);">
            <div style="font-size:0.78rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.06em; font-weight:600;">{t('rep_monthly_label')}</div>
            <div style="text-align:center; padding:0.75rem 0;">
                <span style="font-size:2.05rem; font-weight:800; color:var(--gold-deep);
                             letter-spacing:-0.02em; line-height:1; font-feature-settings:'tnum';">
                    {monthly_pmt:,.0f}
                </span>
                <span style="font-size:0.95rem; color:var(--text-secondary); margin-left:0.3rem;">VNĐ</span>
            </div>
            <div style="background:var(--bg-soft); border-radius:6px; padding:0.5rem 0.75rem;
                        font-size:0.78rem; color:var(--text-secondary); line-height:1.5;">
                <div style="display:flex; justify-content:space-between; padding:0.15rem 0;">
                    <span>{t('rep_total_interest')}</span>
                    <span style="color:var(--navy); font-weight:600; font-feature-settings:'tnum';">{p1.total_interest:,.0f} VNĐ</span>
                </div>
                <div style="display:flex; justify-content:space-between; padding:0.15rem 0;
                            border-top:1px dashed var(--border-soft); margin-top:0.25rem; padding-top:0.35rem;">
                    <span>{t('rep_total_paid')}</span>
                    <span style="color:var(--navy); font-weight:600; font-feature-settings:'tnum';">{p1.total_paid:,.0f} VNĐ</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:0.75rem; padding:0.6rem 0.85rem; background:var(--bg-soft);
                border-left:3px solid var(--text-secondary); border-radius:4px;
                font-size:0.78rem; color:var(--text-secondary); font-style:italic; line-height:1.5;">
        {t('rep_note')}
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1.2rem;"></div>', unsafe_allow_html=True)

    # 3 metric cards
    saving = p1.total_interest - p2.total_interest
    saving_pct = (saving / p1.total_interest * 100) if p1.total_interest > 0 else 0
    p2_first = p2.payments[0].total_payment
    p2_last = p2.payments[-1].total_payment

    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
        <div style="background:white; border:1px solid var(--border-soft); border-left:3px solid var(--navy);
                    border-radius:8px; padding:0.85rem 1rem;">
            <div style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:600;">{t('rep_pa1_title')}</div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.2rem;">{t('rep_pa1_desc')}</div>
            <div style="font-size:1.1rem; font-weight:700; color:var(--navy); margin-top:0.3rem;
                        font-feature-settings:'tnum';">
                {monthly_pmt:,.0f} VNĐ
            </div>
            <div style="font-size:0.72rem; color:var(--text-secondary); margin-top:0.15rem;">
                {t('rep_total_int_short')} <b style="color:var(--navy); font-feature-settings:'tnum';">{p1.total_interest:,.0f} VNĐ</b>
            </div>
        </div>
        <div style="background:white; border:1px solid var(--border-soft); border-left:3px solid var(--gold);
                    border-radius:8px; padding:0.85rem 1rem;">
            <div style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:600;">{t('rep_pa2_title')}</div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.2rem;">{t('rep_pa2_desc')}</div>
            <div style="font-size:1.1rem; font-weight:700; color:var(--navy); margin-top:0.3rem;
                        font-feature-settings:'tnum';">
                {p2_first:,.0f} → {p2_last:,.0f}
            </div>
            <div style="font-size:0.72rem; color:var(--text-secondary); margin-top:0.15rem;">
                {t('rep_total_int_short')} <b style="color:#0F7A5C; font-feature-settings:'tnum';">{p2.total_interest:,.0f} VNĐ</b>
            </div>
        </div>
        <div style="background:linear-gradient(135deg, #F5FBF8 0%, #FFFFFF 100%);
                    border:1px solid #0F7A5C33; border-left:3px solid #0F7A5C;
                    border-radius:8px; padding:0.85rem 1rem;">
            <div style="font-size:0.7rem; color:var(--text-secondary); text-transform:uppercase;
                        letter-spacing:0.05em; font-weight:600;">{t('rep_pa2_savings')}</div>
            <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.2rem;">{t('rep_pa2_savings_desc')}</div>
            <div style="font-size:1.1rem; font-weight:700; color:#0F7A5C; margin-top:0.3rem;
                        font-feature-settings:'tnum';">
                {saving:,.0f} VNĐ
            </div>
            <div style="font-size:0.72rem; color:var(--text-secondary); margin-top:0.15rem;">
                {t_pos('rep_pa2_savings_eq', saving_pct)}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_chart, tab_p1, tab_p2, tab_download = st.tabs([
        t("rep_tab_chart"), t("rep_tab_p1"), t("rep_tab_p2"), t("rep_tab_dl"),
    ])

    with tab_chart:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                f'<div style="font-weight:600; color:var(--navy); font-size:0.9rem; margin-bottom:0.4rem;">'
                f'{t("rep_chart_cashflow")}</div>',
                unsafe_allow_html=True,
            )
            cashflow_df = pd.DataFrame({
                t("rep_period"): [p.period for p in p1.payments],
                t("rep_p1_legend"): [p.total_payment for p in p1.payments],
                t("rep_p2_legend"): [p.total_payment for p in p2.payments],
            }).set_index(t("rep_period"))
            st.line_chart(cashflow_df, height=240, color=["#0A2540", "#C9A961"])
        with col_b:
            st.markdown(
                f'<div style="font-weight:600; color:var(--navy); font-size:0.9rem; margin-bottom:0.4rem;">'
                f'{t("rep_chart_balance")}</div>',
                unsafe_allow_html=True,
            )
            balance_df = pd.DataFrame({
                t("rep_period"): [p.period for p in p1.payments],
                t("rep_p1_legend"): [p.closing_balance for p in p1.payments],
                t("rep_p2_legend"): [p.closing_balance for p in p2.payments],
            }).set_index(t("rep_period"))
            st.area_chart(balance_df, height=240, color=["#0A2540", "#C9A961"])

    with tab_p1:
        df1 = schedule_to_df(p1)
        st.dataframe(df1, use_container_width=True, hide_index=True, height=380)

    with tab_p2:
        df2 = schedule_to_df(p2)
        st.dataframe(df2, use_container_width=True, hide_index=True, height=380)

    with tab_download:
        st.markdown(
            f'<p style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.75rem;">'
            f'{t("rep_dl_intro")}</p>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            df1 = schedule_to_df(p1)
            excel_bytes = export_to_excel(p1, p2, current_loan, annual_rate, current_term)
            st.download_button(
                t("rep_dl_excel"),
                data=excel_bytes,
                file_name=f"loan_schedule_{current_loan//1_000_000}M_{current_term}m_{annual_rate*100:.0f}pct.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            csv1 = df1.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                t("rep_dl_csv"),
                data=csv1,
                file_name=f"plan1_annuity_{current_loan//1_000_000}M.csv",
                mime="text/csv",
                use_container_width=True,
            )


# ============================================================
# RATE EXPLANATION
# ============================================================

def render_rate_explanation(grade_result, scorecard):
    if not grade_result or grade_result.interest_rate_annual is None:
        st.info(t("rate_rejected_info"))
        return

    components = scorecard["scoring_system"].get("interest_rate_components")
    if not components:
        st.warning(
            "⚠️ scorecard.json is missing `interest_rate_components`. "
            "Please push the latest file to the repo and wait for redeploy."
        )
        return

    risk_premium = getattr(grade_result, "risk_premium", None)
    if risk_premium is None:
        st.warning(
            "⚠️ engine/scoring_engine.py is missing `risk_premium`. "
            "Please push the latest file to the repo and wait for redeploy."
        )
        return

    selected_rate = st.session_state.selected_rate or grade_result.interest_rate_annual

    st.markdown(f"#### {t('rate_explain_title')}")
    st.markdown(f"""
    <p style="color:var(--text-secondary); font-size:0.9rem;">
    {t('rate_explain_intro')}
    </p>
    """, unsafe_allow_html=True)

    total_avg = (components['policy_rate'] + components['cost_of_fund'] + risk_premium + components['service_fee']) * 100

    st.markdown(f"""
    <div class="rate-explain-card">
        <div style="font-weight:600; color:var(--navy); font-size:1rem; margin-bottom:0.5rem;">
            {t('rate_formula_title')}
        </div>
        <div class="rate-formula">
            {t('rate_formula')}
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
                <span class="label">{t('rate_risk_premium', grade=grade_result.grade, risk=translate_risk_level(grade_result.risk_level))}</span>
                <span class="value">+ {risk_premium*100:.2f}%</span>
            </div>
            <div class="rate-component">
                <span class="label">{components['service_fee_label']}</span>
                <span class="value">+ {components['service_fee']*100:.2f}%</span>
            </div>
            <div class="rate-component">
                <span class="label">{t('rate_total_label')}</span>
                <span class="value">{total_avg:.2f}{t('rate_per_year')}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:white; border:1px solid var(--border-soft); border-radius:10px;
                padding:1.25rem 1.5rem; margin-top:1rem;">
        <div style="font-weight:600; color:var(--navy); margin-bottom:0.6rem;">
            {t('rate_explain_card')}
        </div>
        <div style="font-size:0.88rem; color:var(--text-secondary); line-height:1.7;">
            <p>{t('rate_exp_1', rate=f"{components['policy_rate']*100:.1f}", src=components['policy_rate_source'])}</p>
            <p>{t('rate_exp_2', rate=f"{components['cost_of_fund']*100:.1f}")}</p>
            <p>{t('rate_exp_3', rate=f"{risk_premium*100:.1f}", grade=grade_result.grade)}</p>
            <p>{t('rate_exp_4', rate=f"{components['service_fee']*100:.1f}")}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### {t('rate_ref_title')}")

    ref_data = []
    for tier in scorecard["scoring_system"]["grade_thresholds"]:
        if tier["interest_rate_annual"] is None:
            continue
        is_current = tier["grade"] == grade_result.grade
        rmin = tier.get("interest_rate_min", tier["interest_rate_annual"] - 0.02)
        rmax = tier.get("interest_rate_max", tier["interest_rate_annual"] + 0.02)
        rprem = tier.get("risk_premium", 0)
        ref_data.append({
            t("rate_ref_grade"):    ("👉 " if is_current else "") + tier["grade"],
            t("rate_ref_minscore"): tier["min_score"],
            t("rate_ref_risk"):     translate_risk_level(tier["risk_level"]),
            t("rate_ref_premium"):  f"{rprem*100:.1f}%",
            t("rate_ref_range"):    f"{rmin*100:.1f}% - {rmax*100:.1f}%",
            t("rate_ref_avg"):      f"{tier['interest_rate_annual']*100:.1f}%",
        })
    df_ref = pd.DataFrame(ref_data)
    st.dataframe(df_ref, use_container_width=True, hide_index=True)

    st.caption(t("rate_caption", grade=grade_result.grade, rate=selected_rate*100))


# ============================================================
# UTILS
# ============================================================

def schedule_to_df(schedule):
    return pd.DataFrame([
        {t("rep_period"):       p.period,
         t("rep_df_opening"):   f"{p.opening_balance:,.0f}",
         t("rep_df_principal"): f"{p.principal:,.0f}",
         t("rep_df_interest"):  f"{p.interest:,.0f}",
         t("rep_df_total"):     f"{p.total_payment:,.0f}",
         t("rep_df_closing"):   f"{p.closing_balance:,.0f}"}
        for p in schedule.payments
    ])


def export_to_excel(p1, p2, loan_amount, annual_rate, term_months):
    output = BytesIO()
    is_en = st.session_state.get("language", "vi") == "en"
    sheet_summary = "Summary" if is_en else "Tổng hợp"
    sheet_p1 = "Plan 1 - Annuity" if is_en else "PA1 - Niên kim"
    sheet_p2 = "Plan 2 - Equal principal" if is_en else "PA2 - Gốc đều"
    col_metric = "Metric" if is_en else "Thông số"
    col_value = "Value" if is_en else "Giá trị"
    col_period = t("rep_period")
    col_opening = t("rep_df_opening")
    col_principal = t("rep_df_principal")
    col_interest = t("rep_df_interest")
    col_total = t("rep_df_total")
    col_closing = t("rep_df_closing")

    def lbl(en, vi): return en if is_en else vi

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_rows = [
            (lbl("Loan amount", "Số tiền vay"),               f"{loan_amount:,.0f} VNĐ"),
            (lbl("Annual rate", "Lãi suất/năm"),               f"{annual_rate*100:.1f}%"),
            (lbl("Term", "Kỳ hạn"),                             f"{term_months} {t('rep_months')}"),
            (lbl("Plan 1 - Total interest", "PA1 - Tổng lãi"), f"{p1.total_interest:,.0f} VNĐ"),
            (lbl("Plan 1 - Total payable", "PA1 - Tổng phải trả"), f"{p1.total_paid:,.0f} VNĐ"),
            (lbl("Plan 2 - Total interest", "PA2 - Tổng lãi"), f"{p2.total_interest:,.0f} VNĐ"),
            (lbl("Plan 2 - Total payable", "PA2 - Tổng phải trả"), f"{p2.total_paid:,.0f} VNĐ"),
            (lbl("Plan 2 saves vs Plan 1", "PA2 tiết kiệm so với PA1"),
             f"{p1.total_interest - p2.total_interest:,.0f} VNĐ"),
        ]
        summary = pd.DataFrame(summary_rows, columns=[col_metric, col_value])
        summary.to_excel(writer, sheet_name=sheet_summary, index=False)

        df1 = pd.DataFrame([
            {col_period: p.period, col_opening: p.opening_balance,
             col_principal: p.principal, col_interest: p.interest,
             col_total: p.total_payment, col_closing: p.closing_balance}
            for p in p1.payments])
        df1.to_excel(writer, sheet_name=sheet_p1, index=False)

        df2 = pd.DataFrame([
            {col_period: p.period, col_opening: p.opening_balance,
             col_principal: p.principal, col_interest: p.interest,
             col_total: p.total_payment, col_closing: p.closing_balance}
            for p in p2.payments])
        df2.to_excel(writer, sheet_name=sheet_p2, index=False)
    output.seek(0)
    return output.getvalue()


# ============================================================
# MAIN ROUTER
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
        render_step_init_profile()
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
