"""Integration tests for banking operations."""
from __future__ import annotations


class TestBankAccounts:
    def test_list_bank_accounts_requires_auth(self, client):
        response = client.get("/api/v1/bank/accounts")
        assert response.status_code == 401

    def test_list_bank_accounts_returns_data(self, client, auth_headers):
        response = client.get("/api/v1/bank/accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestBankTransactions:
    def test_list_bank_transactions_requires_auth(self, client):
        response = client.get("/api/v1/bank/transactions")
        assert response.status_code == 401

    def test_list_bank_transactions_returns_data(self, client, auth_headers):
        response = client.get(
            "/api/v1/bank/transactions", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
