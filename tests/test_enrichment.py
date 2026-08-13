import unittest
from datetime import datetime, timezone

from collectors.job_details import extract_job_requirements
from filters.recency import is_recent_article
from summarizers.news_summary import NOT_STATED, summarize_text


class JobDetailExtractionTests(unittest.TestCase):
    def test_extracts_city_level_experience_and_english(self):
        text = (
            "Location: Ho Chi Minh City, Vietnam. "
            "Bachelor degree in Electrical Engineering is required. "
            "At least 3 years experience in SoC design verification using "
            "SystemVerilog and UVM. TOEIC score 750 or equivalent English "
            "proficiency is preferred."
        )

        result = extract_job_requirements(
            "Senior Design Verification Engineer",
            "Vietnam",
            text,
        )

        self.assertEqual(result["city"], "Ho Chi Minh City")
        self.assertEqual(result["seniority"], "Senior")
        self.assertIn("3 years", result["experience_requirement"])
        self.assertIn("TOEIC", result["english_requirement"])
        self.assertTrue(result["qualification_requirements"])

    def test_extracts_plus_years_without_word_experience(self):
        result = extract_job_requirements(
            "RTL Design Engineer",
            "Ho Chi Minh City, Vietnam",
            "Candidates should have 5+ years in RTL design, synthesis, and timing closure.",
        )
        self.assertIn("5+ years", result["experience_requirement"])
        self.assertIn("RTL design", result["experience_requirement"])

    def test_extracts_minimum_years_hands_on_requirement(self):
        result = extract_job_requirements(
            "Design Verification Engineer",
            "Da Nang, Vietnam",
            "Minimum 4 years of hands-on SystemVerilog and UVM verification is required.",
        )
        self.assertIn("Minimum 4 years", result["experience_requirement"])
        self.assertIn("UVM", result["experience_requirement"])

    def test_extracts_relevant_working_experience_wording(self):
        result = extract_job_requirements(
            "Physical Design Engineer",
            "Ho Chi Minh City, Vietnam",
            "Candidate must have at least 3 years of relevant working experience in physical design.",
        )
        self.assertIn("3 years", result["experience_requirement"])
        self.assertIn("working experience", result["experience_requirement"])

    def test_extracts_compact_year_range_from_job_title(self):
        result = extract_job_requirements(
            "RTL Design Engineer (3-5 yrs)",
            "Quy Nhon, Vietnam",
            "RTL Design Engineer (3-5 yrs)",
        )
        self.assertIn("3-5 yrs", result["experience_requirement"])

    def test_extracts_explicit_no_experience_requirement(self):
        result = extract_job_requirements(
            "Design Verification Trainee",
            "Ho Chi Minh City, Vietnam",
            "Fresh graduates are welcome. SystemVerilog knowledge is preferred.",
        )
        self.assertIn("Fresh graduates", result["experience_requirement"])

    def test_company_history_is_not_experience_requirement(self):
        result = extract_job_requirements(
            "Physical Design Engineer",
            "Hanoi, Vietnam",
            "Our semiconductor company celebrates 25 years of innovation worldwide.",
        )
        self.assertEqual(result["experience_requirement"], "Not stated")

    def test_preserves_multiple_vietnam_cities(self):
        result = extract_job_requirements(
            "Physical Design Engineer",
            "Ho Chi Minh City, Vietnam & Da Nang, Vietnam",
            "Physical design role available in Ho Chi Minh City and Da Nang.",
        )
        self.assertEqual(result["city"], "Ho Chi Minh City / Da Nang")

    def test_direct_listing_city_beats_other_offices_in_page_body(self):
        result = extract_job_requirements(
            "Staff Engineer Physical Design",
            "Ho Chi Minh City, Vietnam",
            "Global careers footer also lists Hanoi and Da Nang offices.",
        )
        self.assertEqual(result["city"], "Ho Chi Minh City")

    def test_missing_requirements_are_explicit(self):
        result = extract_job_requirements(
            "RTL Engineer",
            "Hanoi, Vietnam",
            "RTL Engineer based in Hanoi.",
        )

        self.assertEqual(result["city"], "Hanoi")
        self.assertEqual(result["experience_requirement"], "Not stated")
        self.assertEqual(result["english_requirement"], "Not stated")

    def test_title_seniority_beats_unrelated_body_words(self):
        result = extract_job_requirements(
            "Physical Design Engineer (Senior/Staff)",
            "Ho Chi Minh City, Vietnam",
            "We mentor graduate and junior engineers and work with managers.",
        )
        self.assertEqual(result["seniority"], "Senior / Staff")

    def test_experienced_title_is_not_mislabeled_junior(self):
        result = extract_job_requirements(
            "Design Verification Engineer (Experienced)",
            "Ho Chi Minh City, Vietnam",
            "Junior team members may also participate in the project.",
        )
        self.assertEqual(result["seniority"], "Experienced")


class NewsSummaryTests(unittest.TestCase):
    def test_extracts_supported_technical_metrics(self):
        text = (
            "The company introduced a new 2nm nanosheet architecture for AI "
            "data center processors. The design reduces power by 25% at the "
            "same frequency. Performance improves by 15% compared with the "
            "previous generation. The chip uses 3D hybrid bonding for its "
            "chiplet interconnect. The company will begin volume production "
            "in 2027. It is investing $10 billion in a new fabrication site."
        )

        summary = summarize_text(text)

        self.assertIn("2nm", summary["process_node"])
        self.assertIn("25%", summary["power"])
        self.assertIn("15%", summary["performance"])
        self.assertIn("hybrid bonding", summary["packaging"].lower())
        self.assertIn("$10 billion", summary["financial"])
        self.assertIn("volume production", summary["production"].lower())
        self.assertIn("data center", summary["use_case"].lower())

    def test_does_not_invent_missing_ppa_metrics(self):
        summary = summarize_text(
            "A new processor architecture targets cloud workloads."
        )

        self.assertEqual(summary["power"], NOT_STATED)
        self.assertEqual(summary["area_density"], NOT_STATED)


class NewsRecencyTests(unittest.TestCase):
    def test_rejects_old_dated_company_news(self):
        now = datetime(2026, 8, 12, tzinfo=timezone.utc)
        article = {"published": "2026-03-19"}
        self.assertFalse(is_recent_article(article, max_days=60, now=now))

    def test_accepts_recent_dated_news(self):
        now = datetime(2026, 8, 12, tzinfo=timezone.utc)
        article = {"published": "Jul 29, 2026"}
        self.assertTrue(is_recent_article(article, max_days=60, now=now))

    def test_undated_items_remain_eligible_for_persistent_dedupe(self):
        self.assertTrue(is_recent_article({"published": ""}))


if __name__ == "__main__":
    unittest.main()
