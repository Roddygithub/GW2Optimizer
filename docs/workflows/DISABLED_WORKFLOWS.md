# Disabled Workflows

## test_real_conditions.yml.disabled

**Status**: Disabled (kept for future use)

**Purpose**: Full E2E test with real Mistral AI API and GW2 API

**Why Disabled**:
- Requires API secrets (MISTRAL_API_KEY, GW2_API_KEY)
- Costs money on each run (Mistral API calls)
- Long execution time (~30 minutes)
- Not needed for every PR

**When to Re-enable**:
- Before major releases (v1.0, v2.0)
- Monthly scheduled runs
- When testing AI features specifically

**How to Re-enable**:
```bash
# 1. Add secrets to GitHub repo
# Settings > Secrets > Actions
# - MISTRAL_API_KEY
# - GW2_API_KEY

# 2. Rename workflow
mv .github/workflows/test_real_conditions.yml.disabled \
   .github/workflows/test_real_conditions.yml

# 3. Update schedule (optional)
# Edit cron: "0 4 * * *" to desired frequency
```

**Alternative**: Run manually via `workflow_dispatch` when needed

---

## security.yml.disabled

**Status**: REMOVED (2025-11-14)

**Reason**: Redundant with existing security tools
- CodeQL: Container scanning + code analysis
- Dependabot: Dependency vulnerability alerts
- CI: npm audit + pip-audit in test workflows

**Replacement**: CodeQL + Dependabot provide comprehensive coverage

---

## Recommendation

Keep `test_real_conditions.yml.disabled` for future use.
Enable only when:
1. Testing AI features
2. Before major releases
3. Monthly validation runs

Do not enable for every PR to avoid API costs.
