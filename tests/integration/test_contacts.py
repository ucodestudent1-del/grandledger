"""Integration tests for contact operations."""
from __future__ import annotations


class TestContactList:
    def test_list_contacts_requires_auth(self, client):
        response = client.get("/api/v1/contacts")
        assert response.status_code == 401

    def test_list_contacts_returns_data(self, client, auth_headers):
        response = client.get("/api/v1/contacts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_contact_requires_auth(self, client):
        response = client.post(
            "/api/v1/contacts",
            json={"name": "Test Customer", "type": "customer"},
        )
        assert response.status_code == 401

    def test_create_contact_returns_data(self, client, auth_headers):
        response = client.post(
            "/api/v1/contacts",
            json={"name": "Test Customer", "type": "customer"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Customer"
        assert data["type"] == "customer"
