# AniBase 🎌

> A full-stack anime & manga discovery platform — think IMDb, but for anime and manga.

**🔗 Live Demo: [anibase-ayix.onrender.com](https://anibase-ayix.onrender.com)**

---

## Overview

AniBase lets users discover, browse, and track anime and manga across 10,000 titles sourced from the [AniList GraphQL API](https://graphql.anilist.co). It features a cinematic dark UI, a full authentication system, personal list management, and a Naruto-inspired rank progression system.

Built as a portfolio project to demonstrate full-stack data engineering skills — from data ingestion and database design to backend API development and frontend delivery.

---

## Features

- 🔍 **Browse & Search** — Filter by type, genre, and keyword with infinite scroll
- 🎬 **Media Detail Pages** — Synopsis, characters, relations, streaming/reading links
- 🔐 **Authentication** — JWT-based register/login system
- 📋 **Personal Lists** — Create lists, add/remove titles, manage your collection
- 🥷 **Rank System** — Naruto-inspired progression (Genin → Chunin → Jonin → Kage) based on unique titles tracked
- 📱 **Mobile Responsive** — Full mobile layout across all pages
- ⚡ **Loading Skeletons** — Shimmer placeholders on all data-heavy pages
- 🔗 **Streaming Links** — External links to watch/read sources (login required)

---

## Tech Stack

| Layer              | Technology                                                     |
| ------------------ | -------------------------------------------------------------- |
| **Data Ingestion** | Python, AniList GraphQL API, psycopg2                          |
| **Database**       | PostgreSQL — domain-based schema design (7 schemas, 14 tables) |
| **Backend**        | FastAPI, SQLAlchemy ORM                                        |
| **Authentication** | JWT (python-jose), bcrypt password hashing (passlib)           |
| **Frontend**       | HTML, CSS, Vanilla JavaScript — no frameworks                  |
| **Hosting**        | Render (app) + Neon (PostgreSQL)                               |

---

## Database Design

AniBase uses a **domain-based schema architecture** (deliberately contrasting with the medallion architecture used in my other projects), with 7 schemas and 14 tables:

```
media          → core media table (anime + manga)
metadata       → episode/chapter/season details
catalog        → genres, tags, junction tables
characters     → character profiles + media associations
external_links → streaming/reading URLs
relations      → related media + recommendations
users          → accounts, lists, list items
```

10,000 titles ingested (5,000 anime + 5,000 manga) sorted by popularity from AniList.

---

## Project Structure

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

---

## API Endpoints

### Public

| Method | Endpoint                      | Description                                               |
| ------ | ----------------------------- | --------------------------------------------------------- |
| GET    | `/media/`                     | List media with filters (type, genre, status, pagination) |
| GET    | `/media/search?q=`            | Search by title                                           |
| GET    | `/media/{id}`                 | Full media detail                                         |
| GET    | `/media/{id}/characters`      | Characters sorted by role                                 |
| GET    | `/media/{id}/relations`       | Related media                                             |
| GET    | `/media/{id}/recommendations` | Recommendations                                           |
| GET    | `/media/{id}/links`           | Streaming/reading links                                   |
| GET    | `/media/genres`               | All genres                                                |

### Auth

| Method | Endpoint         | Description                 |
| ------ | ---------------- | --------------------------- |
| POST   | `/auth/register` | Create account, returns JWT |
| POST   | `/auth/login`    | Login, returns JWT          |

### Protected (JWT required)

| Method   | Endpoint                       | Description           |
| -------- | ------------------------------ | --------------------- |
| GET      | `/users/me`                    | Profile + stats       |
| PUT      | `/users/me`                    | Update username/email |
| PUT      | `/users/me/password`           | Change password       |
| DELETE   | `/users/me`                    | Delete account        |
| GET/POST | `/lists/`                      | Get/create lists      |
| DELETE   | `/lists/{id}`                  | Delete list           |
| GET/POST | `/lists/{id}/items`            | Get/add items         |
| DELETE   | `/lists/{id}/items/{media_id}` | Remove item           |

---

## Running Locally

> **Note:** The database is not included in this repo. You'll need a local PostgreSQL instance and will need to run the ingestion script to populate data from the AniList API.

```bash
# Clone the repo
git clone https://github.com/sambal-dataengineer/anibase.git
cd anibase

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create a PostgreSQL database named 'anibase'
# Then create a .env file in the root:
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/anibase
SECRET_KEY=any_random_secret_string

# Create all schemas and tables by running the SQL files in order:
# db/tables/media.sql → metadata.sql → catalog.sql → characters.sql
# → external_links.sql → relations.sql → users.sql

# Populate the database (fetches from AniList API — takes ~1 hour)
python ingestion/ingestion.py

# Start the server
uvicorn app.main:app --reload
```

Open `http://localhost:8000`

---

## Other Portfolio Projects

| Project                                                                                     | Description                                                                 |
| ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| [cafe-sales-data-pipeline](https://github.com/sambal-dataengineer/cafe-sales-data-pipeline) | Bronze→Silver→Gold medallion pipeline + Power BI dashboard                  |
| [retail_sales_pipeline](https://github.com/sambal-dataengineer/retail_sales_pipeline)       | Retail sales pipeline, 9 Gold tables, XGBoost model, 5-page Power BI report |

---

## Author

**Sambal Agarwal** — Aspiring Data Engineer, Bengaluru

[![LinkedIn]](https://www.linkedin.com/in/sambal-agarwal-843a43339)
[![GitHub]](https://github.com/sambal-dataengineer)
