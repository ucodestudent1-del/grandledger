"""Integration tests for bill CRUD operations."""
from __future__ import annotations

from uuid import uuid4


class TestBillCreate:
    def test_create_bill_requires_auth(self, client):
        response = client.post(
            "/api/v1/bills",
            json={
                "contact_id": str(uuid4()),
                "issue_date": "2026-10-26",
                "due_date": "2026-11-26",
                "lines": [
                    {
                        "description": "Test Expense",
                        "qty": "1",
                        "unit_price": "100.00",
                        "tax_rate": "0",
                        "account_id": str(uuid4()),
                    }
                ],
            },
        )
        assert response.status_code == 401


class TestBillList:
    def test_list_bills_requires_auth(self, client):
        response = client.get("/api/v1/bills")
        assert response.status_code == 401

    def test_list_bills_returns_data(self, client, auth_headers):
        response = client.get("/api/v1/bills", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestBillPost:
    def test_post_bill_requires_auth(self, client):
        response = client.post(
            "/api/v1/bills/00000000-0000-0000-0000-000000000000/post"
        )
        assert response.status_code == 401

    def test_post_bill_not_found(self, client, auth_headers):
        response = client.post(
            "/api/v1/bills/00000000-0000-0000-0000-000000000000/post",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestBillVoid:
    def test_void_bill_requires_auth(self, client):
        response = client.post(
            "/api/v1/bills/00000000-0000-0000-0000-000000000000/void"
        )
        assert response.status_code == 401

    def test_void_bill_not_found(self, client, auth_headers):
        response = client.post(
            "/api/v1/bills/00000000-0000-0000-0000-000000000000/void",
            headers=auth_headers,
        )
        assert response.status_code == 404
