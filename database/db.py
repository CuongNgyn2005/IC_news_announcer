import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


DB_PATH = Path("data") / "ic_watch.db"
JOB_REANNOUNCE_DAYS = 7


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


def _stable_job_identity(job):
    if not job:
        return None

    company = str(job.get("company", "") or "").strip().lower()
    title = str(job.get("title", "") or "").strip().lower()
    url = str(job.get("link", "") or "").strip()

    if not company or not title or not url:
        return None
    return company, title, url


def _find_job_row(conn, job_key, job=None):
    """Return the newest matching stored job row as ``(id, sent_at)``.

    The current key deliberately ignores derived metadata. The stable
    company/title/URL fallback also recognizes rows written by older parser
    versions whose key formula was different.
    """
    row = conn.execute(
        """
        SELECT id, sent_at
        FROM jobs
        WHERE job_key = ?
        ORDER BY datetime(sent_at) DESC, id DESC
        LIMIT 1
        """,
        (job_key,),
    ).fetchone()
    if row is not None:
        return row

    identity = _stable_job_identity(job)
    if identity is None:
        return None

    return conn.execute(
        """
        SELECT id, sent_at
        FROM jobs
        WHERE lower(trim(company)) = ?
          AND lower(trim(title)) = ?
          AND trim(COALESCE(url, '')) = ?
        ORDER BY datetime(sent_at) DESC, id DESC
        LIMIT 1
        """,
        identity,
    ).fetchone()


def _parse_sent_at(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text.replace(" ", "T", 1))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def job_in_quiet_period(job_key, job=None, quiet_days=JOB_REANNOUNCE_DAYS, now=None):
    """Return True while a previously announced job is inside its quiet window.

    Once ``quiet_days`` have elapsed since the last successful send/baseline,
    the same still-visible posting becomes eligible to be announced again.
    News behavior is intentionally separate and remains permanent one-time
    deduplication by article URL.
    """
    with get_connection() as conn:
        row = _find_job_row(conn, job_key, job)

    if row is None:
        return False

    sent_at = _parse_sent_at(row[1])
    if sent_at is None:
        return True

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)

    return current - sent_at < timedelta(days=quiet_days)


def job_exists(job_key, job=None):
    """Compatibility gate used by ``main.py`` for job announcements.

    Historically this meant "has ever been seen". It now means "is still in
    the seven-day quiet period" so a still-open posting may reappear after one
    week. Article deduplication is unchanged and remains one-time only.
    """
    return job_in_quiet_period(job_key, job)


def save_job(job):
    """Store a job send and refresh ``sent_at`` when it is re-announced.

    Updating the existing identity is essential for the seven-day lifecycle:
    every successful Telegram send starts a new quiet period. A stable identity
    fallback keeps legacy rows from being duplicated after parser/key changes.
    """
    with get_connection() as conn:
        row = _find_job_row(conn, job["job_key"], job)

        values = (
            job.get("link", ""),
            job["title"],
            job.get("company", ""),
            job.get("source", ""),
            job.get("location", ""),
            job.get("role", ""),
            job.get("posted", ""),
            job.get("job_score", 0),
        )

        if row is not None:
            conn.execute(
                """
                UPDATE jobs
                SET url = ?,
                    title = ?,
                    company = ?,
                    source = ?,
                    location = ?,
                    role = ?,
                    posted = ?,
                    score = ?,
                    sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*values, row[0]),
            )
            return

        conn.execute(
            """
            INSERT INTO jobs
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
            (job["job_key"], *values),
        )
