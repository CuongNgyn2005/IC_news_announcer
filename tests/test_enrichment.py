import unittest

from collectors.job_details import extract_job_requirements
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

    def test_preserves_multiple_vietnam_cities(self):
        result = extract_job_requirements(
            "Physical Design Engineer",
            "Ho Chi Minh City, Vietnam & Da Nang, Vietnam",
            "Physical design role available in Ho Chi Minh City and Da Nang.",
        )

        self.assertEqual(result["city"], "Ho Chi Minh City / Da Nang")

    def test_missing_requirements_are_explicit(self):
        result = extract_job_requirements(
            "RTL Engineer",
            "Hanoi, Vietnam",
            "RTL Engineer based in Hanoi.",
        )

        self.assertEqual(result["city"], "Hanoi")
        self.assertEqual(result["experience_requirement"], "Not stated")
        self.assertEqual(result["english_requirement"], "Not stated")


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


if __name__ == "__main__":
    unittest.main()
