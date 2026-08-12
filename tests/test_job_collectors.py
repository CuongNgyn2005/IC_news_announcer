import unittest
from unittest.mock import patch

from collectors.jobs import fetch_ttc_jobs


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class TTCJobCollectorTests(unittest.TestCase):
    def test_only_vietnam_rows_are_collected(self):
        payload = {
            "current_page": 1,
            "per_page": 3,
            "total_entries": 3,
            "entries": [
                {
                    "title": "Verification Engineer",
                    "location": "Ho Chi Minh City, SG, Vietnam",
                    "permalink": "/jobs/100-verification-engineer",
                },
                {
                    "title": "Design Implementation Engineer",
                    "location": "Ho Chi Minh City, SG, Vietnam",
                    "permalink": "/jobs/101-design-implementation-engineer",
                },
                {
                    "title": "SoC Verification Engineer",
                    "location": "Santa Clara, CA, United States",
                    "permalink": "/jobs/102-soc-verification-engineer",
                },
            ],
        }
        source = {
            "name": "Ampere Computing Vietnam Careers",
            "company": "Ampere Computing",
            "url": "https://careers.amperecomputing.com/",
            "json_url": (
                "https://careers.amperecomputing.com/"
                "search/jobs.json"
            ),
            "max_pages": 2,
        }

        with patch(
            "collectors.jobs._browser_get",
            return_value=DummyResponse(payload),
        ):
            jobs = fetch_ttc_jobs(source)

        self.assertEqual(len(jobs), 2)
        self.assertEqual(
            {job["title"] for job in jobs},
            {
                "Verification Engineer",
                "Design Implementation Engineer",
            },
        )
        self.assertTrue(
            all("Vietnam" in job["location"] for job in jobs)
        )
        self.assertTrue(
            all(job["assume_vietnam"] is False for job in jobs)
        )


if __name__ == "__main__":
    unittest.main()
