"""Integration tests for audit log."""
from __future__ import annotations


class TestAuditLogs:
    def test_list_audit_logs_requires_auth(self, client):
        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 401

    def test_list_audit_logs_returns_data(self, client, auth_headers):
        response = client.get("/api/v1/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
