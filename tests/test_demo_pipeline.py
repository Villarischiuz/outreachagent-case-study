import unittest

from src.demo_pipeline import Business, deduplicate, evaluate, normalize_domain, run_pipeline


class DemoPipelineTests(unittest.TestCase):
    def test_normalize_domain(self):
        self.assertEqual(normalize_domain("https://www.example.com/path"), "example.com")
        self.assertEqual(normalize_domain("example.com"), "example.com")
        self.assertIsNone(normalize_domain(None))

    def test_deduplicate_by_domain(self):
        records = [
            Business(1, "Alpha", "legal", "Salerno", "https://example.com"),
            Business(2, "Alpha duplicate", "legal", "Salerno", "https://www.example.com/contact"),
        ]
        self.assertEqual([record.id for record in deduplicate(records)], [1])

    def test_high_opportunity_reaches_human_review(self):
        record = Business(
            1,
            "Synthetic Studio",
            "legal",
            "Salerno",
            "https://slow-example.test",
            has_https=False,
            mobile_ready=False,
            load_time_ms=4_200,
            contact_available=True,
        )
        result = evaluate(record)
        self.assertEqual(result.state, "ready_for_review")
        self.assertEqual(result.score, 7)
        self.assertIn("slow measured load time", result.reasons)

    def test_social_profile_is_excluded(self):
        record = Business(1, "Social Only", "creative", "Naples", "https://instagram.com/example")
        result = evaluate(record)
        self.assertEqual(result.state, "excluded")
        self.assertEqual(result.score, 0)

    def test_pipeline_has_no_send_state(self):
        records = [Business(1, "No Site", "consulting", "Rome", None, contact_available=True)]
        states = {item.state for item in run_pipeline(records)}
        self.assertEqual(states, {"ready_for_review"})
        self.assertNotIn("sent", states)


if __name__ == "__main__":
    unittest.main()

