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
    def test_list_companies_requires_auth(self, client):
        response = client.get("/api/v1/companies")
        assert response.status_code == 401

    def test_list_companies_empty(self, client, auth_headers):
        response = client.get("/api/v1/companies", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_company(self, client, auth_headers):
        response = client.get("/api/v1/companies", headers=auth_headers)
        assert response.status_code == 200
        companies = response.json()
        assert len(companies) >= 1

    def test_get_company_requires_auth(self, client):
        response = client.get("/api/v1/companies/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 401


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


class TestPasswordReset:
    def test_request_password_reset(self, client, test_user):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        assert response.status_code == 200
        assert "message" in response.json()

    def test_request_password_reset_unknown_email(self, client):
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 200
        assert "If the email exists" in response.json()["message"]


class TestSessionManagement:
    def test_list_sessions(self, client, auth_headers):
        response = client.get("/api/v1/auth/sessions", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_revoke_session(self, client, auth_user, auth_headers):
        sessions_resp = client.get("/api/v1/auth/sessions", headers=auth_headers)
        sessions = sessions_resp.json()
        if sessions:
            session_id = sessions[0]["id"]
            response = client.delete(
                f"/api/v1/auth/sessions/{session_id}",
                headers=auth_headers,
            )
            assert response.status_code == 200


class TestTenantIsolation:
    def test_cannot_post_other_company_journal(self, client, db_session):
        """User from Company B should not be able to post Journal Entry from Company A."""
        import uuid

        from src.core.security import create_access_token, get_password_hash
        from src.models import Account, AccountType
        from src.models import Company as CompanyModel
        from src.models import User as UserModel

        # Company A + User A + Accounts
        company_a = CompanyModel(name="Company A", slug=f"co-a-{uuid.uuid4().hex[:8]}", currency="USD")
        db_session.add(company_a)
        db_session.flush()

        acct_asset = Account(company_id=company_a.id, code="1000", name="Cash", type=AccountType.ASSET, is_system=True)
        acct_liab = Account(company_id=company_a.id, code="1200", name="AP", type=AccountType.LIABILITY, is_system=True)
        db_session.add(acct_asset)
        db_session.add(acct_liab)
        db_session.flush()

        user_a = UserModel(
            company_id=company_a.id,
            email=f"user-a-{uuid.uuid4().hex[:8]}@example.com",
            name="User A",
            role="owner",
            password_hash=get_password_hash("Password123"),
            is_verified=True,
        )
        db_session.add(user_a)
        db_session.commit()
        db_session.refresh(user_a)

        # Company B + User B
        company_b = CompanyModel(name="Company B", slug=f"co-b-{uuid.uuid4().hex[:8]}", currency="USD")
        db_session.add(company_b)
        db_session.commit()
        db_session.refresh(company_b)

        user_b = UserModel(
            company_id=company_b.id,
            email=f"user-b-{uuid.uuid4().hex[:8]}@example.com",
            name="User B",
            role="owner",
            password_hash=get_password_hash("Password123"),
            is_verified=True,
        )
        db_session.add(user_b)
        db_session.commit()
        db_session.refresh(user_b)

        access_a = create_access_token(
            subject=str(user_a.id),
            company_id=user_a.company_id,
            role=user_a.role,
        )
        headers_a = {"Authorization": f"Bearer {access_a}"}

        access_b = create_access_token(
            subject=str(user_b.id),
            company_id=user_b.company_id,
            role=user_b.role,
        )
        headers_b = {"Authorization": f"Bearer {access_b}"}

        # User A creates a journal entry in Company A
        response = client.post(
            "/api/v1/journals",
            headers=headers_a,
            json={
                "entry_date": "2026-10-26",
                "description": "Test JE for company A",
                "lines": [
                    {"account_id": str(acct_asset.id), "debit": "100.00", "credit": "0"},
                    {"account_id": str(acct_liab.id), "credit": "100.00", "debit": "0"},
                ],
            },
        )
        assert response.status_code == 200
        je_id = response.json()["id"]

        # User B from Company B should not be able to post it
        response = client.post(
            f"/api/v1/journals/{je_id}/post",
            headers=headers_b,
        )
        assert response.status_code == 404
