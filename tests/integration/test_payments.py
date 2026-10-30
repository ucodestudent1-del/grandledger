"""Integration tests for payment operations."""
from __future__ import annotations


class TestPaymentCreate:
    def test_create_payment_requires_auth(self, client):
        response = client.post(
            "/api/v1/payments",
            json={
                "contact_id": "00000000-0000-0000-0000-000000000000",
                "type": "receipt",
                "amount": "100.00",
                "payment_date": "2026-10-26",
            },
        )
        assert response.status_code == 401

    def test_list_payments_requires_auth(self, client):
        response = client.get("/api/v1/payments")
        assert response.status_code == 401

    def test_list_payments_returns_data(self, client, auth_headers):
        response = client.get("/api/v1/payments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
