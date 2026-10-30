"""Integration tests for period locking feature."""
from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException

from src.services.posting import JournalLineData, post_journal


class TestPeriodLock:
    """Tests for company period lock endpoints."""

    def _signup(self, client, unique_suffix: str) -> dict:
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"period-{unique_suffix}@test.com",
                "name": "Period Test",
                "password": "Password123",
                "company_name": f"Period Company {unique_suffix}",
                "company_slug": f"period-comp-{unique_suffix}",
                "role": "owner",
            },
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_period_lock(self, client):
        headers = self._signup(client, "get-lock")
        companies = client.get("/api/v1/companies", headers=headers).json()
        company_id = companies[0]["id"]

        response = client.get(f"/api/v1/companies/{company_id}/period-lock", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "locked_period_end" in data
        assert data["locked_period_end"] is None

    def test_lock_period(self, client):
        headers = self._signup(client, "lock-set")
        companies = client.get("/api/v1/companies", headers=headers).json()
        company_id = companies[0]["id"]

        response = client.patch(
            f"/api/v1/companies/{company_id}/period-lock",
            headers=headers,
            json={"locked_period_end": "2026-06-30"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["locked_period_end"] == "2026-06-30"

    def test_unlock_period(self, client):
        headers = self._signup(client, "unlock")
        companies = client.get("/api/v1/companies", headers=headers).json()
        company_id = companies[0]["id"]

        client.patch(
            f"/api/v1/companies/{company_id}/period-lock",
            headers=headers,
            json={"locked_period_end": "2026-06-30"},
        )

        response = client.patch(
            f"/api/v1/companies/{company_id}/period-lock",
            headers=headers,
            json={"locked_period_end": None},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["locked_period_end"] is None

    def test_period_lock_requires_auth(self, client):
        response = client.get("/api/v1/companies/00000000-0000-0000-0000-000000000000/period-lock")
        assert response.status_code == 401

    def test_posting_to_locked_period_fails(self, test_company, test_user, test_accounts, db_session):
        """Ensure journal entries cannot be created in a locked period."""
        revenue_account = test_accounts[4]
        expense_account = test_accounts[5]

        test_company.locked_period_end = date(2026, 6, 30)
        db_session.add(test_company)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            post_journal(
                company_id=test_company.id,
                lines=[
                    JournalLineData(account_id=revenue_account.id, credit=100, debit=0),
                    JournalLineData(account_id=expense_account.id, debit=100, credit=0),
                ],
                description="Test entry in locked period",
                entry_date=date(2026, 6, 15),
                created_by=test_user.id,
            )
        assert exc_info.value.status_code == 400
        assert "locked" in exc_info.value.detail.lower()

        test_company.locked_period_end = None
        db_session.add(test_company)
        db_session.commit()

    def test_posting_to_unlocked_period_succeeds(self, test_company, test_user, test_accounts, db_session):
        """Ensure journal entries can be created after unlocking the period."""
        revenue_account = test_accounts[4]
        expense_account = test_accounts[5]

        test_company.locked_period_end = date(2026, 6, 30)
        db_session.add(test_company)
        db_session.commit()

        je = post_journal(
            company_id=test_company.id,
            lines=[
                JournalLineData(account_id=revenue_account.id, credit=100, debit=0),
                JournalLineData(account_id=expense_account.id, debit=100, credit=0),
            ],
            description="Test entry outside locked period",
            entry_date=date(2026, 7, 1),
            created_by=test_user.id,
        )
        assert je is not None
        assert je.status == "draft"

        test_company.locked_period_end = None
        db_session.add(test_company)
        db_session.commit()
