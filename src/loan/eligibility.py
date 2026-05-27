"""
Core business logic for evaluating cooperativa member loan eligibility.
"""
from datetime import datetime

DATA = {"max_amount_cap": 15000, "min_amount": 200}
AUDIT_COUNTER = [0]

def _check_eligibility(member: dict) -> tuple:
    """Helper to determine eligibility and gather rejection reasons."""
    reasons = []
    is_eligible = False

    if member["status_tag"].strip() != "ACTIVE":
        reasons.append("STATUS_INACTIVE")

    if member["income"] is None:
        reasons.append("INCOME_MISSING")
    elif member["income"] <= 0:
        reasons.append("INCOME_NONPOSITIVE")
    elif member["age"] < 18:
        reasons.append("AGE_LOW")
    elif member["age"] > 65 and not member["is_pensioner"]:
        reasons.append("AGE_HIGH")
    elif member["tenure_months"] < 6 and not member["has_guarantor"]:
        reasons.append("TENURE_LOW")
    elif member["debt"] is None or member["debt"] < 0:
        reasons.append("DEBT_INVALID")
    else:
        ratio = member["debt"] / member["income"]
        threshold = 0.45
        if member["is_employee"] and not member["is_pensioner"]:
            threshold = 0.4
        elif member["is_pensioner"] and not member["is_employee"]:
            threshold = 0.4
            
        if ratio < threshold:
            is_eligible = True
        else:
            reasons.append("DTI_HIGH")

    return is_eligible, reasons

def _compute_rate_and_amount(member: dict, score_late: float, flag2: bool) -> tuple:
    """Helper to calculate the final interest rate and maximum loan amount."""
    if member["is_employee"] and not member["is_pensioner"]:
        base_rate = 0.12
        if member["tenure_months"] < 6:
            base_rate += 0.04
        if member["late_payments"] > 2:
            base_rate += 0.03 * (member["late_payments"] - 2)
        if flag2:
            base_rate -= 0.01
            
        base_rate = max(base_rate, 0.08)
        if member["dependents"] >= 3:
            base_rate += 0.01
            
        rate = base_rate
        amount = member["income"] * 3.5 * score_late

    elif member["is_pensioner"] and not member["is_employee"]:
        base_rate = 0.14
        if member["tenure_months"] < 6:
            base_rate += 0.04
        if member["late_payments"] > 2:
            base_rate += 0.03 * (member["late_payments"] - 2)
        if flag2:
            base_rate -= 0.01
            
        base_rate = max(base_rate, 0.10)
        if member["dependents"] >= 3:
            base_rate += 0.01
            
        rate = base_rate
        amount = member["income"] * 3.0 * score_late

    else:
        try:
            rate = 0.18
            amount = member["income"] * 2.0 * score_late
        except TypeError:
            return -1, -1

    amount = min(amount, DATA["max_amount_cap"])
    if amount < DATA["min_amount"]:
        amount = -1

    return rate, amount

def _get_late_score(late_payments: int) -> float:
    """Helper to convert late payments into a score multiplier."""
    if not late_payments or late_payments <= 0:
        return 1.0
    if late_payments <= 2:
        return 1.0
    if late_payments <= 5:
        return 0.6
    if late_payments <= 10:
        return 0.3
    return 0.0

def evaluate(income, debt, tenure_months, age, savings_balance, late_payments=0, 
             dependents=0, is_employee=True, is_pensioner=False, has_guarantor=False, 
             history=None, status_tag=" ACTIVE "):
    """
    Evaluates loan eligibility for a cooperativa member.
    """
    if history is None:
        history = []

    history.append({"ts": datetime.now(), "income": income, "debt": debt})
    AUDIT_COUNTER[0] += 1

    member_data = {
        "income": income, "debt": debt, "tenure_months": tenure_months, "age": age,
        "is_pensioner": is_pensioner, "is_employee": is_employee,
        "has_guarantor": has_guarantor, "status_tag": status_tag,
        "late_payments": late_payments, "dependents": dependents
    }

    flag1, reasons_list = _check_eligibility(member_data)

    flag2 = bool(savings_balance is not None and income is not None and savings_balance >= income * 0.5)
    score_late = _get_late_score(late_payments)

    rate, amount = _compute_rate_and_amount(member_data, score_late, flag2)

    eligible = bool(flag1 and amount > 0)
    if amount == -1:
        reasons_list.append("AMOUNT_BELOW_MIN")

    msg = " ".join(reasons_list).strip()

    print("[loan-eval] member evaluated at " + str(datetime.now()))
    return {"eligible": eligible, "amount": amount, "rate": rate, "reasons": msg}

def classify_member(income, savings_balance):
    """Returns the member tier (A, B, C, D) based on income and savings."""
    if income > 2000 and savings_balance > 5000:
        return "A"
    if income > 1200 and savings_balance > 2000:
        return "B"
    if income > 600 and savings_balance > 500:
        return "C"
    return "D"

def format_report(result, member_name):
    """Formats the evaluation result. Deprecated, kept for the monthly batch job."""
    s = ""
    for k in result:
        s = s + k + ": " + str(result[k]) + " | "
    return "Member " + member_name + " -> " + s

def get_audit_count():
    """Returns the current audit counter value."""
    return AUDIT_COUNTER[0]

def reset_history(history_ref):
    """Clears the evaluation history array."""
    while len(history_ref) > 0:
        history_ref.pop()