"""Integration tests for financial reports."""
from __future__ import annotations


class TestReportsAuthenticated:
    def test_profit_loss_requires_auth(self, client):
        response = client.post(
            "/api/v1/reports/profit-loss",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        assert response.status_code == 401

    def test_balance_sheet_requires_auth(self, client):
        response = client.post(
            "/api/v1/reports/balance-sheet",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        assert response.status_code == 401

    def test_trial_balance_requires_auth(self, client):
        response = client.post(
            "/api/v1/reports/trial-balance",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        assert response.status_code == 401

    def test_general_ledger_requires_auth(self, client):
        response = client.post(
            "/api/v1/reports/general-ledger",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        assert response.status_code == 401

    def test_ar_aging_requires_auth(self, client):
        response = client.post("/api/v1/reports/ar-aging", json={})
        assert response.status_code == 401

    def test_ap_aging_requires_auth(self, client):
        response = client.post("/api/v1/reports/ap-aging", json={})
        assert response.status_code == 401

    def test_cash_summary_requires_auth(self, client):
        response = client.post(
            "/api/v1/reports/cash-summary",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
        )
        assert response.status_code == 401


class TestProfitLoss:
    def test_profit_loss_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/profit-loss",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "Profit & Loss"
        assert "revenue" in data
        assert "expenses" in data
        assert "net_income" in data
        assert "period" in data
        assert data["period"]["start_date"] == "2026-01-01"
        assert data["period"]["end_date"] == "2026-12-31"


class TestBalanceSheet:
    def test_balance_sheet_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/balance-sheet",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "Balance Sheet"
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "as_of" in data


class TestTrialBalance:
    def test_trial_balance_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/trial-balance",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "Trial Balance"
        assert "accounts" in data
        assert "total_debits" in data
        assert "total_credits" in data


class TestGeneralLedger:
    def test_general_ledger_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/general-ledger",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "General Ledger"
        assert "accounts" in data
        assert "period" in data


class TestArAging:
    def test_ar_aging_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/ar-aging",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "AR Aging"
        assert "total_outstanding" in data
        assert "buckets" in data
        assert "contacts" in data


class TestApAging:
    def test_ap_aging_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/ap-aging",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "AP Aging"
        assert "total_outstanding" in data
        assert "buckets" in data
        assert "vendors" in data


class TestCashSummary:
    def test_cash_summary_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/reports/cash-summary",
            json={"start_date": "2026-01-01", "end_date": "2026-12-31"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["report"] == "Cash Summary"
        assert "accounts" in data
        assert "total_balance" in data
