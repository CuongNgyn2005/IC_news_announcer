import unittest
from unittest.mock import patch

from collectors.jobs import (
    _parse_catalog_page,
    _parse_smartrecruiters_page,
    fetch_ttc_jobs,
)


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


class CatalogCollectorTests(unittest.TestCase):
    def test_parses_vietnam_table_role_and_link(self):
        html = """
        <table>
          <tr><th>Job Position</th><th>Description</th><th>Location</th></tr>
          <tr>
            <td>Design Verification Engineer</td>
            <td>UVM SystemVerilog, at least 2 years experience</td>
            <td>Ho Chi Minh, Vietnam</td>
            <td><a href="/career/design-verification/">Apply now</a></td>
          </tr>
        </table>
        """
        source = {
            "name": "Example",
            "company": "Example Semi",
            "url": "https://example.com/careers/",
            "default_location": "",
            "assume_vietnam": False,
        }

        jobs = _parse_catalog_page(html, source, source["url"])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Design Verification Engineer")
        self.assertEqual(jobs[0]["location"], "Ho Chi Minh City, Vietnam")
        self.assertEqual(
            jobs[0]["link"],
            "https://example.com/career/design-verification/",
        )

    def test_parses_static_qnsc_style_role_list(self):
        html = """
        <ul>
          <li>RTL Design Engineer (3-5 yrs)</li>
          <li>Verification Engineer (UVM / Formal)</li>
          <li>Marketing Specialist</li>
        </ul>
        """
        source = {
            "name": "QNSC",
            "company": "Quy Nhon Semiconductor",
            "url": "https://qnsc.vn/",
            "default_location": "Quy Nhon, Vietnam",
            "assume_vietnam": True,
            "detail_fetch": False,
        }

        jobs = _parse_catalog_page(html, source, source["url"])

        self.assertEqual(len(jobs), 2)
        self.assertTrue(
            all(job["location"] == "Quy Nhon, Vietnam" for job in jobs)
        )


class SmartRecruitersCollectorTests(unittest.TestCase):
    def test_preserves_vietnam_location_groups(self):
        html = """
        <h3>Ho Chi Minh City, Vietnam</h3>
        <a href="https://jobs.smartrecruiters.com/RenesasElectronics/123-staff-engineer">
          Staff Engineer, SoC Verification Full-time
        </a>
        <h3>Bengaluru, India</h3>
        <a href="https://jobs.smartrecruiters.com/RenesasElectronics/456-staff-engineer">
          Staff Engineer, Physical Design Full-time
        </a>
        """
        source = {
            "name": "Renesas Vietnam Careers",
            "company": "Renesas Electronics",
            "url": "https://careers.smartrecruiters.com/RenesasElectronics?search=Vietnam",
            "default_location": "",
            "assume_vietnam": False,
        }

        jobs = _parse_smartrecruiters_page(html, source, source["url"])

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Staff Engineer, SoC Verification")
        self.assertEqual(jobs[0]["location"], "Ho Chi Minh City, Vietnam")


if __name__ == "__main__":
    unittest.main()
