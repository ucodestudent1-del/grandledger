# GrandLedger Commercial Launch Implementation Plan

## Executive Summary

**Goal:** Make GrandLedger ready for commercial launch with paying customers.
**Timeline:** 8 weeks
**Scope:** Security hardening, payment infrastructure, legal compliance, monitoring, UX polish

---

## Phase A: Critical Blockers (Weeks 1-2)

### A1. Payment Infrastructure (Stripe Integration)
**Owner:** Backend + Frontend
**Deliverables:**
- Stripe account setup (test + production)
- Stripe Python SDK integration (`stripe` package)
- Subscription plans (Starter $29/mo, Professional $79/mo, Enterprise $199/mo)
- Checkout session creation endpoint (`POST /billing/checkout`)
- Stripe webhook endpoint (`POST /webhooks/stripe`) with signature verification
- Duplicate webhook protection (idempotency keys)
- Subscription entitlement enforcement middleware
- Customer portal management endpoint
- Failed payment handling (dunning emails, access suspension)
- Refund processing endpoint
- Pricing page (`/pricing`)
- Billing portal page (`/billing`)

**Verification:**
- Webhook signature verification tested with Stripe CLI
- Duplicate webhook idempotency tested
- Entitlement blocks access to premium features without active subscription
- Failed payment suspends account access after grace period

---

### A2. Security Hardening
**Owner:** Backend + Security
**Deliverables:**
- Move access/refresh tokens to httpOnly + Secure + SameSite=strict cookies
- Backend sets cookies instead of returning tokens in JSON
- Frontend reads cookies automatically (no localStorage for tokens)
- CSRF double-submit token implementation
- CSRF token cookie + X-CSRF-Token header validation
- Remove default SECRET_KEY (fail startup if not set in production)
- MFA (TOTP) for owner and accountant roles
- QR code setup and backup codes
- MFA enforcement for privileged operations

**Verification:**
- XSS cannot steal tokens (httpOnly cookies)
- CSRF attacks blocked (missing/invalid token rejected)
- Production fails to start with default SECRET_KEY
- MFA blocks login without valid TOTP code

---

### A3. Legal & Compliance
**Owner:** Product + Legal (external review)
**Deliverables:**
- Terms of Service (subscription terms, liability, termination)
- Privacy Policy (data collection, usage, sharing, retention)
- Cookie consent banner (GDPR/CCPA)
- Refund policy
- Subscription cancellation terms
- Data deletion endpoint (`DELETE /account/delete`)
- Data export endpoint (`GET /account/export`)
- Data retention policy documentation
- Contact/support page
- Professional legal review of all documents

**Verification:**
- Legal review sign-off on all documents
- Cookie consent banner blocks non-essential cookies until accepted
- Data deletion removes all customer PII and financial data
- Data export provides machine-readable customer data

---

## Phase B: High Priority (Weeks 3-4)

### B1. Monitoring & Observability
**Owner:** DevOps
**Deliverables:**
- Error monitoring (Sentry or Rollbar) with Python + JavaScript SDKs
- Uptime monitoring (ping endpoints, alert on downtime)
- Log aggregation (structured JSON logs shipped to centralized system)
- Application Performance Monitoring (APM) for slow queries
- Custom business metrics (registrations, activations, churn, MRR)
- Alerting (email/Slack on critical errors, downtime)

**Verification:**
- Errors captured and traceable to user sessions
- Downtime detected and alerted within 5 minutes
- Business metrics dashboard visible

### B2. Performance Optimization
**Owner:** Backend
**Deliverables:**
- Database indexes (company_id, entry_date, account_id, status)
- Redis caching for reports (P&L, BS, TB with TTL)
- Query result caching for frequently accessed reports
- Connection pool tuning for production (pool_size, max_overflow)
- CDN for static assets (Next.js export)
- Response compression (gzip/brotli)

**Verification:**
- Report API response < 200ms for cached, < 2s for uncached
- Database queries use indexes (EXPLAIN ANALYZE)
- Cache hit rate > 80% for reports

### B3. Data Integrity Fixes
**Owner:** Backend
**Deliverables:**
- Fix payment allocation double-count (already implemented)
- Prevent voiding invoices with payments (already implemented)
- Soft delete for companies (is_deleted flag)
- Transaction isolation level configuration (READ COMMITTED minimum)
- Audit trail for all data deletions

**Verification:**
- Allocation cannot exceed invoice total
- Paid invoices cannot be voided
- Deleted companies recoverable within 30 days

---

## Phase C: Medium Priority (Weeks 5-6)

### C1. UX & Customer Experience
**Owner:** Frontend
**Deliverables:**
- Empty states for all list views (no invoices, no journals, etc.)
- Onboarding flow (chart of accounts setup wizard)
- Frontend unit tests (Jest + React Testing Library)
- E2E tests (Playwright) for critical journeys
- Email retry mechanism (failed emails queued and retried)
- Email templates with company branding
- Domain authentication (SPF/DKIM/DMARC records)

**Verification:**
- E2E test: register → create invoice → send → view PDF passes
- Empty states displayed when no data
- Onboarding wizard completes chart of accounts setup

### C2. Additional Features
**Owner:** Full Team
**Deliverables:**
- Dark mode toggle
- Keyboard shortcuts (Cmd+K for search, etc.)
- Print-friendly report views
- Help center / documentation links
- Notification preferences settings

**Verification:**
- Dark mode persists across sessions
- Keyboard shortcuts functional
- Reports print correctly

---

## Phase D: Low Priority (Weeks 7-8)

### D1. Production Readiness
**Owner:** DevOps
**Deliverables:**
- Staging environment (mirror of production)
- Blue-green deployment strategy
- Rollback procedure documented and tested
- Secrets management (AWS Secrets Manager or HashiCorp Vault)
- WAF (Cloudflare or AWS WAF)
- DDoS protection
- Automated backup verification (restore test)

**Verification:**
- Staging deploy successful
- Rollback tested and documented
- Backup restore test passes
- WAF blocks common attacks (SQL injection, XSS)

### D2. Analytics & Business Metrics
**Owner:** Product
**Deliverables:**
- Registration funnel tracking
- Activation rate (users who create first invoice)
- MRR/ARR tracking
- Churn tracking (cancellations, downgrades)
- Feature adoption metrics
- Failed payment tracking
- Customer lifetime value estimation

**Verification:**
- Analytics dashboard shows real-time metrics
- Data respects user privacy and consent

---

## Implementation Schedule

| Week | Focus | Key Deliverables |
|------|-------|-----------------|
| 1 | Security + Payments | Stripe integration, cookie auth, CSRF protection |
| 2 | Legal + Compliance | ToS, Privacy Policy, data deletion/export |
| 3 | Monitoring | Sentry, uptime monitoring, business metrics |
| 4 | Performance | Indexes, Redis caching, connection tuning |
| 5 | UX | Empty states, onboarding, frontend tests |
| 6 | E2E | Playwright tests, email retry, branded templates |
| 7 | Production | Staging, WAF, secrets management, rollback |
| 8 | Polish | Dark mode, shortcuts, print reports, final QA |

---

## Resource Requirements

| Role | Allocation | Responsibilities |
|------|-----------|-----------------|
| Backend Engineer | 100% | Stripe integration, security hardening, APIs |
| Frontend Engineer | 100% | Cookie auth, UI, pricing page, billing portal |
| DevOps Engineer | 50% | Monitoring, staging, WAF, backups |
| Product Manager | 25% | Legal docs, pricing, analytics |
| Security Reviewer | External | Penetration test, compliance review |
| Legal Counsel | External | ToS, Privacy Policy review |

---

## Launch Readiness Checklist

### Pre-Launch Requirements
- [ ] Stripe integration tested in test mode
- [ ] Webhook signature verification working
- [ ] Cookie-based auth (no localStorage tokens)
- [ ] CSRF protection enabled
- [ ] SECRET_KEY not default value
- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] GDPR data deletion implemented
- [ ] Error monitoring (Sentry) configured
- [ ] Uptime monitoring configured
- [ ] Database indexes applied
- [ ] Redis caching for reports
- [ ] Staging environment operational
- [ ] Backup restore tested
- [ ] Frontend tests passing
- [ ] E2E tests passing
- [ ] Penetration test completed
- [ ] Legal review sign-off

### Go/No-Go Criteria
**GO if:**
- All critical blockers resolved
- 78+ backend tests passing
- Frontend tests passing
- E2E critical journey tests passing
- Security review passed
- Legal documents reviewed

**NO-GO if:**
- Payment system not functional
- Tokens in localStorage
- No CSRF protection
- Missing legal documents
- No error monitoring
- Security vulnerabilities unpatched

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stripe webhook delivery delays | Medium | High | Idempotency keys, retry logic |
| XSS vulnerability | Medium | Critical | httpOnly cookies, CSP headers |
| Data breach | Low | Critical | Encryption at rest, RLS, audit logs |
| Legal non-compliance | Medium | High | Professional legal review |
| Performance degradation | Medium | Medium | Indexes, caching, monitoring |
| Payment disputes | Low | Medium | Clear refund policy, evidence retention |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage (backend) | >80% | pytest coverage |
| Frontend tests | >50 components | Jest |
| E2E critical journeys | 5 | Playwright |
| Error rate | <1% | Sentry |
| Uptime | >99.9% | Uptime monitor |
| Report API response | <2s | APM |
| Security issues | 0 critical | Penetration test |

---

## Approval

This plan requires sign-off from:
- [ ] CTO / Principal Architect
- [ ] Security Lead
- [ ] Legal Counsel
- [ ] Product Manager

Once approved, implementation begins Week 1.