# CI Runbook

## Overview
This document captures the structure of the GitHub Actions CI pipeline for GW2Optimizer and provides guidance for relaunching or debugging jobs.

## Workflows
| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `ci.yml` | pull requests, pushes to `main` | Backend lint/tests, frontend lint/tests, CodeQL, E2E, Docker image build. |
| `docker-build-test.yml` | pull requests | Matrix build for Docker contexts. |
| `codeql.yml` | pull requests, schedule | Language-specific CodeQL analysis (Python, JavaScript/TypeScript). |
| `cleanup_purge.yml` | manual (`workflow_dispatch`) | Repo hygiene (branch/PR cleanup). |

## Key Jobs in `ci.yml`
- **Lint Workflows**: Runs `actionlint` + `shellcheck` on workflow files. Fix errors in `.github/workflows` and re-run via `gh workflow run ci.yml` or by pushing updates.
- **Lint Backend**: Executes `poetry run ruff check app scripts tests`. Ensure `.venv` cache not stale; run locally before pushing.
- **Lint Frontend**: Runs `npm run lint` under `frontend/`.
- **Backend Tests**: `poetry run pytest`. Uses SQLite by default; ensure fixtures cover auth for cookie assertions.
- **Frontend Unit Tests**: `npm test -- --runInBand` equivalent; relies on Vite env.
- **E2E Tests**: Playwright suite behind feature flag; installs browsers.
- **CodeQL**: Matrix for `python` and `javascript`. Requires `CODEQL_EXTRACTOR_*` config automatically handled by `github/codeql-action` v3.
- **Docker Build Image(s)**: Detects Dockerfile via `docker/**/Dockerfile`; respects detection script from workflow.

## Manual Triggers
```bash
# Re-run CI for latest commit on current branch
gh workflow run ci.yml --ref <branch>

# Re-run CodeQL only
gh workflow run codeql.yml --ref <branch>

# Inspect job logs
gh run view <run-id> --log
```

## Status Monitoring
- `gh pr checks <number> --watch` for live status.
- `gh run list --limit 10 --json status,name,headSha` to confirm queued/running runs.

## Troubleshooting
| Issue | Resolution |
| --- | --- |
| `actionlint`/`shellcheck` failure | Update workflow per lint output (use `gh run view <run-id> --log` for details). |
| Backend lint/test fail | Reproduce locally with `poetry run ruff check` or `poetry run pytest`. |
| Frontend failures | Ensure `npm install` executed; check Node version matrix. |
| Docker build skipped | Workflow detection returns `present=false`; confirm Dockerfile path. |
| CodeQL timeout | Re-run job, ensure dependencies install quickly, consider enabling `ramdisk` cache if repeated. |

## References
- `.github/workflows/ci.yml`
- `.github/workflows/docker-build-test.yml`
- `.github/workflows/codeql.yml`
- `docs/RUNBOOKS/backend.md`
