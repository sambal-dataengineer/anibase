# AniBase — Setup Instructions

Complete step-by-step guide to running AniBase locally from scratch.

---

## Prerequisites

Make sure you have the following installed before starting:

- **Python 3.10+** — [python.org](https://python.org)
- **PostgreSQL 14+** — [postgresql.org](https://postgresql.org)
- **pgAdmin** (optional but recommended) — [pgadmin.org](https://pgadmin.org)
- **Git** — [git-scm.com](https://git-scm.com)

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/sambal-dataengineer/anibase.git
cd anibase
```

---

## Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, SQLAlchemy, psycopg2, passlib, python-jose, and all
other required packages.

---

## Step 4 — Create the PostgreSQL Database

Open pgAdmin or psql and run:

```sql
CREATE DATABASE anibase;
```

Note your PostgreSQL username (usually `postgres`) and password — you'll need
them in the next step.

---

## Step 5 — Create the .env File

Create a file named `.env` in the `anibase/` root directory (same level as
`requirements.txt`). Add the following:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/anibase
SECRET_KEY=your_generated_secret_key
ANILIST_URL=https://graphql.anilist.co
```

Replace `yourpassword` with your actual PostgreSQL password.

To generate a secure SECRET_KEY, run this in your terminal:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as your SECRET_KEY value.

> ⚠️ The `.env` file is in `.gitignore` and will never be committed. Never
> share this file publicly.

---

## Step 6 — Create Schemas and Tables

You need to run the SQL files in the correct order (foreign key dependencies).

Open pgAdmin's Query Tool connected to the `anibase` database, or use psql.
Run each file in this order:

**First — create all schemas:**

```sql
CREATE SCHEMA IF NOT EXISTS media;
CREATE SCHEMA IF NOT EXISTS metadata;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS characters;
CREATE SCHEMA IF NOT EXISTS external_links;
CREATE SCHEMA IF NOT EXISTS relations;
CREATE SCHEMA IF NOT EXISTS users;
```

**Then run each table file in order:**

```
db/tables/media.sql
db/tables/metadata.sql
db/tables/catalog.sql
db/tables/characters.sql
db/tables/external_links.sql
db/tables/relations.sql
db/tables/users.sql
```

**Verify all tables were created:**

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN (
    'media','metadata','catalog','characters',
    'external_links','relations','users'
)
ORDER BY table_schema, table_name;
```

You should see 15 tables

---

## Step 7 — Run the Data Ingestion

This fetches 10,000 titles from the AniList GraphQL API and populates all
14 tables.

```bash
python ingestion/ingestion.py
```

> ⏱️ **Expected time: 50–70 minutes.**
> The script fetches 200 pages (100 anime + 100 manga) at 50 items per page,
> with a 1-second delay between pages to respect AniList's rate limit.
> Do not close the terminal while it runs.

You will see live progress output like:

```
[ANIME] Fetching page 1/100...
  Got 50 items. Has next page: True
  ✓ Page 1 committed. | Fetched: 50 | Skipped: 0
```

**Verify ingestion completed:**

```sql
SELECT
    (SELECT COUNT(*) FROM media.media WHERE type = 'ANIME') AS anime,
    (SELECT COUNT(*) FROM media.media WHERE type = 'MANGA') AS manga,
    (SELECT COUNT(*) FROM media.media) AS total;
```

Expected: `anime: 5000, manga: 5000, total: 10000`

---

## Step 8 — Start the Backend Server

```bash
uvicorn app.main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## Step 9 — Open the App

Open your browser and go to:

```
http://localhost:8000
```

> ⚠️ Always use `http://localhost:8000`, never open HTML files directly
> via `file://` — the browser blocks fetch() requests from the file protocol.

---

## Step 10 — Verify Everything Works

- [ ] Homepage loads with trending anime and manga rows
- [ ] Browse page loads with genre sidebar
- [ ] Search returns results
- [ ] Detail page shows characters, relations, synopsis
- [ ] Register a new account
- [ ] Login works and username appears in navbar
- [ ] Add a title to a list
- [ ] Profile page shows stats and rank

---

## Swagger UI (API Explorer)

FastAPI auto-generates interactive API docs. With the server running, open:

```
http://localhost:8000/docs
```

All 18 endpoints are documented and testable directly from the browser.

---

## Common Issues

**`connection refused` on startup**
PostgreSQL is not running. Start the PostgreSQL service via pgAdmin or
Services on Windows.

**`relation does not exist`**
The SQL schema files were not run, or were run in the wrong order.
Re-run Step 6 carefully.

**`ModuleNotFoundError`**
Virtual environment is not activated. Run `venv\Scripts\activate` (Windows)
or `source venv/bin/activate` (Mac/Linux).

**Ingestion stops mid-way**
Re-run with a modified start page — edit `ingestion.py` temporarily:

```python
# In if __name__ == "__main__":
ingest("MANGA", start_page=51)  # resume from page 51
```

Also update the function signature: `def ingest(media_type: str, start_page: int = 1)`
And the loop: `for page in range(start_page, MAX_PAGES + 1)`

**`401 Unauthorized` on protected endpoints**
JWT has expired (30 min expiry). Log out and log back in.

---

## Project Structure Reference

```
anibase/
├── app/
│   ├── __init__.py
│   ├── main.py               ← FastAPI app, routers, StaticFiles mount
│   ├── database.py           ← SQLAlchemy engine + session
│   ├── auth/
│   │   ├── dependencies.py   ← get_current_user dependency
│   │   ├── hashing.py        ← bcrypt hash + verify
│   │   ├── jwt.py            ← token create + verify
│   │   ├── routes.py         ← POST /auth/register, POST /auth/login
│   │   └── schemas.py        ← RegisterRequest, LoginRequest, TokenResponse
│   ├── api/
│   │   ├── schemas.py
│   │   └── routes/
│   │       ├── characters.py
│   │       ├── lists.py      ← lists + list items CRUD
│   │       ├── media.py
│   │       ├── relations.py
│   │       └── users.py      ← profile, password, delete account
│   └── models/
│       └── media.py          ← all ORM models (14 tables)
├── db/
│   ├── schemas/
│   │   └── create_schemas.sql
│   └── tables/
│       ├── media.sql
│       ├── metadata.sql
│       ├── catalog.sql
│       ├── characters.sql
│       ├── external_links.sql
│       ├── relations.sql
│       └── users.sql
├── frontend/
│   ├── index.html            ← Homepage
│   ├── detail.html           ← Media detail page
│   ├── browse.html           ← Browse & filter
│   ├── search.html           ← Search results
│   ├── login.html            ← Auth (login + register)
│   ├── myspace.html          ← User lists
│   ├── profile.html          ← Profile & settings
│   └── 404.html              ← Error page
├── ingestion/
│   └── ingestion.py          ← GraphQL data pipeline (AniList → PostgreSQL)
├── .env                      ← Local secrets (not in repo)
├── .gitignore
├── LICENSE
├── Procfile                  ← Render deployment start command
├── project_summary.txt       ← Technical project overview
├── README.md
├── requirements.txt          ← Python dependencies
└── setup_instructions.md     ← Local setup guide
```
