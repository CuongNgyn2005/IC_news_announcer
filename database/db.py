import sqlite3
from pathlib import Path


DB_PATH = Path("data") / "ic_watch.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT,
                published TEXT,
                ic_score INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_key TEXT UNIQUE NOT NULL,
                url TEXT,
                title TEXT NOT NULL,
                company TEXT,
                source TEXT,
                location TEXT,
                role TEXT,
                posted TEXT,
                score INTEGER,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def article_exists(url):
    with get_connection() as conn:
        result = conn.execute(
            "SELECT 1 FROM articles WHERE url = ?",
            (url,),
        ).fetchone()
    return result is not None


def save_article(article):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO articles
            (url, title, source, published, ic_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                article["link"],
                article["title"],
                article["source"],
                article.get("published", ""),
                article.get("ic_score", 0),
            ),
        )


def job_exists(job_key, job=None):
    """Check exact key and a stable company/title/link identity.

    Location, seniority and role metadata can improve as parsers are fixed. The
    old job key included location, which could cause an already-announced role
    to be sent again after a location parser improvement. The stable identity
    fallback prevents that while still allowing two jobs with the same title
    when they have different posting URLs.
    """
    with get_connection() as conn:
        result = conn.execute(
            "SELECT 1 FROM jobs WHERE job_key = ?",
            (job_key,),
        ).fetchone()
        if result is not None or not job:
            return result is not None

        company = str(job.get("company", "") or "").strip().lower()
        title = str(job.get("title", "") or "").strip().lower()
        url = str(job.get("link", "") or "").strip()

        if not company or not title or not url:
            return False

        result = conn.execute(
            """
            SELECT 1 FROM jobs
            WHERE lower(trim(company)) = ?
              AND lower(trim(title)) = ?
              AND trim(COALESCE(url, '')) = ?
            LIMIT 1
            """,
            (company, title, url),
        ).fetchone()

    return result is not None


def save_job(job):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs
            (
                job_key,
                url,
                title,
                company,
                source,
                location,
                role,
                posted,
                score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job["job_key"],
                job.get("link", ""),
                job["title"],
                job.get("company", ""),
                job.get("source", ""),
                job.get("location", ""),
                job.get("role", ""),
                job.get("posted", ""),
                job.get("job_score", 0),
            ),
        )
