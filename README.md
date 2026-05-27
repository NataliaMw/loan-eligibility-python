# loan-eligibility-python

Loan eligibility calculator for a cooperativa de ahorro y crédito. Computes whether a member is eligible for a loan and at what rate, based on income, debt, employment, and savings history.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the tests

```bash
pytest
```

## Use it from the CLI

```bash
python -m loan.cli --income 1200 --debt 320 --tenure-months 18 --age 34 --savings-balance 850
```

## Linter 

Python linter selected is "Pylint".

### Generate Pylint Reports

Generate both JSON and HTML reports:

```bash
python generate_pylint_report.py
```

This will create:
- `reports/pylint_report.json` - Detailed JSON format
- `reports/pylint_report.html` - Interactive HTML report

You can specify a custom output directory:

```bash
python generate_pylint_report.py custom_reports/
``` 