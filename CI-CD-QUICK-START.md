# CI/CD Quick Start Guide

## 🎯 Goal
Get a screenshot of working CI/CD pipeline in GitHub Actions.

---

## Step 1: Push Code to Trigger CI

```bash
# From the repo root
git add .
git commit -m "ci: configure CI/CD pipelines with tests"
git push origin new-implementation
```

---

## Step 2: Create Pull Request (Triggers CI)

1. Go to: https://github.com/milanziuziakowski/video-creator
2. Click **"Compare & pull request"** for `new-implementation` branch
3. Set base: `main`, compare: `new-implementation`
4. Create the PR

---

## Step 3: Watch CI Run

1. Go to **Actions** tab in GitHub
2. You'll see two workflows running:
   - **Backend CI** - Lint → Test → Build Docker
   - **Frontend CI** - Lint → E2E Tests → Build

---

## Step 4: Take Screenshot 📸

Screenshot should show:
- ✅ Both workflows (Backend CI + Frontend CI)
- ✅ Green checkmarks or running status
- ✅ Jobs breakdown (lint, test, build)

---

## What the Pipelines Do

### Backend CI (`backend-ci.yml`)
| Job | What it does |
|-----|--------------|
| **Lint** | Ruff linter + mypy type check |
| **Test** | `pytest tests/` with PostgreSQL |
| **Build** | Docker image build |

### Frontend CI (`frontend-ci.yml`)
| Job | What it does |
|-----|--------------|
| **Lint** | ESLint + TypeScript + Prettier |
| **Test** | Playwright E2E tests (`e2e/`) |
| **Build** | Vite production build |

---

## If Tests Fail

That's OK for the screenshot! The CI/CD **process** is working. Common reasons:
- E2E tests need running backend (expected)
- Lint errors in code (fixable)

The screenshot proves the pipeline runs: lint → test → build.

---

## Files Changed

```
.github/workflows/
├── backend-ci.yml   # Backend: lint, pytest, docker build
├── frontend-ci.yml  # Frontend: lint, playwright e2e, vite build
├── backend-cd.yml   # Backend deployment (CD)
└── frontend-cd.yml  # Frontend deployment (CD)
```

---

## Quick Verification Commands (Local)

```bash
# Backend tests
cd ai-video-creator-backend
pip install -e ".[dev]"
pytest tests/ -v

# Frontend E2E tests  
cd ai-video-creator-frontend
npm ci
npx playwright install chromium
npm run test:e2e
```
