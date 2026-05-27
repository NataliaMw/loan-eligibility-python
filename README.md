# loan-eligibility-python

Loan eligibility calculator for a cooperativa de ahorro y crédito. Computes whether a member is eligible for a loan and at what rate, based on income, debt, employment, and savings history.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Linting

This project uses the following linting tools:

- `pylint==4.0.5`
- `pylint-json2html==0.5.0`

### Rule Profile

The project follows the default `pylint` rule profile unless otherwise configured in a `.pylintrc` file.

### Run the Linter

```bash
pylint loan
```

### Generate HTML Report

```bash
pylint loan --output-format=json > pylint-report.json
pylint-json2html -f json -o pylint-report.html pylint-report.json
```

## Run the tests

```bash
pytest
```

## Use it from the CLI

```bash
python -m loan.cli --income 1200 --debt 320 --tenure-months 18 --age 34 --savings-balance 850
```