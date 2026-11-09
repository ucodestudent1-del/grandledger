# GrandLedger Security Policy

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| 1.1.x   | ✅        | Current MVP release |
| < 1.1   | ❌        | Unsupported |

## Reporting a Vulnerability

Please disclose security vulnerabilities responsibly:

1. **Email:** security@grandledger.app (PGP key available on request)
2. **Include:** Steps to reproduce, impact assessment, affected versions
3. **Timeline:** We acknowledge reports within 48 hours and provide status updates weekly
4. **Scope:** GrandLedger API, web frontend, Docker images, and documentation

## Security Features

- **Authentication:** JWT access + rotating refresh tokens, bcrypt password hashing, httpOnly cookies with CSRF double-submit
- **Authorization:** Role-based access control (owner, accountant, bookkeeper, readonly), tenant-scoped data
- **Data Protection:** `numeric(20,4)` money columns, Decimal-only math, no floats
- **Immutable Ledger:** Posted journal lines never updated; corrections via reversal entries
- **Audit Trail:** Every ledger mutation logged (user, IP, timestamp, before/after JSON)
- **Transport Security:** TLS 1.2+, HSTS, security headers (nosniff, DENY, X-XSS-Protection)
- **Rate Limiting:** Per-IP + per-user limits on auth endpoints

## Patch Management

Security patches are released as part of regular version bumps. Critical patches may be released out-of-band.

## Acknowledgements

We thank security researchers who help us improve GrandLedger's security.
