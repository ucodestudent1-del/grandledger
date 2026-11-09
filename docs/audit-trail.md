# Audit Trail & Compliance

## Overview

GrandLedger maintains an immutable, append-only audit trail for every ledger mutation. This document describes the audit architecture and how it supports SOC 2 Type II compliance.

## Immutable Ledger Design

### Core Principle

Posted journal lines are **never updated**. Corrections are made via reversing entries + new entries. This ensures the audit trail is inherent in the data, not a separate log that could be tampered with.

### Enforcement

1. **Application layer:** `services/posting.py` is the single authority for all GL writes. All Sales/Purchase/Payment features call `post_journal()` — never write `JournalLine` directly.
2. **Database layer:** A PostgreSQL trigger `enforce_balanced_entry()` validates `SUM(debits) = SUM(credits)` on every posted journal entry before commit.

## Audit Log

### Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | Tenant isolation (row-level) |
| `user_id` | UUID | User who performed the action |
| `action` | string | Action type (e.g., `journal_entry.create`) |
| `entity_type` | string | Type of entity mutated |
| `entity_id` | UUID | ID of the mutated entity |
| `before` | JSONB | State before mutation |
| `after` | JSONB | State after mutation |
| `ip_address` | string | Client IP address |
| `created_at` | timestamp | When the mutation occurred |

### Coverage

Audit entries are created for:
- Journal entry create / post / void / reverse
- Invoice create / issue / void / pay
- Bill create / post / void / pay
- Payment create / allocate
- Account create / update
- Contact create / update
- User invite / role change

## Tenant Isolation

Every tenant-scoped table has `company_id`. Middleware sets `SET LOCAL app.company_id` for PostgreSQL Row-Level Security (RLS). Policies in `src/migrations/postgres/init.sql` enforce:
- Users can only read/write their own company's data
- Cross-tenant queries return empty results

## Money Safety

- `Decimal` type in Python throughout
- `numeric(20,4)` in PostgreSQL
- Database check constraints: `ROUND(col::numeric, 4) = col` prevents float drift
- Runtime validation rejects `float` values at API boundaries

## Retention

Audit logs are retained indefinitely (no deletion). This supports:
- Historical financial reconstruction
- Auditor review
- Dispute resolution

## SOC 2 Mapping

| Control | Implementation |
|---------|---------------|
| CC6.1 Logical Access | JWT auth + RBAC + tenant isolation |
| CC6.2 Authentication | bcrypt + JWT access/refresh tokens |
| CC7.1 System Operations | Immutable ledger + DB triggers |
| CC7.2 Monitoring | Audit log + structured logging + `/metrics` |
| CC7.3 Incident Response | SECURITY.md disclosure process |
| CC8.1 Change Management | Alembic migrations + code review |
| A1.2 Availability | Docker healthchecks + automated backups |

## Backup & Recovery

- Automated daily backups via `scripts/db-backup.sh`
- Encrypted (AES-256-CBC + PBKDF2) with configurable key
- Retention: 7 days daily, 4 weeks weekly, 12 months monthly
- Restore via `scripts/db-restore.sh`

## Contact

Security questions: security@grandledger.app
