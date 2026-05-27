import argparse
from loan.eligibility import evaluate, format_report, ApplicantProfile, ClientInfo, CreditHistory, AccountInfo


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--income", type=float, required=True)
    p.add_argument("--debt", type=float, required=True)
    p.add_argument("--tenure-months", type=int, required=True)
    p.add_argument("--age", type=int, required=True)
    p.add_argument("--savings-balance", type=float, required=True)
    p.add_argument("--late-payments", type=int, default=0)
    p.add_argument("--dependents", type=int, default=0)
    p.add_argument("--name", type=str, default="Member")
    a = p.parse_args()

    applicant = ApplicantProfile(
        client=ClientInfo(
            income=a.income,
            age=a.age,
            dependents=a.dependents,
        ),
        credit=CreditHistory(
            late_payments=a.late_payments,
        ),
        account=AccountInfo(
            savings_balance=a.savings_balance,
            debt=a.debt,
            tenure_months=a.tenure_months,
        ),
    )

    r = evaluate(applicant)
    print(format_report(r, a.name))

if __name__ == "__main__":
    main()
