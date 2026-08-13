import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import database.db as db


class JobLifecycleTests(unittest.TestCase):
    def setUp(self):
        self._original_db_path = db.DB_PATH
        self._tempdir = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self._tempdir.name) / "ic_watch_test.db"
        db.initialize_database()

    def tearDown(self):
        db.DB_PATH = self._original_db_path
        self._tempdir.cleanup()

    @staticmethod
    def _job(job_key="job-key"):
        return {
            "job_key": job_key,
            "link": "https://example.com/jobs/123",
            "title": "Design Verification Engineer",
            "company": "Example Semiconductor",
            "source": "Example Careers",
            "location": "Ho Chi Minh City, Vietnam",
            "role": "Design Verification",
            "posted": "2026-08-13",
            "job_score": 20,
        }

    def _set_sent_at(self, timestamp):
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET sent_at = ?",
                (timestamp.strftime("%Y-%m-%d %H:%M:%S"),),
            )

    def test_job_is_quiet_for_first_seven_days(self):
        job = self._job()
        db.save_job(job)
        self.assertTrue(db.job_exists(job["job_key"], job))

        self._set_sent_at(datetime.now(timezone.utc) - timedelta(days=6, hours=23))
        self.assertTrue(db.job_exists(job["job_key"], job))

    def test_job_becomes_eligible_after_seven_days(self):
        job = self._job()
        db.save_job(job)
        self._set_sent_at(datetime.now(timezone.utc) - timedelta(days=7, minutes=1))

        self.assertFalse(db.job_exists(job["job_key"], job))

    def test_reannouncement_refreshes_quiet_period_without_duplicate_row(self):
        original = self._job("legacy-key")
        db.save_job(original)
        self._set_sent_at(datetime.now(timezone.utc) - timedelta(days=8))

        current = self._job("current-key")
        self.assertFalse(db.job_exists(current["job_key"], current))
        db.save_job(current)

        self.assertTrue(db.job_exists(current["job_key"], current))
        with db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        self.assertEqual(count, 1)

    def test_news_remains_permanent_one_time_dedupe(self):
        article = {
            "link": "https://example.com/news/chip",
            "title": "New chip architecture",
            "source": "Example News",
            "published": "2026-08-13",
            "ic_score": 10,
        }
        db.save_article(article)
        self.assertTrue(db.article_exists(article["link"]))


if __name__ == "__main__":
    unittest.main()
