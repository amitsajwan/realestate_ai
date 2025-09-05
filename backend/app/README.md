# Modular App (Incremental Migration)

- Entry: `app/main.py`
- Templates: `templates/`
- Static: `static/`
- Routes included: `system`, `proxy`, `auth`, `leads`, `properties`
- Proxy target: `MODULAR_PROXY_TARGET` (defaults to `http://127.0.0.1:8004`)

Testing
- Unit tests: `tests/unit/test_modular_app.py`
- Run with: `pytest`

Runtime
- Start existing CRM (8004) via docker-compose to exercise proxy paths, or run modular app standalone for template checks.
