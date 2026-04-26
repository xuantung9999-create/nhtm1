"""
Unit tests cho scoring engine và repayment calculator.
Chạy: python -m pytest tests/test_scoring.py -v
Hoặc:  python tests/test_scoring.py
"""

import json
import sys
from pathlib import Path

# Cho phép import từ thư mục cha
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine import (
    CreditScoringPipeline,
    calculate_annuity,
    calculate_equal_principal,
)


SCORECARD_PATH = Path(__file__).parent.parent / "data" / "scorecard.json"
PERSONAS_PATH = Path(__file__).parent.parent / "data" / "personas.json"


def load_persona(persona_id):
    with open(PERSONAS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for p in data["personas"]:
        if p["persona_id"] == persona_id:
            return p
    raise ValueError(f"Persona not found: {persona_id}")


# ==========================================
# SCORING TESTS
# ==========================================

def test_persona_A_approved_priority():
    """Persona A là hồ sơ ideal, phải được hạng AA."""
    pipeline = CreditScoringPipeline(str(SCORECARD_PATH))
    persona = load_persona("A_NguyenVanAn")
    decision = pipeline.evaluate(persona)

    assert decision.hard_rules_result.all_passed, "A phải pass hard rules"
    assert decision.scoring_result.total_points >= 800, \
        f"A phải có điểm >= 800, got {decision.scoring_result.total_points}"
    assert decision.grade_result.grade == "AA"
    assert decision.final_decision == "approved_priority"
    print(f"  [OK] Persona A: {decision.scoring_result.total_points} điểm, hạng AA")


def test_persona_B_manual_review():
    """Persona B borderline, phải rơi vào hạng BB (xem xét thủ công) hoặc BBB."""
    pipeline = CreditScoringPipeline(str(SCORECARD_PATH))
    persona = load_persona("B_TranThiBinh")
    decision = pipeline.evaluate(persona)

    assert decision.hard_rules_result.all_passed, "B phải pass hard rules"
    assert 500 <= decision.scoring_result.total_points < 700, \
        f"B phải có điểm trong [500, 700), got {decision.scoring_result.total_points}"
    assert decision.grade_result.grade in ("BB", "BBB")
    print(f"  [OK] Persona B: {decision.scoring_result.total_points} điểm, hạng {decision.grade_result.grade}")


def test_persona_C_rejected():
    """Persona C phải bị từ chối do hard rules (CIC nhóm 3)."""
    pipeline = CreditScoringPipeline(str(SCORECARD_PATH))
    persona = load_persona("C_LeVanCuong")
    decision = pipeline.evaluate(persona)

    assert not decision.hard_rules_result.all_passed, "C phải fail hard rules"
    assert decision.final_decision == "rejected"
    assert len(decision.rejection_reasons) > 0
    # C phải fail ít nhất rule CIC
    failed_ids = [c.rule_id for c in decision.hard_rules_result.failed_rules]
    assert "cic_not_bad" in failed_ids, f"C phải fail cic_not_bad, failed: {failed_ids}"
    print(f"  [OK] Persona C: rejected, fail rules = {failed_ids}")


# ==========================================
# REPAYMENT CALCULATOR TESTS
# ==========================================

def test_annuity_basic():
    """Test PMT với ví dụ số đơn giản có thể tính tay."""
    # P=100tr, 12%/năm, 12 tháng
    # monthly_rate = 1%
    # A = 100_000_000 * 0.01 * 1.01^12 / (1.01^12 - 1) ≈ 8,884,879
    schedule = calculate_annuity(100_000_000, 0.12, 12)

    assert len(schedule.payments) == 12
    # Payment đầu tiên xấp xỉ 8.88tr
    assert 8_800_000 <= schedule.payments[0].total_payment <= 8_900_000
    # Các kỳ (trừ kỳ cuối) phải gần bằng nhau
    first_pmt = schedule.payments[0].total_payment
    for p in schedule.payments[:-1]:
        assert abs(p.total_payment - first_pmt) < 2  # sai số làm tròn
    # Dư nợ cuối kỳ cuối = 0
    assert schedule.payments[-1].closing_balance == 0
    print(f"  [OK] Annuity 100tr/12%/12m: PMT ≈ {first_pmt:,.0f}, "
          f"tổng lãi = {schedule.total_interest:,.0f}")


def test_equal_principal_basic():
    """Test gốc đều: gốc mỗi kỳ = P/n, lãi giảm dần."""
    schedule = calculate_equal_principal(100_000_000, 0.12, 12)

    assert len(schedule.payments) == 12
    # Gốc mỗi kỳ ≈ 100tr/12 = 8,333,333
    for p in schedule.payments[:-1]:  # trừ kỳ cuối do điều chỉnh làm tròn
        assert abs(p.principal - 8_333_333) < 2
    # Lãi kỳ 1 > lãi kỳ cuối
    assert schedule.payments[0].interest > schedule.payments[-1].interest
    # Tổng trả kỳ 1 > tổng trả kỳ cuối
    assert schedule.payments[0].total_payment > schedule.payments[-1].total_payment
    # Dư nợ cuối = 0
    assert schedule.payments[-1].closing_balance == 0
    print(f"  [OK] Equal principal 100tr/12%/12m: "
          f"kỳ 1 = {schedule.payments[0].total_payment:,.0f}, "
          f"kỳ cuối = {schedule.payments[-1].total_payment:,.0f}, "
          f"tổng lãi = {schedule.total_interest:,.0f}")


def test_equal_principal_saves_interest():
    """Invariant tài chính quan trọng: tổng lãi PA2 < PA1."""
    principal = 50_000_000
    rate = 0.24
    term = 24

    annuity = calculate_annuity(principal, rate, term)
    eq = calculate_equal_principal(principal, rate, term)

    assert eq.total_interest < annuity.total_interest, \
        "Gốc đều phải tiết kiệm lãi hơn niên kim"
    saving = annuity.total_interest - eq.total_interest
    print(f"  [OK] PA2 tiết kiệm {saving:,.0f} VNĐ so với PA1 trên cùng khoản vay")


def test_annuity_zero_rate():
    """Case đặc biệt: lãi suất 0% (chương trình khuyến mãi)."""
    schedule = calculate_annuity(12_000_000, 0.0, 12)
    assert schedule.total_interest == 0
    assert all(p.interest == 0 for p in schedule.payments)
    assert all(abs(p.principal - 1_000_000) < 1 for p in schedule.payments)
    print(f"  [OK] Zero interest: total interest = 0")


# ==========================================
# RUNNER
# ==========================================

def run_all():
    tests = [
        test_persona_A_approved_priority,
        test_persona_B_manual_review,
        test_persona_C_rejected,
        test_annuity_basic,
        test_equal_principal_basic,
        test_equal_principal_saves_interest,
        test_annuity_zero_rate,
    ]
    print("=" * 70)
    print("CHẠY UNIT TESTS")
    print("=" * 70)
    passed = 0
    failed = 0
    for t in tests:
        try:
            print(f"\n>> {t.__name__}")
            t()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"KẾT QUẢ: {passed} passed, {failed} failed")
    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
