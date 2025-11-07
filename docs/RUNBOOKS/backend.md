# Backend Runbook

## Overview
This runbook documents the actions required to bootstrap, operate, and troubleshoot the GW2Optimizer backend service in development and staging environments.

## Prerequisites
- Python 3.11 (managed through the project-local Poetry environment).
- Redis reachable at `settings.REDIS_URL` (default `redis://localhost:6379/0`).
- SQLite database (default) or Postgres if `REQUIRE_POSTGRES=true`.
- `.env` (or environment variables) providing FastAPI secrets and cookie configuration.

## Configuration
### Core environment variables
| Variable | Default | Description |
| --- | --- | --- |
| `BASE_URL_BACKEND` | `http://localhost:8000` | External URL used in generated links. |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | Frontend origins allowed by CORS; accepts JSON array or comma-separated list. |
| `COOKIE_DOMAIN` | _empty_ | Domain attribute for auth cookies. Leave unset for localhost. |
| `COOKIE_SECURE` | `false` | Set to `true` for HTTPS deployments. |
| `COOKIE_SAMESITE` | `lax` | One of `lax`, `strict`, or `none` (lower-case). |
| `COOKIE_MAX_AGE` | _empty_ | Overrides auth cookie TTL (seconds). Falls back to access token lifetime. |
| `DEFAULT_RATE_LIMIT` | `60/minute` | SlowAPI default rate limit applied when no per-endpoint override. |
| `LOGIN_RATE_LIMIT` | `50/minute` | Per-endpoint rate limit for login/token endpoints. |
| `REGISTRATION_RATE_LIMIT` | `10/hour` | Per-endpoint rate limit for account registration. |
| `PASSWORD_RECOVERY_RATE_LIMIT` | `5/hour` | Rate limit for password recovery endpoint. |

### Recommended dev values
```
ALLOWED_ORIGINS=["http://localhost:5173"]
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

## Bootstrapping
```bash
# 1. Install dependencies
cd backend
poetry install

# 2. Run migrations (if Postgres)
poetry run alembic upgrade head

# 3. Start the API
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Health checks
- `GET /health`
- `GET /api/v1/health`

## Operational tasks
- **Redis state**: ensure `REDIS_ENABLED=true` for token revocation. Toggle off via `.env` for local testing.
- **Learning scheduler**: automatically starts on app lifespan; inspect logs for `⏰ Learning pipeline scheduler activated`.
- **Rate limiting**: SlowAPI enforces rates using Redis when available. In tests (`PYTEST_CURRENT_TEST`), an in-memory bucket is used per test.

## Troubleshooting
| Symptom | Checks |
| --- | --- |
| `429 Too Many Requests` unexpectedly | Confirm bucket reset, inspect `DEFAULT_RATE_LIMIT` config, verify Redis availability. |
| Auth cookie missing | Ensure frontend origin is allowed, cookies not blocked (Secure + HTTPS mismatch), and path/domain align with expected host. |
| CORS blocked in browser | Inspect `ALLOWED_ORIGINS` normalization; values must include scheme and match frontend origin exactly. |
| Redis connection failures | Validate `REDIS_URL`, confirm service reachable, or set `REDIS_ENABLED=false` for fallback (tokens will not persist). |

## Testing
```bash
cd backend
poetry run pytest -q
poetry run ruff check
```

## References
- `backend/app/core/config.py` for configuration schema.
- `backend/app/api/auth.py` for auth cookie helpers and rate limiting.
- `docs/RUNBOOKS/ci.md` for CI workflow details.
