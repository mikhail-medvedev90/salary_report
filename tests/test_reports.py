import pytest
from src.main import PayoutReport, AverageRateReport

@pytest.fixture
def sample_records():
    return [
        {"id": "1", "name": "Alice", "department": "HR", "hours_worked": "160", "hourly_rate": "50"},
        {"id": "2", "name": "Bob", "department": "Engineering", "hours_worked": "170", "hourly_rate": "60"},
        {"id": "3", "name": "Charlie", "department": "Engineering", "hours_worked": "150", "hourly_rate": "55"},
        {"id": "4", "name": "Dana", "department": "HR", "hours_worked": "160"},
        {"id": "5", "name": "Eve", "department": "HR", "hours_worked": "bad", "hourly_rate": "40"},
    ]

def test_payout_report(sample_records):
    report = PayoutReport()
    result = report.generate(sample_records)

    assert result["report"] == "payout"
    assert len(result["results"]) == 3

    payouts = {r["name"]: r["payout"] for r in result["results"]}
    assert payouts["Alice"] == 8000.0
    assert payouts["Bob"] == 10200.0
    assert payouts["Charlie"] == 8250.0

def test_average_rate_report(sample_records):
    report = AverageRateReport()
    result = report.generate(sample_records)

    assert result["report"] == "average_rate"
    assert set(result["results"]) == {"HR", "Engineering"}

    assert result["results"]["HR"] == 45.0
    assert result["results"]["Engineering"] == 57.5
