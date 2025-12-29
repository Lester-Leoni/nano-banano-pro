# Security Policy

## Supported versions

This repository does not currently publish signed releases. Until that exists, treat the `main` branch as the only supported version.

## Reporting a vulnerability

Please **do not** open a public issue for security reports.

Preferred: create a private GitHub Security Advisory.

If that is not possible, open an issue with the title prefix **[SECURITY]** and include only a high-level description (no exploit/PoC details). Leave a way to contact you for follow-up.

## Threat model (explicit)

Assumptions:
- The app may be reachable from the public internet.
- The app has **no built-in authentication/authorization**.
- Any user input (text and uploaded files) must be treated as untrusted.

Primary threats:
- Denial of service (large uploads, expensive parsing/processing)
- XSS/HTML injection (clipboard helpers, custom components)
- SSRF / untrusted network egress (translation calls, future integrations)
- Supply-chain risks (dependencies, Docker base images)

## Future SaaS threat model (design-level)

This project currently ships **no auth, no billing, no API keys**. The items below
are the primary threats once you add those capabilities.

### 1) API key leakage
- Surface: env/config, logs, UI error messages, client-side JavaScript, build artifacts
- Impact: unauthorized usage, unexpected cost, data exfiltration from upstream providers
- Mitigation class: secret managers, strict redaction, deny-by-default logging, short-lived keys, key-id vs key-material separation

### 2) Abuse / scraping / automated overuse
- Surface: unauthenticated endpoints/UI automation, replayed requests, shared leaked keys
- Impact: resource exhaustion, cost blowup, degraded service for legitimate users
- Mitigation class: tiered quotas, rate limits (burst + sustained), bot detection at gateway, request signing (future), WAF rules

### 3) Credential stuffing (future accounts)
- Surface: login forms, password reset, OAuth callbacks
- Impact: account takeover, billing fraud
- Mitigation class: delegated auth (SSO/OAuth), MFA, throttling, breached-password checks, anomaly detection

### 4) Replay attacks
- Surface: signed requests, payment/billing callbacks, idempotency gaps
- Impact: duplicated charges, quota bypass
- Mitigation class: nonces + timestamps, idempotency keys, short-lived tokens, server-side dedupe

### 5) Billing fraud
- Surface: metering pipeline, tier assignment, webhook handling, client-reported usage
- Impact: revenue loss, chargebacks, disputes
- Mitigation class: server-side metering, immutable audit logs, signature verification, reconciliation jobs

Non-goals:
- Multi-tenant isolation
- Handling regulated data

## Data handling & privacy

- Uploaded files are processed in-memory by Streamlit and are not intentionally persisted by this repository.
- If `deep-translator` is installed and Cyrillic text is present, the app may send text to a third-party translation backend (GoogleTranslator). Disable/remove `deep-translator` if external egress is not acceptable.
- The UI loads Google Fonts from a third-party CDN (network egress / privacy impact).

## Secure deployment recommendations

If you deploy this beyond personal/local use:
- Put it behind an auth gateway (reverse proxy with SSO, basic auth, VPN, etc.).
- Run it as a non-root user (the provided Dockerfile does this).
- Consider disabling external translation and other outbound network calls.
- Keep dependencies updated and monitor `pip-audit` output in CI.
