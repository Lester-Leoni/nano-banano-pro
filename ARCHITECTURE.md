# Architecture (future SaaS-ready)

This repository is a **Streamlit web-app**. Today it is a *single-tenant*, interactive UI with **no authentication** and **no billing**.

The goal of the `future_saas/` package is to provide **extension points** so adding SaaS features later does *not* require rewriting the app.

## Current execution model

- `app.py` is the entrypoint.
- Streamlit runs server-side Python and renders UI to the browser.
- There is no stable public Streamlit API for request headers; treat IP/UA attribution as **best-effort** until a gateway is introduced.

## Security boundaries

### Where secrets must live

**Allowed**:
- Environment variables (local/dev) — *short-lived secrets only*
- Cloud Secret Manager / Vault (prod)

**Forbidden**:
- In repo (code, config files, committed `.env`)
- In UI/session state
- In logs or error messages

`future_saas/secrets.py` provides a minimal interface (`SecretProvider`) and a simple `EnvSecretProvider` placeholder.

### Layers that must NOT see secrets

- Browser/UI
- Prompt templates / history
- Telemetry / usage events

Only the backend integration layer (future) should fetch secrets, and it must use **redaction** + **deny-by-default** logging.

## Identity + auth skeleton

Files:
- `future_saas/identity.py` — dataclasses for:
  - `UserIdentity` (interactive UI sessions)
  - `ApiClientIdentity` (future programmatic clients)
  - `SubscriptionTier` enum
- `future_saas/auth.py` — `AuthProvider` interface
- `future_saas/bootstrap.py` — selects auth provider (today: anonymous via `NoAuthProvider`)

**Design rule**: the rest of the app should only depend on `RequestContext`, never on raw headers/keys.

## Usage accounting skeleton

Files:
- `future_saas/usage.py` — `UsageEvent` + `UsageRecorder` interface
- `future_saas/limits.py` — `enforce_usage_limits(...)` hook (today: allow-all)

### What to count (design)

Prefer counting *cheap, stable units*:
- **per action** ("generate prompt")
- **per translated character** (if translation is enabled)
- (future) **per token** for LLM calls (when introduced)

### How to count (today)

`app.py` records one `GENERATE_PROMPT` usage event per run (metadata-only) and increments translation counters when translation is attempted.

### Where to store (future)

`UsageRecorder` implementations can later be added to ship events to:
- a database
- a queue
- a metering service

## Extension points checklist (6–12 months)

When you introduce SaaS features, add them by *replacing implementations*, not by rewriting UI logic:

1) Replace `NoAuthProvider` with a real `AuthProvider` (gateway verified JWT / API key identity)
2) Replace `NoopUsageRecorder` with a real backend
3) Implement `enforce_usage_limits` to deny on quota and return a user-friendly message
4) Ensure `public_error_message` stays **safe-by-default** (no secret leakage)
