"""Integration tests for invoice CRUD operations."""
from __future__ import annotations


class TestInvoiceCreate:
    def test_create_invoice_requires_auth(self, client):
        response = client.post(
            "/api/v1/invoices",
            json={
                "contact_id": "00000000-0000-0000-0000-000000000000",
                "issue_date": "2026-10-26",
                "due_date": "2026-11-26",
                "lines": [
                    {
                        "description": "Test Service",
                        "qty": "1",
                        "unit_price": "100.00",
                        "tax_rate": "0",
                        "account_id": "00000000-0000-0000-0000-000000000000",
                    }
                ],
            },
        )
        assert response.status_code == 401


class TestInvoiceList:
    def test_list_invoices_requires_auth(self, client):
        response = client.get("/api/v1/invoices")
        assert response.status_code == 401

    def test_list_invoices_returns_data(self, client, auth_headers):
        response = client.get("/api/v1/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestInvoiceIssue:
    def test_issue_invoice_requires_auth(self, client):
        response = client.post(
            "/api/v1/invoices/00000000-0000-0000-0000-000000000000/issue"
        )
        assert response.status_code == 401

    def test_issue_invoice_not_found(self, client, auth_headers):
        response = client.post(
            "/api/v1/invoices/00000000-0000-0000-0000-000000000000/issue",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestInvoiceVoid:
    def test_void_invoice_requires_auth(self, client):
        response = client.post(
            "/api/v1/invoices/00000000-0000-0000-0000-000000000000/void"
        )
        assert response.status_code == 401

    def test_void_invoice_not_found(self, client, auth_headers):
        response = client.post(
            "/api/v1/invoices/00000000-0000-0000-0000-000000000000/void",
            headers=auth_headers,
        )
        assert response.status_code == 404
