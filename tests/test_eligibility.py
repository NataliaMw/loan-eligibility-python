import io
import sys
import pytest
from loan.eligibility import evaluate, classify_member, get_audit_count, ApplicantProfile, ClientInfo, CreditHistory, AccountInfo

def make_applicant(**kwargs):
    return ApplicantProfile(
        client=ClientInfo(
            income=kwargs.get("income", 1500),
            age=kwargs.get("age", 30),
            is_pensioner=kwargs.get("is_pensioner", False),
            dependents=kwargs.get("dependents", 0),
            is_employee=kwargs.get("is_employee", True),
            has_guarantor=kwargs.get("has_guarantor", False),
        ),
        credit=CreditHistory(
            late_payments=kwargs.get("late_payments", 0),
            history=kwargs.get("history", []),
        ),
        account=AccountInfo(
            savings_balance=kwargs.get("savings_balance", 500),
            debt=kwargs.get("debt", 200),
            status_tag=kwargs.get("status_tag", " ACTIVE "),
            tenure_months=kwargs.get("tenure_months", 24),
        ),
    )

def test_employee_eligible_basic():
    r = evaluate(make_applicant(income=1500, debt=400, tenure_months=24, age=30, savings_balance=800, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is True
    assert r["amount"] > 0


def test_employee_high_dti_rejected():
    r = evaluate(make_applicant(income=1000, debt=500, tenure_months=24, age=30, savings_balance=200, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is False
    assert "DTI_HIGH" in r["reasons"]


def test_age_too_low():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=12, age=17, savings_balance=500, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is False
    assert "AGE_LOW" in r["reasons"]


def test_age_exactly_18_accepted():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=12, age=18, savings_balance=500, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is True


def test_age_exactly_65_accepted_as_employee():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=12, age=65, savings_balance=500, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is True


def test_age_66_employee_rejected():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=12, age=66, savings_balance=500, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is False
    assert "AGE_HIGH" in r["reasons"]


def test_pensioner_over_65_accepted():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=12, age=70, savings_balance=500, is_employee=False, is_pensioner=True, history=[]))
    assert r["eligible"] is True


def test_short_tenure_with_guarantor_passes():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=3, age=30, savings_balance=500, has_guarantor=True, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is True


def test_short_tenure_without_guarantor_rejected():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=3, age=30, savings_balance=500, has_guarantor=False, is_employee=True, is_pensioner=False, history=[]))
    assert r["eligible"] is False
    assert "TENURE_LOW" in r["reasons"]


def test_employee_rate_floor():
    r = evaluate(make_applicant(income=3000, debt=300, tenure_months=60, age=40, savings_balance=5000, late_payments=0, is_employee=True, is_pensioner=False, history=[]))
    assert r["rate"] >= 0.08


def test_pensioner_rate_floor():
    r = evaluate(make_applicant(income=2000, debt=200, tenure_months=60, age=70, savings_balance=5000, late_payments=0, is_employee=False, is_pensioner=True, history=[]))
    assert r["rate"] >= 0.10


def test_late_payments_increase_rate():
    a = evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, late_payments=0, is_employee=True, is_pensioner=False, history=[]))
    b = evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, late_payments=8, is_employee=True, is_pensioner=False, history=[]))
    assert b["rate"] > a["rate"]


def test_amount_capped():
    r = evaluate(make_applicant(income=20000, debt=100, tenure_months=60, age=40, savings_balance=50000, is_employee=True, is_pensioner=False, history=[]))
    assert r["amount"] <= 15000


def test_zero_late_payments_score_is_full():
    a = evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, late_payments=0, is_employee=True, is_pensioner=False, history=[]))
    b = evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, late_payments=1, is_employee=True, is_pensioner=False, history=[]))
    assert a["amount"] == b["amount"]


def test_status_inactive_with_trailing_whitespace_is_active():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, is_employee=True, is_pensioner=False, status_tag=" ACTIVE ", history=[]))
    assert "STATUS_INACTIVE" not in r["reasons"]


def test_status_inactive_real():
    r = evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, is_employee=True, is_pensioner=False, status_tag="SUSPENDED", history=[]))
    assert "STATUS_INACTIVE" in r["reasons"]


def test_reasons_field_is_string():
    r = evaluate(make_applicant(income=1000, debt=500, tenure_months=24, age=30, savings_balance=200, is_employee=True, is_pensioner=False, history=[]))
    assert isinstance(r["reasons"], str)


def test_audit_counter_increments():
    before = get_audit_count()
    evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, is_employee=True, is_pensioner=False, history=[]))
    after = get_audit_count()
    assert after == before + 1


def test_evaluation_prints_log_line(capsys):
    evaluate(make_applicant(income=1500, debt=200, tenure_months=24, age=30, savings_balance=300, is_employee=True, is_pensioner=False, history=[]))
    captured = capsys.readouterr()
    assert "[loan-eval]" in captured.out


def test_classify_member_top():
    assert classify_member(2500, 6000) == "A"


def test_classify_member_bottom():
    assert classify_member(300, 100) == "D"


def test_classify_member_first_match_wins():
    assert classify_member(2001, 5001) == "A"
