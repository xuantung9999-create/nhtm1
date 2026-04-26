"""
Credit Scoring Engine cho sản phẩm vay tiêu dùng Việt Nam
Tác giả: [Tên sinh viên]
Môn học: [Tên môn]

Module này cung cấp 3 class chính:
- HardRulesChecker: kiểm tra các điều kiện loại trực tiếp
- Scorer: chấm điểm dựa trên scorecard
- GradeClassifier: phân hạng tín dụng

Logic tách rời hoàn toàn khỏi cấu hình (scorecard.json) để dễ bảo trì.
"""

import json
from dataclasses import dataclass, field
from typing import Any


# ============================================================
# DATA CLASSES cho kết quả
# ============================================================

@dataclass
class HardRuleResult:
    """Kết quả kiểm tra một hard rule cụ thể."""
    rule_id: str
    description: str
    passed: bool
    actual_value: Any
    threshold: Any


@dataclass
class HardRulesCheckResult:
    """Kết quả tổng hợp kiểm tra toàn bộ hard rules."""
    all_passed: bool
    checks: list[HardRuleResult]

    @property
    def failed_rules(self) -> list[HardRuleResult]:
        return [c for c in self.checks if not c.passed]



class VariableScore:
    """Điểm của một biến cụ thể."""
    variable_key: str
    variable_name: str
    actual_value: Any
    points: int
    max_points: int


@dataclass
class GroupScore:
    """Điểm của một nhóm chứng từ."""
    group_key: str
    group_name: str
    weight: float
    points: int
    max_points: int
    variables: list[VariableScore] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.points / self.max_points if self.max_points > 0 else 0.0


@dataclass
class ScoringResult:
    """Kết quả chấm điểm đầy đủ."""
    total_points: int
    max_total_points: int
    groups: list[GroupScore] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.total_points / self.max_total_points if self.max_total_points > 0 else 0.0


@dataclass
class GradeResult:
    """Kết quả xếp hạng."""
    grade: str
    decision: str
    risk_level: str
    interest_rate_annual: float | None
    min_score_required: int
    interest_rate_min: float | None = None
    interest_rate_max: float | None = None
    interest_rate_min: float | None = None
    interest_rate_max: float | None = None
    risk_premium: float | None = None
    risk_premium: float | None = None


@dataclass
class CreditDecision:
    """Quyết định xét duyệt tổng thể."""
    persona_id: str
    hard_rules_result: HardRulesCheckResult
    scoring_result: ScoringResult | None
    grade_result: GradeResult | None
    final_decision: str  # "approved_priority" | "approved" | "approved_conditional" | "manual_review" | "rejected"
    rejection_reasons: list[str] = field(default_factory=list)


# ============================================================
# HARD RULES CHECKER
# ============================================================

class HardRulesChecker:
    """Chạy các điều kiện loại trực tiếp trước khi chấm điểm."""

    def __init__(self, scorecard: dict):
        self.rules = scorecard["hard_rules"]

    def check(self, applicant: dict) -> HardRulesCheckResult:
        """
        Chạy toàn bộ hard rules cho 1 applicant.
        applicant phải có các trường flatten: age, monthly_income_vnd, 
        employment_duration_months, credit_history_cic, dti_after_loan.
        """
        checks = []
        for rule in self.rules:
            result = self._evaluate_rule(rule, applicant)
            checks.append(result)
        return HardRulesCheckResult(
            all_passed=all(c.passed for c in checks),
            checks=checks,
        )

    def _evaluate_rule(self, rule: dict, applicant: dict) -> HardRuleResult:
        field_name = rule["field"]
        actual = applicant.get(field_name)
        rule_type = rule["type"]

        if rule_type == "numeric_min":
            threshold = rule["threshold"]
            passed = actual is not None and actual >= threshold
            return HardRuleResult(rule["id"], rule["description"], passed, actual, f">= {threshold}")

        if rule_type == "numeric_max":
            threshold = rule["threshold"]
            passed = actual is not None and actual <= threshold
            return HardRuleResult(rule["id"], rule["description"], passed, actual, f"<= {threshold}")

        if rule_type == "not_in":
            blocked = rule["blocked_values"]
            passed = actual not in blocked
            return HardRuleResult(rule["id"], rule["description"], passed, actual, f"not in {blocked}")

        raise ValueError(f"Unknown rule type: {rule_type}")


# ============================================================
# SCORER
# ============================================================

class Scorer:
    """Chấm điểm scorecard dựa trên cấu hình JSON."""

    def __init__(self, scorecard: dict):
        self.groups_config = scorecard["scoring_groups"]
        self.max_score = scorecard["scoring_system"]["max_score"]

    def score(self, applicant: dict) -> ScoringResult:
        """Chấm điểm toàn bộ 4 nhóm, trả về ScoringResult."""
        groups = []
        total_points = 0
        max_total = 0

        for group_key, group_cfg in self.groups_config.items():
            group_score = self._score_group(group_key, group_cfg, applicant)
            groups.append(group_score)
            total_points += group_score.points
            max_total += group_score.max_points

        return ScoringResult(
            total_points=total_points,
            max_total_points=max_total,
            groups=groups,
        )

    def _score_group(self, group_key: str, group_cfg: dict, applicant: dict) -> GroupScore:
        variables = []
        total = 0

        for var_key, var_cfg in group_cfg["variables"].items():
            var_score = self._score_variable(var_key, var_cfg, applicant)
            variables.append(var_score)
            total += var_score.points

        return GroupScore(
            group_key=group_key,
            group_name=group_cfg["name"],
            weight=group_cfg["weight"],
            points=total,
            max_points=group_cfg["max_points"],
            variables=variables,
        )

    def _score_variable(self, var_key: str, var_cfg: dict, applicant: dict) -> VariableScore:
        value = applicant.get(var_key)
        var_type = var_cfg["type"]

        if var_type == "categorical":
            points = var_cfg["bins"].get(value, 0)
        elif var_type == "numeric_range":
            points = self._bin_numeric(value, var_cfg["bins"])
        else:
            raise ValueError(f"Unknown variable type: {var_type}")

        return VariableScore(
            variable_key=var_key,
            variable_name=var_cfg["name"],
            actual_value=value,
            points=points,
            max_points=var_cfg["max_points"],
        )

    @staticmethod
    def _bin_numeric(value, bins: list[dict]) -> int:
        """Tìm bin phù hợp theo logic value <= bin['max']."""
        if value is None:
            return 0
        for b in bins:
            if value <= b["max"]:
                return b["points"]
        return 0


# ============================================================
# GRADE CLASSIFIER
# ============================================================

class GradeClassifier:
    """Phân hạng tín dụng dựa trên tổng điểm."""

    def __init__(self, scorecard: dict):
        # Sort giảm dần theo min_score để tìm hạng đầu tiên phù hợp
        self.thresholds = sorted(
            scorecard["scoring_system"]["grade_thresholds"],
            key=lambda x: x["min_score"],
            reverse=True,
        )

    def classify(self, total_points: int) -> GradeResult:
        for t in self.thresholds:
            if total_points >= t["min_score"]:
                return GradeResult(
                    grade=t["grade"],
                    decision=t["decision"],
                    risk_level=t["risk_level"],
                    interest_rate_annual=t["interest_rate_annual"],
                    min_score_required=t["min_score"],
                    interest_rate_min=t.get("interest_rate_min"),
                    interest_rate_max=t.get("interest_rate_max"),
                    risk_premium=t.get("risk_premium"),
                )
        # Fallback (không bao giờ tới đây vì B có min_score=0)
        raise RuntimeError("No grade matched, check scorecard config")


# ============================================================
# PIPELINE TỔNG
# ============================================================

class CreditScoringPipeline:
    """
    Pipeline hoàn chỉnh: flatten applicant → hard rules → scoring → grading.
    Đầu vào: persona dict có cấu trúc nested (theo personas.json).
    Đầu ra: CreditDecision.
    """

    def __init__(self, scorecard_path: str):
        with open(scorecard_path, encoding="utf-8") as f:
            self.scorecard = json.load(f)
        self.hard_checker = HardRulesChecker(self.scorecard)
        self.scorer = Scorer(self.scorecard)
        self.classifier = GradeClassifier(self.scorecard)

    def evaluate(self, persona: dict) -> CreditDecision:
        persona_id = persona.get("persona_id", "unknown")
        flat = self._flatten_persona(persona)

        # Bước 1: Hard rules
        hard_result = self.hard_checker.check(flat)
        if not hard_result.all_passed:
            reasons = [c.description for c in hard_result.failed_rules]
            return CreditDecision(
                persona_id=persona_id,
                hard_rules_result=hard_result,
                scoring_result=None,
                grade_result=None,
                final_decision="rejected",
                rejection_reasons=reasons,
            )

        # Bước 2: Chấm điểm
        scoring = self.scorer.score(flat)

        # Bước 3: Xếp hạng
        grade = self.classifier.classify(scoring.total_points)

        return CreditDecision(
            persona_id=persona_id,
            hard_rules_result=hard_result,
            scoring_result=scoring,
            grade_result=grade,
            final_decision=grade.decision,
            rejection_reasons=[],
        )

    @staticmethod
    def _flatten_persona(persona: dict) -> dict:
        """
        Gộp các trường nested trong persona thành 1 dict phẳng để chấm điểm.
        Tính thêm DTI sau vay mới = (nợ hiện tại + PMT khoản vay mới) / thu nhập.
        """
        flat = {}
        flat.update(persona.get("personal_info", {}))
        flat.update(persona.get("employment", {}))
        flat.update(persona.get("credit_history", {}))
        flat.update(persona.get("assets", {}))

        # Tính DTI sau khi cộng khoản vay mới
        loan = persona.get("loan_request", {})
        income = flat.get("monthly_income_vnd", 1)  # tránh chia 0
        dti_current = flat.get("dti_current", 0.0)
        loan_amount = loan.get("loan_amount_vnd", 0)
        term = loan.get("term_months", 12)
        # Ước tính PMT ở lãi suất trung bình 24% để check DTI (không phải lãi suất cuối)
        est_annual_rate = 0.24
        est_monthly_rate = est_annual_rate / 12
        if term > 0 and est_monthly_rate > 0:
            est_pmt = loan_amount * est_monthly_rate * (1 + est_monthly_rate) ** term / ((1 + est_monthly_rate) ** term - 1)
        else:
            est_pmt = loan_amount / max(term, 1)
        dti_after_loan = dti_current + (est_pmt / income if income > 0 else 1.0)
        flat["dti_after_loan"] = dti_after_loan

        return flat


# ============================================================
# CONVENIENCE FUNCTION
# ============================================================

def evaluate_applicant(scorecard_path: str, persona: dict) -> CreditDecision:
    """Shortcut để chạy toàn bộ pipeline trong 1 lần."""
    pipeline = CreditScoringPipeline(scorecard_path)
    return pipeline.evaluate(persona)
