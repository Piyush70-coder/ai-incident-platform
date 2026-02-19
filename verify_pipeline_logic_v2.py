
import unittest
from incidents.services.ai_parser import parse_ai_output
from incidents.services.postmortem_service import generate_postmortem

class TestAIPipeline(unittest.TestCase):
    
    def test_parser_valid_output(self):
        text = """
        Root Cause: Redis Connection Refused
        Explanation: Log file indicates connection refused on port 6379.
        Confidence: 0.8
        """
        rc, expl, conf = parse_ai_output(text)
        self.assertEqual(rc, "Redis Connection Refused")
        self.assertEqual(conf, 0.8)

    def test_parser_placeholder_rejection(self):
        text = """
        Root Cause: <specific technical cause>
        Explanation: analysis in progress
        Confidence: 0.95
        """
        # Should trigger fallback. Since no keywords like redis/db are in there, 
        # it might fallback to "Application Performance Degradation"
        rc, expl, conf = parse_ai_output(text)
        self.assertNotEqual(rc, "<specific technical cause>")
        self.assertNotEqual(conf, 0.95) # Should be clamped to 0.85
        self.assertTrue(conf <= 0.85)
        self.assertTrue(conf >= 0.30)
        print(f"Placeholder fallback result: {rc}")

    def test_parser_keyword_fallback(self):
        text = """
        Root Cause: unknown
        Explanation: logs show redis timeout errors
        Confidence: 0.1
        """
        # "redis" is in text, so should infer Redis
        rc, expl, conf = parse_ai_output(text)
        self.assertIn("Redis", rc)
        self.assertEqual(conf, 0.30) # Clamped min

    def test_postmortem_generation(self):
        rc = "Redis Cache Connection Timeout"
        expl = "Connection refused on port 6379"
        report = generate_postmortem("context", rc, expl)
        
        self.assertIn("## Incident Postmortem", report)
        self.assertIn("circuit breakers", report.lower()) # Redis specific action
        self.assertNotIn("<specific technical cause>", report)

if __name__ == '__main__':
    unittest.main()
