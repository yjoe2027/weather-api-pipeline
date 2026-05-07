# GitHub Actions Weather Pipeline — Design Spec

**Date:** 2026-05-06
**Status:** Approved

## Overview

Schedule `weather.py` to run automatically once per day using GitHub Actions. Each run fetches a 7-day forecast for 20 US cities from weatherapi.com and commits the updated `weather_data.csv` back to `main`. Failures surface via GitHub's default email notifications.

## Trigger

- **Scheduled**: `cron: '0 6 * * *'` — 06:00 UTC daily
- **Manual**: `workflow_dispatch` — allows on-demand runs from the Actions UI

## Runner & Environment

- Runner: `ubuntu-latest`
- Python: 3.11 (pinned via `actions/setup-python@v5`)

## Workflow Steps

Single job — `fetch-and-commit` — runs the following steps in order:

1. **Checkout** — `actions/checkout@v4` with `fetch-depth: 0`
2. **Set up Python 3.11** — `actions/setup-python@v5`
3. **Install dependencies** — `pip install -r requirements.txt`
4. **Run pipeline** — `python weather.py` with `WEATHER_API_KEY` injected from a GitHub Secret
5. **Commit & push CSV** — commits `weather_data.csv` with message `chore: update weather_data.csv [skip ci]` only if the file changed; skips the commit if `git diff --quiet` reports no changes

## Secrets

- `WEATHER_API_KEY` must be added to the repo under **Settings → Secrets and variables → Actions**
- Injected as an environment variable; never printed to logs

## Error Handling

- **API errors**: `weather.py` will be updated to check `response.status_code`. If not 200, print the error body and call `sys.exit(1)`, causing the workflow run to fail and triggering GitHub's failure email.
- **No-change guard**: Use `git diff --quiet weather_data.csv` before committing. If no changes, skip the commit to avoid empty commits in history.
- **Failure notifications**: GitHub's built-in email notifications cover this — no additional configuration needed.

## Pre-flight Fix

`python-dotenv` is imported in `weather.py` but missing from `requirements.txt`. This must be added before the workflow will succeed in CI.

## Files Changed

| File | Change |
|------|--------|
| `.github/workflows/weather-pipeline.yml` | New — the Actions workflow |
| `requirements.txt` | Add `python-dotenv` |
| `weather.py` | Add `response.status_code` check with `sys.exit(1)` |

## What Is Not in Scope

- Appending historical data (each run overwrites the CSV)
- Uploading artifacts or pushing to external storage
- Slack/PagerDuty/webhook failure alerts
- Matrix runs across multiple Python versions
