# FastAPI Calculator — Final Project

Capstone project for IS601 — a JWT-authenticated FastAPI application with full BREAD on calculations, an HTML/JS front-end, and a complete CI/CD pipeline that runs unit + integration + end-to-end tests against Postgres before pushing the Docker image to Docker Hub.

**Status:** 102 pytest passing · 33 Playwright passing · CI green · Docker image deployed

## Final-Project Additions

This project extends the Module 14 application with **two new features** to satisfy the final-project requirements:

### Feature A — Three Advanced Operations
On top of the existing Add / Subtract / Multiply / Divide, the calculator now supports:

| Operation | Formula | Validation |
|---|---|---|
| **Power** | `a ^ b` | Any operands (including fractional and negative `b`) |
| **Modulus** | `a mod b` | `b ≠ 0` |
| **Root** | `b`-th root of `a` (i.e. `a^(1/b)`) | `b ≠ 0`; if `b` is even, `a ≥ 0`. Odd roots of negatives are computed correctly via sign re-application (Python's `**` would otherwise return complex). |

All three are implemented as `Calculation` subclasses in the existing Factory pattern, surfaced through the same Pydantic schema, exposed in the dropdown UI, and validated identically client-side and server-side.

### Feature B — Stats Dashboard
A new `GET /calculations/stats` endpoint returns aggregate metrics scoped to the authenticated user:

```json
{
  "total": 5,
  "by_type": {"Add": 2, "Power": 1, "Modulus": 1, "Root": 1},
  "most_used_type": "Add",
  "avg_a": 10.0,
  "avg_b": 4.8,
  "avg_result": 207.8
}
```

Backed by a single SQL aggregation query (Postgres-side `func.avg()` and `GROUP BY`), so the work scales cleanly. Surfaced through a new `/stats` page with stat tiles and a horizontal bar chart for the per-type breakdown.

## Full Endpoint Reference

| Method | Path | Description |
|---|---|---|
| POST | `/users/register` | Create a new user |
| POST | `/users/login` | JSON login → JWT |
| POST | `/users/token` | OAuth2 form login (Swagger Authorize) |
| GET | `/users/me` | Current authenticated user |
| POST | `/calculations` | Create — returns 201 |
| GET | `/calculations` | Browse — caller's calculations |
| GET | `/calculations/stats` | **NEW** — aggregate stats |
| GET | `/calculations/{id}` | Read — 404 if not owner |
| PUT | `/calculations/{id}` | Edit — recomputes result |
| DELETE | `/calculations/{id}` | Delete — 204 No Content |

## Project Layout

```
app/
  main.py                    # FastAPI app + static mount + page routes (/, /register, /login, /dashboard, /stats)
  routers/
    users.py                 # /register /login /token /me
    calculations.py          # BREAD + /stats (route ordering matters)
  auth/
    hashing.py               # bcrypt
    jwt.py                   # JWT helpers + get_current_user
  schemas/
    user.py                  # UserCreate, UserLogin, UserRead, Token
    calculation.py           # CalculationCreate/Update/Read + CalculationStats (NEW)
  models/                    # SQLAlchemy User, Calculation
  operations/
    factory.py               # Add, Sub, Multiply, Divide, Power, Modulus, Root + CalculationFactory
static/
  index.html
  register.html
  login.html
  dashboard.html             # BREAD UI — dropdown includes new ops
  stats.html                 # NEW — stat tiles + bar chart
  css/style.css
  js/
    api.js                   # Shared fetch + JWT helper
    register.js
    login.js
    dashboard.js             # BREAD logic with client-side validation
    stats.js                 # NEW — fetches /calculations/stats and renders
e2e/
  package.json
  playwright.config.ts
  tests/
    register.spec.ts         # 5 tests
    login.spec.ts            # 6 tests
    calculations.spec.ts     # 12 tests
    stats.spec.ts            # 10 tests (NEW — final project)
tests/
  unit/                      # 35 tests, no DB required
    test_calculation_factory.py     # incl. Power/Modulus/Root logic
    test_calculation_schema.py      # incl. CalculationStats schema
    test_hashing.py
    test_schemas.py
  integration/               # 47 tests, real Postgres
    test_user_db.py
    test_user_routes.py
    test_calculation_db.py
    test_calculation_routes.py
    test_final_features.py          # NEW — new ops + /stats coverage
.github/workflows/ci.yml     # test → e2e → build-and-push (3-stage pipeline)
Dockerfile                   # Copies app/ + static/
docker-compose.yml
requirements.txt
.env.example
```

## Running Locally

### Docker Compose (fastest)

```bash
cp .env.example .env
# edit JWT_SECRET_KEY in .env
docker compose up --build
```

Visit http://localhost:8000.

### Manual (Python + Postgres container)

```bash
# Postgres
docker run -d --name fastapi-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fastapi_calc \
  -p 5432:5432 postgres:16
docker exec -i fastapi-pg psql -U postgres -c "CREATE DATABASE fastapi_calc_test;"

# App
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
uvicorn app.main:app --reload
```

## Running Tests

### pytest (102 tests)

```bash
pytest --cov=app --cov-report=term-missing -v
```

Splits as:
- 35 unit (no DB)
- 47 integration (Postgres)
- 102 total

### Playwright (33 tests)

In one terminal:
```bash
uvicorn app.main:app --reload
```

In a second:
```bash
cd e2e
npm install
npx playwright install --with-deps chromium   # one-time, ~200MB
npx playwright test                            # headless
npx playwright show-report                     # pretty HTML report
```

## Manual Walk-Through

1. Register → land on `/login`
2. Log in → `/dashboard`
3. Add a few calculations using the new operations:
   - `2 ^ 10` → `1024` via Power
   - `17 mod 5` → `2` via Modulus
   - `27` and `3` with Root → `3` (cube root)
4. Try the negative paths: edit a row, set type to Modulus, set `b` to `0` — UI blocks before any HTTP call.
5. Click **Stats** in the topbar → `/stats` shows total, most-used operation, averages, and a bar chart by type.

## Security Notes

- Passwords stored as bcrypt hashes — never plaintext
- JWTs signed with HS256 using `JWT_SECRET_KEY` from environment
- Row-level authorization on every calculation route — cross-user requests return `404` (don't leak existence)
- Stats endpoint is also user-scoped — User A cannot see User B's totals
- Client-side validation is decorative; server-side Pydantic validation is the real contract
- Trivy scan on every Docker image push

## Docker Hub

```bash
docker pull gxutxm7/fastapi-calculator:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/fastapi_calc \
  -e JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))") \
  gxutxm7/fastapi-calculator:latest
```

**Docker Hub:** https://hub.docker.com/r/gxutxm7/fastapi-calculator

## CI/CD

`.github/workflows/ci.yml` runs three jobs on every push to `main`:

1. **test** — pytest against Postgres 16 (102 tests, ~30s)
2. **e2e** — Playwright against a fresh Postgres + auto-started uvicorn (33 tests, ~2 min, uploads HTML report as workflow artifact)
3. **build-and-push** — only on `main`; builds, pushes `latest` + SHA-tagged image to Docker Hub, scans with Trivy

Required repo secret: `DOCKERHUB_TOKEN` (Docker Hub Access Token, Read/Write/Delete scope).

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | local Postgres | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | dev fallback | HS256 signing key (set per environment) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

Generate a real secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
