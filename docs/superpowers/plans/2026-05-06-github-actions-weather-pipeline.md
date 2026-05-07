# GitHub Actions Weather Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Schedule `weather.py` to run daily on GitHub Actions, committing the refreshed `weather_data.csv` back to `main` automatically.

**Architecture:** Three small, sequential changes — fix a missing dependency in `requirements.txt`, add a status-code guard to `weather.py`, and create the workflow YAML. No new abstractions; the script stays a single top-level file.

**Tech Stack:** Python 3.11, GitHub Actions (`actions/checkout@v4`, `actions/setup-python@v5`), `python-dotenv`, `requests`, `pandas`

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Modify | Declare `python-dotenv` so CI can install it |
| `weather.py` | Modify | Exit with code 1 on non-200 API response |
| `tests/test_weather_error_handling.py` | Create | Unit test for the new error-handling behavior |
| `.github/workflows/weather-pipeline.yml` | Create | Daily cron + manual trigger, runs script, commits CSV |

---

### Task 1: Fix missing dependency in requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add `python-dotenv` to requirements.txt**

Open `requirements.txt` and add this line (keep alphabetical order with the existing pins):

```
python-dotenv==1.1.0
```

The full file should look like:

```
certifi==2026.4.22
charset-normalizer==3.4.7
idna==3.13
numpy==2.4.4
pandas==3.0.2
python-dateutil==2.9.0.post0
python-dotenv==1.1.0
requests==2.33.1
six==1.17.0
urllib3==2.6.3
```

- [ ] **Step 2: Verify the install works cleanly**

Run from the project root (activate your venv first if needed):

```bash
pip install -r requirements.txt
```

Expected: all packages already satisfied or installed with no errors. If you see a version conflict for `python-dotenv`, run `pip show python-dotenv` to find the installed version and update the pin to match.

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "fix: add missing python-dotenv dependency"
```

---

### Task 2: Add API error handling to weather.py (TDD)

**Files:**
- Create: `tests/test_weather_error_handling.py`
- Modify: `weather.py`

- [ ] **Step 1: Create the tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_weather_error_handling.py` with this content:

```python
import sys
import unittest
from unittest.mock import patch, MagicMock
import runpy


class TestWeatherAPIErrorHandling(unittest.TestCase):
    def test_exits_on_non_200_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = '{"error": {"code": 2006, "message": "API key is invalid."}}'

        with patch('requests.get', return_value=mock_resp):
            with self.assertRaises(SystemExit) as cm:
                runpy.run_path('weather.py', run_name='__main__')

        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 3: Run the test to confirm it fails**

Run from the project root:

```bash
python -m unittest tests/test_weather_error_handling.py -v
```

Expected output (before implementation): the test will error — not with `SystemExit`, but with a `TypeError` because the unmocked script tries to iterate over a `MagicMock` object. This confirms the guard doesn't exist yet:

```
ERROR: test_exits_on_non_200_response (tests.test_weather_error_handling.TestWeatherAPIErrorHandling)
TypeError: 'MagicMock' object is not iterable
```

- [ ] **Step 4: Add the status-code guard to weather.py**

Add `import sys` to the imports at the top of `weather.py`. The top of the file should become:

```python
import os
import sys
import requests
import time
import pandas as pd
from dotenv import load_dotenv
```

Then, inside the `for zip_code in zip_codes:` loop, add the check immediately after `requests.get(...)`:

```python
    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f"API error for {zip_code} (HTTP {response.status_code}): {response.text}")
        sys.exit(1)
    data = response.json()
```

The full loop should now look like:

```python
for zip_code in zip_codes:
    params = {
        "key": api_key,
        "q": zip_code,
        "days": 7,
    }
    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(f"API error for {zip_code} (HTTP {response.status_code}): {response.text}")
        sys.exit(1)
    data = response.json()

    city = data["location"]["name"]
    region = data["location"]["region"]

    for day in data["forecast"]["forecastday"]:
        record = {
            "zip_code": zip_code,
            "city": city,
            "region": region,
            "date": day["date"],
            "max_temp_f": day["day"]["maxtemp_f"],
            "min_temp_f": day["day"]["mintemp_f"],
            "condition": day["day"]["condition"]["text"],
        }
        results.append(record)
        print(f"{city}, {region} | {record['date']}: {record['min_temp_f']}–{record['max_temp_f']}°F, {record['condition']}")

    time.sleep(1)
```

- [ ] **Step 5: Run the test to confirm it passes**

```bash
python -m unittest tests/test_weather_error_handling.py -v
```

Expected output:

```
test_exits_on_non_200_response (tests.test_weather_error_handling.TestWeatherAPIErrorHandling) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.XXXs

OK
```

- [ ] **Step 6: Commit**

```bash
git add weather.py tests/
git commit -m "feat: exit with code 1 on API error response"
```

---

### Task 3: Create the GitHub Actions workflow

**Files:**
- Create: `.github/workflows/weather-pipeline.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create `.github/workflows/weather-pipeline.yml`**

```yaml
name: Weather Pipeline

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

jobs:
  fetch-and-commit:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run pipeline
        env:
          WEATHER_API_KEY: ${{ secrets.WEATHER_API_KEY }}
        run: python weather.py

      - name: Commit and push CSV
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add weather_data.csv
          if ! git diff --staged --quiet; then
            git commit -m "chore: update weather_data.csv [skip ci]"
            git push
          else
            echo "No changes to weather_data.csv — skipping commit."
          fi
```

- [ ] **Step 3: Validate the YAML syntax**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/weather-pipeline.yml')); print('YAML valid')"
```

Expected output:

```
YAML valid
```

If you get `ModuleNotFoundError: No module named 'yaml'`, install it first: `pip install pyyaml`, then re-run.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/weather-pipeline.yml
git commit -m "feat: add daily GitHub Actions workflow for weather pipeline"
```

---

### Task 4: Configure the GitHub Secret and verify the workflow

**Files:** None — this is a manual configuration step in the GitHub UI.

- [ ] **Step 1: Push the branch to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Add the API key as a repository secret**

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `WEATHER_API_KEY`
5. Value: paste your key from `.env` (`ff3cd52bbdbb45d7a29175240261304`)
6. Click **Add secret**

- [ ] **Step 3: Trigger a manual run to verify end-to-end**

1. Go to your repository → **Actions** tab
2. Select **Weather Pipeline** from the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch the run — all steps should turn green
5. After it completes, check that a new commit appears on `main` authored by `github-actions[bot]` with message `chore: update weather_data.csv [skip ci]`

Expected: the run completes in under 2 minutes and `weather_data.csv` is updated in the repo.

- [ ] **Step 4: Verify failure notifications are wired up**

No action needed — GitHub sends failure emails to the repo owner by default whenever a workflow run fails. You can confirm your notification settings at [github.com/settings/notifications](https://github.com/settings/notifications).
