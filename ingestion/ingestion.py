"""
AniBase — ingestion.py
Fetches anime and manga data from the AniList GraphQL API
and inserts it into the anibase PostgreSQL database.

Learning goals:
- How to send GraphQL queries using the requests library
- How to handle paginated API responses
- How to insert data into multi-schema PostgreSQL (respecting FK order)
- How to use psycopg2 with ON CONFLICT for safe upserts
"""

import os
import time
import datetime
import requests
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

load_dotenv()

# psycopg2 needs a standard connection string, not SQLAlchemy's format.
# We parse the DATABASE_URL from your .env file.
DATABASE_URL = os.getenv("DATABASE_URL")

ANILIST_URL = os.getenv("ANILIST_URL")

# How many titles to fetch per page (AniList max = 50)
PER_PAGE = 50

# How many pages to fetch per run (50 pages × 50 per page = 2,500 titles)
# Start small (e.g. 2) for testing, increase later
MAX_PAGES = 100


# ─────────────────────────────────────────────
# GRAPHQL QUERY
# ─────────────────────────────────────────────

# This is the GraphQL query we send to AniList.
# It fetches all the fields we need for every table in anibase.
# $page and $perPage are variables — we pass different values each loop.
# $type is either "ANIME" or "MANGA"

MEDIA_QUERY = """
query ($page: Int, $perPage: Int, $type: MediaType) {
  Page(page: $page, perPage: $perPage) {
    pageInfo {
      hasNextPage
      currentPage
    }
    media(type: $type, sort: POPULARITY_DESC) {
      id
      title {
        romaji
        english
        native
      }
      type
      format
      status
      description(asHtml: false)
      episodes
      duration
      season
      seasonYear
      source
      chapters
      volumes
      startDate {year month day}
      endDate {year month day}
      nextAiringEpisode {
        airingAt
        episode
      }
      coverImage {
        large
      }
      bannerImage
      averageScore
      popularity
      trailer {
        id
        site
      }
      genres
      tags {
        id
        name
        rank
      }
      characters(sort: ROLE, perPage: 10) {
        edges {
          node {
            id
            name {
              full
              native
            }
            image {
              large
            }
          }
          role
        }
      }
      externalLinks {
        id
        url
        site
        type
        language
      }
      relations {
        edges {
          relationType
          node {
            id
          }
        }
      }
      recommendations(sort: RATING_DESC, perPage: 5) {
        edges {
          node {
            rating
            mediaRecommendation {
              id
            }
          }
        }
      }
    }
  }
}
"""


# ─────────────────────────────────────────────
# API FETCH
# ─────────────────────────────────────────────

def fetch_page(media_type: str, page: int) -> dict:
    """
    Sends one GraphQL request to AniList and returns the parsed JSON.

    How GraphQL over HTTP works:
    - Endpoint is always the same URL (not REST's different URLs per resource)
    - You POST a JSON body with two keys:
        "query"     → the GraphQL query string
        "variables" → a dict of variables the query uses ($page, $perPage, etc.)
    - The response is always JSON with a "data" key (and "errors" if something went wrong)
    """
    payload = {
        "query": MEDIA_QUERY,
        "variables": {
            "page": page,
            "perPage": PER_PAGE,
            "type": media_type,   # "ANIME" or "MANGA"
        }
    }

    response = requests.post(
        ANILIST_URL,
        json=payload,           # requests serialises the dict to JSON and sets Content-Type header
        headers={"Content-Type": "application/json"}
    )

    # AniList rate-limits to ~90 requests/min. If we get 429, wait and retry once.
    if response.status_code == 429:
        print("  Rate limited — waiting 60 seconds...")
        time.sleep(60)
        response = requests.post(ANILIST_URL, json=payload,
                                 headers={"Content-Type": "application/json"})

    response.raise_for_status()   # raises an exception for any other 4xx/5xx
    return response.json()


# ─────────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────────

def get_connection():
    """
    Opens a psycopg2 connection using the DATABASE_URL from .env.
    psycopg2 accepts the standard postgresql:// URI directly.
    """
    return psycopg2.connect(DATABASE_URL)


# ─────────────────────────────────────────────
# INSERT HELPERS
# Each function handles one table (or pair of tables for junctions).
# They all use ON CONFLICT DO NOTHING — safe to re-run without duplicates.
# ─────────────────────────────────────────────

def insert_media(cur, item: dict):
    cur.execute("""
        INSERT INTO media.media (
            id, title_romaji, title_english,
            type, format, status, cover_image_url,
            average_score, popularity
        ) VALUES (
            %(id)s, %(title_romaji)s, %(title_english)s,
            %(type)s, %(format)s, %(status)s, %(cover_image_url)s,
            %(average_score)s, %(popularity)s
        )
        ON CONFLICT (id) DO NOTHING
    """, {
        "id":             item["id"],
        "title_romaji":   item["title"]["romaji"],
        "title_english":  item["title"]["english"],
        "type":           item["type"],
        "format":         item.get("format"),
        "status":         item.get("status"),
        "cover_image_url": item["coverImage"]["large"] if item.get("coverImage") else None,
        "average_score":  item.get("averageScore"),
        "popularity":     item.get("popularity"),
    })


def insert_details(cur, item: dict):
    trailer_id = None
    if item.get("trailer"):
        trailer_id = item["trailer"].get("id")

    def build_date(d):
        if not d or not d.get("year"):
            return None
        return f"{d['year']}-{d.get('month') or 1:02d}-{d.get('day') or 1:02d}"
    
    next_airing_at = None
    next_airing_episode = None
    if item.get("nextAiringEpisode"):
        next_airing_at = datetime.datetime.fromtimestamp(
            item["nextAiringEpisode"]["airingAt"]
        )
        next_airing_episode = item["nextAiringEpisode"]["episode"]

    cur.execute("""
        INSERT INTO metadata.details (
            media_id, description, episodes, chapters, volumes, duration,
            season, season_year, source, trailer_id,
            start_date, end_date, next_airing_at, next_airing_episode
        ) VALUES (
            %(media_id)s, %(description)s, %(episodes)s, %(chapters)s, %(volumes)s, %(duration)s,
            %(season)s, %(season_year)s, %(source)s, %(trailer_id)s,
            %(start_date)s, %(end_date)s, %(next_airing_at)s, %(next_airing_episode)s
        )
       ON CONFLICT (media_id) DO UPDATE SET
            description         = EXCLUDED.description,
            episodes            = EXCLUDED.episodes,
            chapters            = EXCLUDED.chapters,
            volumes             = EXCLUDED.volumes,
            duration            = EXCLUDED.duration,
            season              = EXCLUDED.season,
            season_year         = EXCLUDED.season_year,
            source              = EXCLUDED.source,
            trailer_id          = EXCLUDED.trailer_id,
            start_date          = EXCLUDED.start_date,
            end_date            = EXCLUDED.end_date,
            next_airing_at      = EXCLUDED.next_airing_at,
            next_airing_episode = EXCLUDED.next_airing_episode
        """, {
        "media_id":             item["id"],
        "description":          item.get("description"),
        "episodes":             item.get("episodes"),
        "chapters":             item.get("chapters"),
        "volumes":              item.get("volumes"),
        "duration":             item.get("duration"),
        "season":               item.get("season"),
        "season_year":          item.get("seasonYear"),
        "source":               item.get("source"),
        "trailer_id":           trailer_id,
        "start_date":           build_date(item.get("startDate")),
        "end_date":             build_date(item.get("endDate")),
        "next_airing_at":       next_airing_at,
        "next_airing_episode":  next_airing_episode,
    })


def insert_genres(cur, item: dict):
    for genre_name in item.get("genres", []):
        cur.execute("""
            INSERT INTO catalog.genres (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (genre_name,))

        cur.execute("SELECT id FROM catalog.genres WHERE name = %s", (genre_name,))
        genre_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO catalog.media_genres (media_id, genre_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (item["id"], genre_id))


def insert_tags(cur, item: dict):
    # Your catalog.tags uses SERIAL id — insert by name, fetch back the generated id
    for tag in item.get("tags", []):
        cur.execute("""
            INSERT INTO catalog.tags (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (tag["name"],))

        cur.execute("SELECT id FROM catalog.tags WHERE name = %s", (tag["name"],))
        tag_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO catalog.media_tags (media_id, tag_id, tag_rank)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (item["id"], tag_id, tag.get("rank")))


def insert_characters(cur, item: dict):
    edges = item.get("characters", {}).get("edges", [])
    for edge in edges:
        char = edge.get("node")
        if not char:
            continue

        cur.execute("""
            INSERT INTO characters.characters (id, name_full, name_native, image_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            char["id"],
            char["name"]["full"] if char.get("name") else None,
            char["name"].get("native") if char.get("name") else None,
            char["image"]["large"] if char.get("image") else None,
        ))

        cur.execute("""
            INSERT INTO characters.media_characters (media_id, character_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (item["id"], char["id"], edge.get("role")))


def insert_external_links(cur, item: dict):
    # id is SERIAL — let PostgreSQL generate it, don't insert AniList's link id
    for link in item.get("externalLinks", []):
        cur.execute("""
            INSERT INTO external_links.links (media_id, url, site, type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (media_id, url) DO NOTHING
        """, (
            item["id"],
            link.get("url"),
            link.get("site"),
            link.get("type"),
        ))


def insert_relations(cur, item: dict):
    edges = item.get("relations", {}).get("edges", [])
    for edge in edges:
        related = edge.get("node")
        if not related:
            continue

        cur.execute("SELECT id FROM media.media WHERE id = %s", (related["id"],))
        if cur.fetchone() is None:
            continue

        cur.execute("""
            INSERT INTO relations.media_relations (media_id, related_media_id, relation_type)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (item["id"], related["id"], edge.get("relationType")))


def insert_recommendations(cur, item: dict):
    edges = item.get("recommendations", {}).get("edges", [])
    for edge in edges:
        node = edge.get("node", {})
        rec_media = node.get("mediaRecommendation")
        if not rec_media:
            continue

        cur.execute("SELECT id FROM media.media WHERE id = %s", (rec_media["id"],))
        if cur.fetchone() is None:
            continue

        cur.execute("""
            INSERT INTO relations.recommendations (media_id, recommended_media_id, rating)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (item["id"], rec_media["id"], node.get("rating")))

# ─────────────────────────────────────────────
# PROCESS ONE MEDIA ITEM
# ─────────────────────────────────────────────

def process_item(cur, item: dict):
    """
    Calls every insert function for one media item, in FK-safe order.
    All inserts share the same cursor (same open transaction).
    """
    insert_media(cur, item)
    insert_details(cur, item)
    insert_genres(cur, item)
    insert_tags(cur, item)
    insert_characters(cur, item)
    insert_external_links(cur, item)
    insert_relations(cur, item)
    insert_recommendations(cur, item)


# ─────────────────────────────────────────────
# MAIN INGESTION LOOP
# ─────────────────────────────────────────────

def ingest(media_type: str):
    """
    Fetches MAX_PAGES pages of the given media type from AniList
    and inserts everything into PostgreSQL.

    Commit strategy: one commit per item.
    If an item fails, only that item rolls back — everything else is safe.
    """
    print(f"\n{'='*50}")
    print(f"Starting ingestion: {media_type}")
    print(f"{'='*50}")

    conn = get_connection()

    try:
        total_skipped = 0
        total_fetched = 0
        for page in range(1, MAX_PAGES + 1):
            print(f"\n[{media_type}] Fetching page {page}/{MAX_PAGES}...")

            data = fetch_page(media_type, page)

            # Check for GraphQL errors (status 200 but errors in body)
            if "errors" in data:
                print(f"  GraphQL errors: {data['errors']}")
                break

            page_info  = data["data"]["Page"]["pageInfo"]
            media_list = data["data"]["Page"]["media"]

            print(f"  Got {len(media_list)} items. Has next page: {page_info['hasNextPage']}")

            page_skipped = 0
            for item in media_list:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            process_item(cur, item)
                except Exception as e:
                    print(f"  ⚠ Skipped media id={item.get('id')}: {e}")
                    conn = get_connection()
                    page_skipped += 1

            total_skipped += page_skipped
            total_fetched += len(media_list)

            print(f"  ✓ Page {page} committed. |   Fetched: {len(media_list)}  |   Skipped: {page_skipped}")

            # Respect AniList rate limit — 1 request/second is very safe
            if page_info["hasNextPage"] and page < MAX_PAGES:
                time.sleep(1)
            else:
                break

    finally:
        conn.close()

    print(f"\n✓ {media_type} ingestion complete.   |   Total fetched: {total_fetched}  |   Total skipped: {total_skipped}  |   Inserted: {total_fetched - total_skipped}")

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    ingest("ANIME")
    ingest("MANGA")
    print("\n✅ All done! Check your tables in pgAdmin.")