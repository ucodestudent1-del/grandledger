# SOC 2 Type II Compliance Checklist

GrandLedger is designed to support SOC 2 Type II compliance. This checklist maps Trust Services Criteria to implementation.

## Security (CC)

### CC6.1 — Logical and Physical Access Controls
- [x] Role-based access control (owner, accountant, bookkeeper, readonly)
- [x] Tenant isolation via `company_id` + PostgreSQL RLS policies
- [x] JWT access + rotating refresh tokens
- [x] httpOnly cookies with CSRF double-submit

### CC6.2 — Authentication
- [x] bcrypt password hashing (12 rounds)
- [x] JWT HS256 access tokens with expiry
- [x] Password complexity enforcement (8+ chars, upper/lower/digit)
- [x] Password reset via time-limited, single-use tokens
- [x] Email verification before login (production)

### CC7.1 — System Operations
- [x] Single posting function (`services/posting.py`) centralizes all GL writes
- [x] PostgreSQL trigger enforces debit/credit balance
- [x] Immutable ledger — posted lines never updated
- [x] Period locking prevents back-dated entries

### CC7.2 — Monitoring
- [x] Audit log for every ledger mutation (user, IP, timestamp, before/after)
- [x] Structured JSON logging (`src/core/logging.py`)
- [x] `/metrics` Prometheus endpoint
- [x] Enhanced `/health` with DB + Redis checks
- [x] Request ID tracing

### CC7.3 — Incident Response
- [x] `SECURITY.md` with vulnerability disclosure process
- [x] 48-hour acknowledgment SLA
- [x] Rate limiting on auth endpoints (SlowAPI)

### CC8.1 — Change Management
- [x] Alembic migrations for all schema changes
- [x] Code review via PR process
- [x] CI pipeline: lint + typecheck + test

## Availability (A)

### A1.2 — Availability
- [x] Docker healthchecks on all services
- [x] Automated daily backups with encryption
- [x] Backup retention: 7 days / 4 weeks / 12 months
- [x] Restore procedure documented (`scripts/db-restore.sh`)

## Confidentiality (C) — Optional Criteria

### C1.1 — Confidentiality
- [x] Tenant isolation prevents cross-company data access
- [x] Role-based permissions restrict sensitive operations
- [x] Audit trail logs all access to sensitive entities

## Remaining Items (Post-MVP)

| Item | Priority | Notes |
|------|----------|-------|
| External penetration test | High | Third-party security assessment |
| HSM / KMS key management | Medium | For encryption key storage |
| SIEM integration | Medium | Forward logs to Splunk/Datadog |
| Vendor security review | Low | Third-party processor due diligence |

## Evidence Available

- `src/core/middleware.py` — Tenant context + RBAC
- `src/core/security.py` — JWT + bcrypt
- `src/core/money.py` — Decimal-only validation
- `src/migrations/postgres/init.sql` — RLS policies
- `scripts/db-backup.sh` — Encrypted backups
- `web/app/audit/page.tsx` — Audit log viewer
