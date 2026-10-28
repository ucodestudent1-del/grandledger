"""Integration tests for API endpoints."""
from __future__ import annotations


class TestAuthSignup:
    def test_signup_creates_user_and_company(self, client):
        unique = "newuser123"
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"{unique}@test.com",
                "name": "New User",
                "password": "Password123",
                "company_name": "New Company",
                "company_slug": f"new-company-{unique}",
                "role": "owner",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_signup_duplicate_email_fails(self, client, auth_user):
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": auth_user["email"],
                "name": "Dup User",
                "password": "Password123",
                "company_name": "Another",
                "company_slug": "dup-company-abc",
                "role": "owner",
            },
        )
        assert response.status_code == 409


class TestAuthLogin:
    def test_login_returns_token(self, client, auth_user):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": auth_user["email"],
                "password": "Password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


class TestAuthMe:
    def test_get_me(self, client, auth_headers, auth_user):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == auth_user["email"]


class TestCompanies:
    def test_list_companies_empty(self, client, auth_headers):
        response = client.get("/api/v1/companies", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_company(self, client, auth_headers):
        response = client.get("/api/v1/companies", headers=auth_headers)
        assert response.status_code == 200
        companies = response.json()
        assert len(companies) >= 1


class TestAccounts:
    def test_create_account_requires_auth(self, client):
        response = client.post(
            "/api/v1/accounts",
            json={"code": "1000", "name": "Cash", "type": "asset"},
        )
        assert response.status_code == 401

    def test_list_accounts(self, client, auth_headers):
        response = client.get("/api/v1/accounts", headers=auth_headers)
        assert response.status_code == 200


class TestJournals:
    def test_create_journal_requires_auth(self, client):
        response = client.post(
            "/api/v1/journals",
            json={
                "entry_date": "2026-10-26",
                "description": "Test",
                "lines": [],
            },
        )
        assert response.status_code == 401

    def test_journal_list_requires_auth(self, client):
        response = client.get("/api/v1/journals")
        assert response.status_code == 401


class TestInvoices:
    def test_invoices_require_auth(self, client):
        response = client.get("/api/v1/invoices")
        assert response.status_code == 401


class TestReports:
    def test_pnl_requires_auth(self, client):
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
