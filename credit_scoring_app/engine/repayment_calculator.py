"""
Module tính 2 phương án trả nợ cho khoản vay tiêu dùng.

Phương án 1 - Niên kim (Annuity / PMT đều):
  Gốc + lãi mỗi kỳ bằng nhau. Kỳ đầu lãi nhiều gốc ít, kỳ cuối ngược lại.
  Công thức: A = P * i * (1+i)^n / ((1+i)^n - 1)
  
Phương án 2 - Gốc đều (Equal principal):
  Gốc mỗi kỳ cố định = P/n. Lãi tính theo dư nợ đầu kỳ (giảm dần).
  Tổng trả mỗi kỳ = P/n + dư_nợ_đầu_kỳ * i
  Tổng lãi PA2 luôn < PA1.
"""

from dataclasses import dataclass


@dataclass
class RepaymentPayment:
    """Một dòng trong bảng lịch trả nợ."""
    period: int
    opening_balance: float   # Dư nợ đầu kỳ
    principal: float         # Gốc trả kỳ này
    interest: float          # Lãi trả kỳ này
    total_payment: float     # Tổng trả kỳ này (= principal + interest)
    closing_balance: float   # Dư nợ cuối kỳ


@dataclass
class RepaymentSchedule:
    """Kết quả tính lịch trả nợ đầy đủ cho 1 phương án."""
    plan_name: str           # "Niên kim" hoặc "Gốc đều"
    plan_code: str           # "annuity" hoặc "equal_principal"
    principal_amount: float  # P - số tiền vay gốc
    annual_rate: float       # Lãi suất năm
    term_months: int         # Số kỳ (tháng)
    payments: list[RepaymentPayment]
    total_interest: float    # Tổng lãi phải trả
    total_paid: float        # Tổng phải trả (gốc + lãi)


def calculate_annuity(principal: float, annual_rate: float, term_months: int) -> RepaymentSchedule:
    """
    Phương án 1: Gốc + lãi đều các kỳ (PMT/Annuity).
    A = P * i * (1+i)^n / ((1+i)^n - 1)
    """
    if term_months <= 0:
        raise ValueError("term_months phải > 0")
    if principal <= 0:
        raise ValueError("principal phải > 0")

    monthly_rate = annual_rate / 12

    # Xử lý đặc biệt: lãi suất 0%
    if monthly_rate == 0:
        monthly_payment = principal / term_months
    else:
        monthly_payment = (
            principal * monthly_rate * (1 + monthly_rate) ** term_months
            / ((1 + monthly_rate) ** term_months - 1)
        )

    payments = []
    balance = principal

    for k in range(1, term_months + 1):
        interest_k = balance * monthly_rate
        principal_k = monthly_payment - interest_k
        # Điều chỉnh kỳ cuối để tránh lỗi làm tròn
        if k == term_months:
            principal_k = balance
            total_k = principal_k + interest_k
        else:
            total_k = monthly_payment
        new_balance = balance - principal_k

        payments.append(RepaymentPayment(
            period=k,
            opening_balance=round(balance, 0),
            principal=round(principal_k, 0),
            interest=round(interest_k, 0),
            total_payment=round(total_k, 0),
            closing_balance=round(max(new_balance, 0), 0),
        ))
        balance = new_balance

    total_interest = sum(p.interest for p in payments)
    total_paid = sum(p.total_payment for p in payments)

    return RepaymentSchedule(
        plan_name="Phương án 1: Gốc + lãi đều (Niên kim)",
        plan_code="annuity",
        principal_amount=principal,
        annual_rate=annual_rate,
        term_months=term_months,
        payments=payments,
        total_interest=round(total_interest, 0),
        total_paid=round(total_paid, 0),
    )


def calculate_equal_principal(principal: float, annual_rate: float, term_months: int) -> RepaymentSchedule:
    """
    Phương án 2: Gốc đều, lãi theo dư nợ đầu kỳ.
    Gốc kỳ k = P / n
    Lãi kỳ k = dư_nợ_đầu_kỳ_k * monthly_rate
    """
    if term_months <= 0:
        raise ValueError("term_months phải > 0")
    if principal <= 0:
        raise ValueError("principal phải > 0")

    monthly_rate = annual_rate / 12
    principal_per_period = principal / term_months

    payments = []
    balance = principal

    for k in range(1, term_months + 1):
        interest_k = balance * monthly_rate
        principal_k = principal_per_period
        # Điều chỉnh kỳ cuối
        if k == term_months:
            principal_k = balance
        total_k = principal_k + interest_k
        new_balance = balance - principal_k

        payments.append(RepaymentPayment(
            period=k,
            opening_balance=round(balance, 0),
            principal=round(principal_k, 0),
            interest=round(interest_k, 0),
            total_payment=round(total_k, 0),
            closing_balance=round(max(new_balance, 0), 0),
        ))
        balance = new_balance

    total_interest = sum(p.interest for p in payments)
    total_paid = sum(p.total_payment for p in payments)

    return RepaymentSchedule(
        plan_name="Phương án 2: Gốc đều + lãi theo dư nợ đầu kỳ",
        plan_code="equal_principal",
        principal_amount=principal,
        annual_rate=annual_rate,
        term_months=term_months,
        payments=payments,
        total_interest=round(total_interest, 0),
        total_paid=round(total_paid, 0),
    )


def calculate_both_plans(principal: float, annual_rate: float, term_months: int) -> dict:
    """Tính cả 2 phương án để so sánh."""
    return {
        "plan_1_annuity": calculate_annuity(principal, annual_rate, term_months),
        "plan_2_equal_principal": calculate_equal_principal(principal, annual_rate, term_months),
    }
