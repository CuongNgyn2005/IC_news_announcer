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

    def test_physical_verification_is_backend_not_functional_dv(self):
        related, role, _, _ = classify_job({
            "title": "Physical Verification Engineer (Chip Top)",
            "company": "BOS Semiconductors",
            "location": "Ho Chi Minh City, Vietnam",
            "context": "DRC LVS physical verification signoff",
        })
        self.assertTrue(related)
        self.assertEqual(role, "Physical Design")

    def test_non_vietnam_job_is_rejected_even_with_source_filter(self):
        related, _, _, _ = classify_job({
            "title": "SoC Verification Engineer",
            "company": "Marvell",
            "location": "Santa Clara, California",
            "country": "Vietnam",
            "context": "UVM SystemVerilog",
            "assume_vietnam": False,
        })
        self.assertFalse(related)

    def test_explicit_foreign_title_beats_vietnam_page_context(self):
        related, _, _, _ = classify_job({
            "title": "Staff Engineer Analog Layout Bucharest (Romania)",
            "company": "Infineon Technologies",
            "location": "Bucharest, Romania",
            "context": "Global career page also lists Hanoi, Vietnam roles.",
            "assume_vietnam": False,
        })
        self.assertFalse(related)

    def test_foreign_title_beats_polluted_derived_vietnam_location(self):
        related, _, _, _ = classify_job({
            "title": "Staff Engineer Analog Layout (f/m/div) Bucharest (Romania)",
            "company": "Infineon Technologies",
            "location": "Hanoi, Vietnam",
            "context": "Global career page also lists Hanoi, Vietnam roles.",
            "assume_vietnam": False,
        })
        self.assertFalse(related)

    def test_title_role_beats_unrelated_page_context(self):
        related, role, _, _ = classify_job({
            "title": "Custom Analog Design",
            "company": "FPT Semiconductor",
            "location": "Ho Chi Minh City, Vietnam",
            "context": (
                "Company services also include design verification, UVM, "
                "physical design and DFT."
            ),
        })
        self.assertTrue(related)
        self.assertEqual(role, "Analog / Custom Layout")

    def test_rtl_title_is_not_reclassified_as_dft_from_context(self):
        related, role, _, _ = classify_job({
            "title": "RTL Design Lead",
            "company": "FPT Semiconductor",
            "location": "Hanoi, Vietnam",
            "context": "Team provides DFT, ATPG and physical design services.",
        })
        self.assertTrue(related)
        self.assertEqual(role, "RTL / Logic Design")


if __name__ == "__main__":
    unittest.main()
