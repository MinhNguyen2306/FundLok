# FundLok — CI/CD & Deployment Pipeline Documentation

> Full reference for how code moves from a developer's machine to production:
> branches, GitHub Actions workflows, Cloud Run services, and every environment
> variable in each environment.
>
> Last updated: 2026-07-09 | Author: Phat | Source of truth: `.github/workflows/`, `Dockerfile`, `docker/entrypoint.sh`, `app/core/config.py`

---

## 1. High-Level Overview

FundLok's backend (FastAPI + PostgreSQL) is deployed to **Google Cloud Run** in
project **`fundlok`**, region **`asia-southeast1`** (Singapore). Deployment is
fully automated through **GitHub Actions** using source-based deploys — GitHub
never builds the container itself; Cloud Build builds the image from the repo
`Dockerfile` on Google's side.

There are four environments:

| Environment | Where it runs | Trigger | Workflow file |
|---|---|---|---|
| **Local development** | Developer machine (Docker Compose + host uvicorn) | manual (`bun run dev`) | n/a |
| **CI (test)** | GitHub Actions runners (ephemeral) | push / PR to `main` | `.github/workflows/ci.yml` |
| **Staging** | Cloud Run service **`staging`** | push to `dev` branch | `.github/workflows/Fundlok_staging_cloudrun.yml` (exists only on `dev` branch) |
| **Production** | Cloud Run service **`prod-api`** | push to `main` branch | `.github/workflows/deploy-prod.yml` |

### Branch flow

```
feature/<module>/<desc> ──PR──> preview ──merge──> main ──auto-deploy──> prod-api (Cloud Run)
                        └─PR──> dev ─────auto-deploy──> staging (Cloud Run)
```

- **`dev`** — staging integration branch. Every push auto-deploys to the `staging` Cloud Run service.
- **`preview`** — pre-production integration branch. Feature PRs are merged here first (see PRs #16–#18); it carries the same workflow files as `main` but pushing to `preview` does **not** trigger any deploy (both workflows trigger on `main` only).
- **`main`** — production. Every push triggers **both** the CI workflow and the production deploy workflow.

### Pipeline diagram

```mermaid
flowchart LR
    A[Developer push] -->|feature branch PR| B[preview branch]
    A -->|push to dev| S1

    subgraph "Staging (dev branch)"
        S1[Staging_DB workflow] --> S2[WIF auth to GCP]
        S2 --> S3[deploy-cloudrun v2: service 'staging']
    end

    B -->|merge| M[main branch]

    subgraph "Production (main branch)"
        M --> C1[Backend CI workflow]
        M --> D1[Deploy to Cloud Run workflow]
        C1 --> C2[migration-check job]
        C1 --> C3[tests job]
        D1 --> D2[WIF auth to GCP]
        D2 --> D3[deploy-cloudrun v2: service 'prod-api']
    end

    S3 --> R1[Cloud Build builds Dockerfile]
    D3 --> R1
    R1 --> R2["entrypoint.sh: alembic upgrade head"]
    R2 --> R3["uvicorn app.main:app on :8080"]
```

> ⚠️ Note: CI and the production deploy run **in parallel** — the deploy is
> **not** gated on tests passing. See [§8 Known Gaps](#8-known-gaps--risks).

---

## 2. Local Development Environment

Local infra is defined in `docker-compose.yml`; app config comes from `.env`
(copied from `.env.example`, gitignored). Day-to-day flow: `bun run dev`
(starts containers, then uvicorn with hot reload on host port 8000).

### Services (Docker Compose)

| Service | Image | Host port | Purpose |
|---|---|---|---|
| `postgres` | `postgres:16-alpine` | **5433** → 5432 | Dev database `fundlok_dev` (user/pass `fundlok`/`fundlok`); init script enables `pgcrypto` |
| `mailpit` | `axllent/mailpit` | 8025 (UI), 1025 (SMTP) | Local SMTP catcher for email flows |
| `minio` | `minio/minio` | 9000 (S3 API), 9001 (console) | Local stand-in for Cloudflare R2 (creds `minioadmin`/`minioadmin`) |
| `api` (optional) | built from `Dockerfile` | 8000 → 8080 | Prod-like containerized run (`bun run docker:up`); overrides `DATABASE_URL`/`SMTP_HOST` to resolve on the compose network |

### Local env vars (`.env`, from `.env.example`)

| Variable | Local value | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://fundlok:fundlok@localhost:5433/fundlok_dev` | App uses async driver; Alembic run by hand needs the `+psycopg2` form |
| `SECRET_KEY` | dev random string | JWT signing — generate with `openssl rand -hex 32` |
| `SMTP_HOST` / `SMTP_PORT` | `localhost` / `1025` | Points at Mailpit |
| `R2_ENDPOINT_URL` | `http://localhost:9000` | Points at MinIO |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | `minioadmin` / `minioadmin` | MinIO defaults |
| `DIDIT_*` | secrets empty in example | KYC secrets go only into gitignored `.env` |

---

## 3. CI — GitHub Actions Test Pipeline (`ci.yml`, "Backend CI")

**Trigger:** every push to `main` and every PR targeting `main`.
**Runner:** `ubuntu-latest`, Python **3.11** (pip-cached), with a
`postgres:15` service container (`test_user`/`test_password`/`test_db`,
health-checked with `pg_isready`).

Two independent jobs:

### Job 1 — `migration-check` ("Check Schema Migrations")

1. Checkout → set up Python 3.11 → `pip install -r requirements.txt`
2. `alembic upgrade head` — applies every migration to the empty test DB
3. `alembic check` — fails the build if the SQLAlchemy models contain changes
   without a corresponding migration script

Env: `DATABASE_URL=postgresql+psycopg2://test_user:test_password@localhost:5432/test_db`, `SECRET_KEY=dummy_secret_key_for_testing`, `DEBUG=True`.

### Job 2 — `tests` ("Run Test Suite")

Same setup, but `DATABASE_URL` is set **per step**, not per job, because the
two tools need different drivers (HANDOFF-02 Fix A):

1. `alembic upgrade head` with `postgresql+psycopg2://…` (sync driver)
2. `pytest -q` with `postgresql+asyncpg://…` (async driver, matches the app)

### CI env vars summary

| Variable | Value | Scope |
|---|---|---|
| `DATABASE_URL` | psycopg2 URL for Alembic steps, asyncpg URL for pytest step | per job / per step |
| `SECRET_KEY` | `dummy_secret_key_for_testing` | job |
| `DEBUG` | `True` | job |
| `POSTGRES_USER/PASSWORD/DB` | `test_user` / `test_password` / `test_db` | service container only |

> The `dev` branch has **no CI workflow** — pushes to `dev` deploy straight to
> staging without running tests (see §8).

---

## 4. Staging Deployment (`dev` branch → Cloud Run `staging`)

**Workflow:** `.github/workflows/Fundlok_staging_cloudrun.yml` ("Staging_DB") — this file exists **only on the `dev` branch**, not on `main`.
**Trigger:** every push to `dev`.

### Steps

1. **Checkout** (`actions/checkout@v4`, SHA-pinned)
2. **Authenticate to Google Cloud** via **Workload Identity Federation** — no
   long-lived JSON keys stored in GitHub:
   - Provider: `projects/1086381007504/locations/global/workloadIdentityPools/fundlok/providers/github`
   - Service account: `github-deploy@fundlok.iam.gserviceaccount.com`
   - GitHub job permissions: `contents: read`, `id-token: write`
3. **Deploy** with `google-github-actions/deploy-cloudrun@v2`:
   - `service: staging`, `region: asia-southeast1`, `project_id: fundlok`
   - `source: ./` — Cloud Build builds the repo `Dockerfile` remotely
   - Flag: `--add-cloudsql-instances fundlok:asia-southeast1:fundlok`
4. Print the deployed Cloud Run URL.

### Staging env vars injected by the workflow

| Variable | Source | Value |
|---|---|---|
| `DATABASE_URL` | GitHub secret `FUNLOK_DB` | staging Postgres connection string |
| `SECRET_KEY` | GitHub secret `FUNLOK_DB` | 🐛 **BUG — see §8: staging's JWT signing key is set to the database URL, not to `secrets.SECRET_KEY`** |

---

## 5. Production Deployment (`main` branch → Cloud Run `prod-api`)

**Workflow:** `.github/workflows/deploy-prod.yml` ("Deploy to Cloud Run from Source").
**Trigger:** every push to `main` (merge commits included). Runs **concurrently** with Backend CI — not gated on it.

### Steps

Identical mechanism to staging (same WIF provider, same deploy service
account, same region/project, same Cloud SQL flag), except:

- `service: prod-api`
- Workflow env vars injected:

| Variable | Source | Notes |
|---|---|---|
| `SECRET_KEY` | GitHub secret `SECRET_KEY` | JWT signing key |
| `DATABASE_URL` | **not set by the workflow** | Deliberately removed in commit `36ad182` (2026-07-07). `deploy-cloudrun@v2` *merges* `env_vars` with existing service configuration, so the `DATABASE_URL` already stored on the `prod-api` Cloud Run service persists across deploys. It is managed directly in the Cloud Run console/gcloud, not in GitHub. |

Per the README: if either `DATABASE_URL` or `SECRET_KEY` is missing on the
service, the app fails at import time and the container never listens — the
deploy fails visibly rather than serving a half-configured API.

### GitHub repository secrets in use

| Secret | Used by | Purpose |
|---|---|---|
| `SECRET_KEY` | prod deploy | Production JWT signing key |
| `FUNLOK_DB` | staging deploy (dev branch) | Staging DB connection string *(note the typo — "FUNLOK", not "FUNDLOK")* |

No service-account JSON key secret exists — auth is keyless via Workload Identity Federation.

---

## 6. Container Runtime (what actually runs on Cloud Run)

**`Dockerfile`:** `python:3.12-slim` → install `requirements.txt` → copy source
→ `ENV PORT=8080` → run `docker/entrypoint.sh`.

**`docker/entrypoint.sh`** does two things on every container start:

1. **Automatic DB migration:** `alembic upgrade head`. Idempotent (no-op at
   head), and Alembic takes a lock so parallel Cloud Run instance cold-starts
   are safe. This means *a deploy automatically brings the schema up to date* —
   no manual migration step in the pipeline.
2. **Start the API:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

**Driver-splitting logic:** the deployed `DATABASE_URL` secret can only name
one driver, but Alembic needs sync `psycopg2` and the app needs async
`asyncpg`. The entrypoint strips the driver and query string from whatever URL
is provided and rebuilds both forms:

- Alembic gets `postgresql+psycopg2://…?sslmode=require` (libpq params)
- The app gets `postgresql+asyncpg://…?ssl=require&prepared_statement_cache_size=0` (asyncpg params, pooler-safe)

> The entrypoint comment states the container "only ever connects to **Neon**"
> (SSL always required). The deploy workflows nonetheless still attach a Cloud
> SQL instance (`--add-cloudsql-instances fundlok:asia-southeast1:fundlok`) —
> see §8 for this discrepancy.

---

## 7. Complete Application Env Var Reference

All variables consumed by the app are declared in `app/core/config.py`
(pydantic-settings; reads process env first, then `.env`; unknown vars
ignored). **Required** = app crashes at import without it.

| Variable | Required | Default | Purpose | Local dev | CI | Staging | Production |
|---|---|---|---|---|---|---|---|
| `DATABASE_URL` | ✅ | — | Postgres connection | compose Postgres :5433 | ephemeral service container | secret `FUNLOK_DB` via workflow | set on Cloud Run service directly |
| `SECRET_KEY` | ✅ | — | JWT signing | dev string | dummy value | 🐛 wrong secret (`FUNLOK_DB`) | secret `SECRET_KEY` via workflow |
| `ALGORITHM` | | `HS256` | JWT algorithm | default | default | default | default |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `30` | Access-token TTL | default | default | default | default |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `14` | Refresh-token TTL (DB-backed revocation) | default | default | default | default |
| `GOOGLE_CLIENT_ID` | | `None` | Google OAuth | unset | unset | unset | unset* |
| `MICROSOFT_CLIENT_ID` / `MICROSOFT_TENANT_ID` | | `None` / `common` | Microsoft OAuth | unset | unset | unset | unset* |
| `FRONTEND_URL` | | `http://localhost:3000` | CORS / redirects / KYC callback base | default | default | *needs prod value** | *needs prod value** |
| `MOCK_UPLOAD_BASE_URL` | | mock URL | Legacy mock storage | example value | default | default | default |
| `CLOUDFLARE_TURNSTILE_SECRET_KEY` | | `None` | Bot protection (CAPTCHA) verify | placeholder | unset | unset* | unset* |
| `R2_ENDPOINT_URL` | | `None` | Cloudflare R2 endpoint | MinIO :9000 | unset | unset* | unset* |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | | `None` | R2 credentials | `minioadmin` | unset | unset* | unset* |
| `R2_BUCKET` / `R2_REGION` | | `fundlok-uploads` / `auto` | R2 bucket config | defaults | defaults | defaults | defaults |
| `R2_PRESIGN_EXPIRE_SECONDS` | | `900` | Presigned-URL TTL | default | default | default | default |
| `SMTP_HOST` / `SMTP_PORT` | | `localhost` / `1025` | Outbound email | Mailpit | unset | *needs prod SMTP** | *needs prod SMTP** |
| `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_SECURE` | | `None` / `None` / `False` | SMTP auth | empty | unset | unset* | unset* |
| `EMAILS_FROM_EMAIL` / `EMAILS_FROM_NAME` | | `noreply@fundlok.com` / `FundLok` | Email sender identity | defaults | defaults | defaults | defaults |
| `DIDIT_API_KEY` | | `None` | Didit KYC API key (`x-api-key`) | gitignored `.env` | unset | unset* | unset* |
| `DIDIT_WEBHOOK_SECRET` (alias `DIDIT_WEBHOOK_SECRET_KEY`) | | `None` | Webhook HMAC verification | gitignored `.env` | unset | unset* | unset* |
| `DIDIT_WORKFLOW_ID` / `DIDIT_KYB_WORKFLOW_ID` | | `None` | KYC (investor) / KYB (SME) workflow UUIDs | example has KYC id | unset | unset* | unset* |
| `DIDIT_BASE_URL` | | `https://verification.didit.me` | Didit API base | default | default | default | default |
| `DIDIT_CALLBACK_URL` | | `None` (→ `FRONTEND_URL/kyc/callback`) | Post-KYC redirect | default | default | default | default |
| `DIDIT_LANGUAGE` | | `vi` | Hosted KYC flow UI language | default | default | default | default |
| `PORT` | | `8080` (Dockerfile) | Uvicorn listen port | 8000 (host run) | n/a | Cloud Run injects | Cloud Run injects |

\* *"unset\*" / "needs prod value\*\*": the deploy workflows only inject
`DATABASE_URL`/`SECRET_KEY`. Any of these needed in staging/production
(R2, SMTP, Didit, Turnstile, OAuth client IDs, `FRONTEND_URL`) must be set
directly on the Cloud Run service (console or `gcloud run services update`)
— they persist across deploys because `deploy-cloudrun@v2` merges rather than
replaces env vars. Whether each is currently set can only be verified in the
Cloud Run console, not from the repo.*

---

## 8. Known Gaps & Risks

Items to be aware of (and candidates for the next infra iteration):

1. **🐛 Staging `SECRET_KEY` is set to the database URL.** In
   `Fundlok_staging_cloudrun.yml`, both `DATABASE_URL` and `SECRET_KEY` are
   assigned `${{ secrets.FUNLOK_DB }}`. Staging JWTs are therefore signed with
   the DB connection string. Fix: point `SECRET_KEY` at a dedicated staging
   secret.
2. **Production deploy is not gated on CI.** `ci.yml` and `deploy-prod.yml`
   both trigger on push to `main` and run in parallel — a commit with failing
   tests still deploys. Fix options: make the deploy job depend on the CI
   workflow (`workflow_run` or a single workflow with `needs:`), and/or a
   GitHub *environment* with required reviewers for `prod-api`.
3. **No tests before staging deploys.** The `dev` branch carries only the
   deploy workflow; `ci.yml` doesn't exist there and wouldn't trigger anyway
   (it filters on `main`). Pushes to `dev` go straight to staging untested.
4. **Cloud SQL flag vs. Neon.** Both deploys attach
   `fundlok:asia-southeast1:fundlok` (Cloud SQL), but `entrypoint.sh` is
   written for Neon ("this container only ever connects to Neon", SSL forced).
   One of the two is vestigial and should be removed/clarified.
5. **Python version drift.** CI tests on **3.11** (matching `runtime.txt` and
   CLAUDE.md), but the deployed container runs **3.12-slim**. Tests don't run
   on the interpreter production uses.
6. **Prod `DATABASE_URL` is invisible to the repo.** It lives only in the
   Cloud Run service config (by design, since commit `36ad182`), so there is
   no versioned record of it. Consider Google Secret Manager references
   (`--set-secrets`) for auditability.
7. **Secret name typo:** `FUNLOK_DB` (missing "D") — cosmetic, but a rename
   avoids confusion when adding more secrets.
8. **Migrations run on every container start.** Convenient and idempotent,
   but ties schema changes to deploy timing with no separate rollback step —
   acceptable now; revisit when the ledger goes live (append-only tables make
   down-migrations impossible anyway; corrections are reversing entries).
9. **Legacy files:** `Procfile` and `runtime.txt` are Heroku-era artifacts and
   are not used by the Cloud Run pipeline; `cloud-sql-proxy` binary (35 MB) is
   checked into the repo root.

---

## 9. Quick Reference — "What happens when I push?"

| Action | What runs | Result |
|---|---|---|
| Open PR → `main` | Backend CI (migration-check + tests) | Merge gate signal (if branch protection enabled) |
| Push/merge to `preview` | nothing | Integration branch only |
| Push/merge to `dev` | Staging_DB deploy | New revision of Cloud Run `staging`, migrations auto-applied |
| Push/merge to `main` | Backend CI **and** prod deploy (parallel) | New revision of Cloud Run `prod-api`, migrations auto-applied |
