"""
Demo script: chạy hệ thống xét duyệt cho 3 persona và in kết quả đầy đủ.

Usage:
    python main.py
"""

import json
from pathlib import Path

from engine import CreditScoringPipeline, calculate_both_plans


# ============================================================
# PRINTING HELPERS
# ============================================================

def hr(char="=", width=80):
    print(char * width)


def fmt_vnd(amount: float) -> str:
    """Format số tiền VNĐ có dấu phẩy ngăn cách."""
    return f"{amount:>15,.0f} VNĐ"


def print_hard_rules(result):
    hr("-")
    print("BƯỚC 1: KIỂM TRA HARD RULES (điều kiện loại trực tiếp)")
    hr("-")
    for check in result.checks:
        icon = "[PASS]" if check.passed else "[FAIL]"
        print(f"  {icon} {check.description}")
        print(f"         Giá trị thực tế: {check.actual_value}  |  Ngưỡng: {check.threshold}")
    print()
    status = "PASS - Chuyển sang chấm điểm" if result.all_passed else "FAIL - Từ chối ngay"
    print(f"  => KẾT LUẬN: {status}")


def print_scoring(scoring_result):
    hr("-")
    print("BƯỚC 2: CHẤM ĐIỂM SCORECARD 4 NHÓM")
    hr("-")

    for group in scoring_result.groups:
        print(f"\n  Nhóm: {group.group_name} (trọng số {group.weight*100:.0f}%)")
        print(f"  {'Biến':<40}{'Giá trị':<25}{'Điểm':>8}{'Tối đa':>10}")
        print(f"  {'-'*83}")
        for var in group.variables:
            val_str = str(var.actual_value)[:22]
            print(f"  {var.variable_name:<40}{val_str:<25}{var.points:>8}{var.max_points:>10}")
        print(f"  {'TỔNG NHÓM':<40}{'':25}{group.points:>8}{group.max_points:>10}  ({group.ratio*100:.1f}%)")

    print()
    hr("-")
    print(f"  TỔNG ĐIỂM: {scoring_result.total_points} / {scoring_result.max_total_points}  ({scoring_result.ratio*100:.1f}%)")


def print_grade(grade_result):
    hr("-")
    print("BƯỚC 3: XẾP HẠNG TÍN DỤNG")
    hr("-")
    decision_map = {
        "approved_priority": "DUYỆT ƯU TIÊN",
        "approved": "DUYỆT",
        "approved_conditional": "DUYỆT CÓ ĐIỀU KIỆN",
        "manual_review": "XEM XÉT THỦ CÔNG",
        "rejected": "TỪ CHỐI",
    }
    print(f"  Hạng:              {grade_result.grade}")
    print(f"  Mức rủi ro:        {grade_result.risk_level}")
    print(f"  Quyết định:        {decision_map.get(grade_result.decision, grade_result.decision)}")
    if grade_result.interest_rate_annual is not None:
        print(f"  Lãi suất đề xuất:  {grade_result.interest_rate_annual*100:.1f}%/năm")


def print_repayment_plan(schedule, show_all_periods=False):
    print(f"\n  >>> {schedule.plan_name}")
    print(f"      Số tiền vay: {fmt_vnd(schedule.principal_amount)}")
    print(f"      Lãi suất:    {schedule.annual_rate*100:.1f}%/năm  |  Kỳ hạn: {schedule.term_months} tháng")
    print()
    print(f"      {'Kỳ':>4}{'Dư nợ đầu kỳ':>18}{'Gốc':>14}{'Lãi':>14}{'Tổng trả':>15}{'Dư nợ cuối':>18}")
    print(f"      {'-'*83}")

    # Hiển thị 3 kỳ đầu + 2 kỳ cuối cho gọn
    payments = schedule.payments
    if show_all_periods or len(payments) <= 8:
        rows_to_show = list(enumerate(payments))
    else:
        rows_to_show = list(enumerate(payments[:3]))
        rows_to_show.append((None, None))  # separator
        rows_to_show += [(i, p) for i, p in enumerate(payments[-2:], start=len(payments)-2)]

    for idx, p in rows_to_show:
        if p is None:
            print(f"      {'...':>4}{'...':>18}{'...':>14}{'...':>14}{'...':>15}{'...':>18}")
            continue
        print(f"      {p.period:>4}{p.opening_balance:>18,.0f}{p.principal:>14,.0f}"
              f"{p.interest:>14,.0f}{p.total_payment:>15,.0f}{p.closing_balance:>18,.0f}")

    print(f"      {'-'*83}")
    print(f"      Tổng lãi:           {schedule.total_interest:>15,.0f} VNĐ")
    print(f"      Tổng phải trả:      {schedule.total_paid:>15,.0f} VNĐ")


def print_comparison(plans):
    print(f"\n  >>> SO SÁNH 2 PHƯƠNG ÁN")
    p1 = plans["plan_1_annuity"]
    p2 = plans["plan_2_equal_principal"]
    saving = p1.total_interest - p2.total_interest
    print(f"      Tổng lãi PA1 (niên kim):     {p1.total_interest:>15,.0f} VNĐ")
    print(f"      Tổng lãi PA2 (gốc đều):      {p2.total_interest:>15,.0f} VNĐ")
    print(f"      Chênh lệch (PA2 tiết kiệm):  {saving:>15,.0f} VNĐ")
    print(f"\n      Nhận xét:")
    print(f"      - PA1 trả đều, dòng tiền ổn định, phù hợp khách có thu nhập cố định")
    print(f"      - PA2 trả giảm dần, tổng lãi thấp hơn {saving:,.0f} VNĐ, phù hợp khách muốn tiết kiệm lãi")


# ============================================================
# MAIN
# ============================================================

def evaluate_persona(pipeline, persona, scorecard):
    hr("=")
    print(f"HỒ SƠ: {persona['persona_id']}")
    print(f"Tên: {persona['full_name_censored']}  |  {persona['description']}")
    print(f"Dự kiến: {persona['expected_result']}")
    print(f"Xe muốn mua: {persona['loan_request']['vehicle_name']}  "
          f"|  Vay {persona['loan_request']['loan_amount_vnd']:,} VNĐ  "
          f"|  {persona['loan_request']['term_months']} tháng")
    hr("=")

    # Chạy pipeline
    decision = pipeline.evaluate(persona)

    # In từng bước
    print_hard_rules(decision.hard_rules_result)

    if not decision.hard_rules_result.all_passed:
        print()
        hr("!")
        print("KẾT QUẢ CUỐI CÙNG: TỪ CHỐI (do vi phạm hard rules)")
        hr("!")
        print("Lý do từ chối:")
        for reason in decision.rejection_reasons:
            print(f"  - {reason}")
        print()
        return

    print()
    print_scoring(decision.scoring_result)
    print()
    print_grade(decision.grade_result)

    # Nếu pass, tính phương án trả nợ
    if decision.grade_result.decision != "rejected" and decision.grade_result.interest_rate_annual:
        print()
        hr("-")
        print("BƯỚC 4: HAI PHƯƠNG ÁN TRẢ NỢ")
        hr("-")
        loan_amount = persona["loan_request"]["loan_amount_vnd"]
        term = persona["loan_request"]["term_months"]
        rate = decision.grade_result.interest_rate_annual
        plans = calculate_both_plans(loan_amount, rate, term)
        print_repayment_plan(plans["plan_1_annuity"])
        print_repayment_plan(plans["plan_2_equal_principal"])
        print_comparison(plans)

    print()


def main():
    base_dir = Path(__file__).parent
    scorecard_path = base_dir / "data" / "scorecard.json"
    personas_path = base_dir / "data" / "personas.json"

    # Load data
    with open(scorecard_path, encoding="utf-8") as f:
        scorecard = json.load(f)
    with open(personas_path, encoding="utf-8") as f:
        personas_data = json.load(f)

    pipeline = CreditScoringPipeline(str(scorecard_path))

    hr("#")
    print("#" + " "*78 + "#")
    print("#" + "HỆ THỐNG XÉT DUYỆT HỒ SƠ VAY TIÊU DÙNG - DEMO 3 PERSONA".center(78) + "#")
    print("#" + f"Sản phẩm: {scorecard['product']['name']}".center(78) + "#")
    print("#" + " "*78 + "#")
    hr("#")

    for persona in personas_data["personas"]:
        evaluate_persona(pipeline, persona, scorecard)


if __name__ == "__main__":
    main()
