import unittest

from filters.ic_filter import is_ic_related
from filters.job_filter import classify_job


class ICFilterTests(unittest.TestCase):
    def test_ambiguous_rtl_does_not_self_prove_context(self):
        related, _, _ = is_ic_related({
            "title": "Detect Dark Matter's Mark From Your Backyard",
            "summary": "RTL appears in unrelated text.",
            "company": None,
        })
        self.assertFalse(related)

    def test_trusted_company_acquisition_is_rejected(self):
        related, _, _ = is_ic_related({
            "title": "SoftBank Group to Acquire Ampere Computing",
            "summary": "Ampere is a silicon design company.",
            "company": "Ampere Computing",
        })
        self.assertFalse(related)

    def test_ampere_product_is_accepted(self):
        related, _, _ = is_ic_related({
            "title": "AmpereOne M processor expands memory capacity",
            "summary": "New processor platform for servers.",
            "company": "Ampere Computing",
        })
        self.assertTrue(related)


class JobFilterTests(unittest.TestCase):
    def test_vietnam_design_verification_is_accepted(self):
        related, role, _, _ = classify_job({
            "title": "Design Verification Engineer",
            "company": "Marvell",
            "location": "Ho Chi Minh City, Vietnam",
            "country": "Vietnam",
            "context": "SystemVerilog UVM SoC verification",
        })
        self.assertTrue(related)
        self.assertEqual(role, "Design Verification")

    def test_mechanical_verification_is_rejected(self):
        related, _, _, _ = classify_job({
            "title": "Design Verification & Validation Engineer",
            "company": "HCLTech",
            "location": "Vietnam",
            "country": "Vietnam",
            "context": "Mechanical design Creo SolidWorks",
        })
        self.assertFalse(related)

    def test_physical_design_is_accepted(self):
        related, role, _, _ = classify_job({
            "title": "Senior Engineer Physical Design",
            "company": "Marvell",
            "location": "Ho Chi Minh City, Vietnam",
            "country": "Vietnam",
            "context": "ASIC place and route timing closure",
        })
        self.assertTrue(related)
        self.assertEqual(role, "Physical Design")

    def test_non_vietnam_job_is_rejected(self):
        related, _, _, _ = classify_job({
            "title": "SoC Verification Engineer",
            "company": "Marvell",
            "location": "Santa Clara, California",
            "country": "United States",
            "context": "UVM SystemVerilog",
            "assume_vietnam": False,
        })
        self.assertFalse(related)


if __name__ == "__main__":
    unittest.main()
