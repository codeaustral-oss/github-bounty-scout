from unittest import TestCase

from src.bounty_scout import parse_issue_url, score_issue


class BountyScoutTests(TestCase):
    def test_parse_issue_url(self):
        ref = parse_issue_url("https://github.com/codeaustral-oss/example/issues/12")
        self.assertEqual(ref.owner, "codeaustral-oss")
        self.assertEqual(ref.repo, "example")
        self.assertEqual(ref.number, 12)

    def test_penalizes_closed_assigned_and_duplicate_work(self):
        issue = {
            "title": "Fix table sorting",
            "body": "Rows sort incorrectly after refresh.",
            "state": "closed",
            "assignees": [{"login": "maintainer"}],
            "labels": [{"name": "bug"}],
            "comments": 4,
            "updated_at": "2026-05-20T00:00:00Z",
        }
        score, reasons = score_issue(issue, related_pr_count=2)
        self.assertLess(score, 75)
        self.assertIn("issue is not open", reasons)
        self.assertIn("issue already has assignees", reasons)
        self.assertIn("2 related pull requests found", reasons)

    def test_penalizes_security_or_crypto_terms(self):
        issue = {
            "title": "Security roadmap for API keys",
            "body": "",
            "state": "open",
            "assignees": [],
            "labels": [{"name": "bug"}],
            "comments": 1,
            "updated_at": "2026-05-20T00:00:00Z",
        }
        score, reasons = score_issue(issue, related_pr_count=0)
        self.assertLess(score, 75)
        self.assertIn("issue matches excluded security or crypto terms", reasons)
