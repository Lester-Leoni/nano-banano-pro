# Contributing

Thanks for your interest in contributing!

## Project scope

NanoBanano Pro is intentionally small:
- Streamlit UI for prompt assembly (RU/EN) + negative prompt
- No backend, no user accounts, no analytics

Please avoid proposals that add features, change UX flows, or introduce heavy dependencies.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
streamlit run app.py
```

## Code quality

We use Ruff for linting:

```bash
ruff check .
```

## Security

- Read `SECURITY.md` for threat model and reporting.
- Do not introduce silent fallbacks for security-relevant behavior.
- Keep outbound network calls explicit and bounded (timeouts, size limits).

## Pull requests

- Keep diffs minimal.
- Include a short rationale in the PR description.
- Ensure CI is green.
