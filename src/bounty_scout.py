#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

ISSUE_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)/?$")
EXCLUDED_TERMS = ("security", "vulnerability", "cve", "crypto", "wallet", "smart contract")


@dataclass(frozen=True)
class IssueRef:
    owner: str
    repo: str
    number: int


def parse_issue_url(url: str) -> IssueRef:
    match = ISSUE_RE.match(url.strip())
    if not match:
        raise ValueError("expected a GitHub issue URL")
    owner, repo, number = match.groups()
    return IssueRef(owner=owner, repo=repo, number=int(number))


def api_get(path: str) -> Any:
    request = urllib.request.Request(f"https://api.github.com{path}")
    request.add_header("Accept", "application/vnd.github+json")
    if token := os.getenv("GITHUB_TOKEN"):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def days_since(value: str) -> int:
    updated = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - updated).days


def score_issue(issue: dict[str, Any], related_pr_count: int) -> tuple[int, list[str]]:
    score = 100
    reasons: list[str] = []
    text = " ".join(
        [
            str(issue.get("title", "")),
            str(issue.get("body", "")),
            " ".join(label["name"] for label in issue.get("labels", [])),
        ],
    ).lower()

    if issue.get("state") != "open":
        score -= 80
        reasons.append("issue is not open")
    if issue.get("assignees"):
        score -= 20
        reasons.append("issue already has assignees")
    if any(term in text for term in EXCLUDED_TERMS):
        score -= 50
        reasons.append("issue matches excluded security or crypto terms")
    if related_pr_count:
        score -= min(40, related_pr_count * 10)
        reasons.append(f"{related_pr_count} related pull requests found")
    if issue.get("comments", 0) > 30:
        score -= 15
        reasons.append("high-comment thread may be crowded")
    if days_since(issue["updated_at"]) > 30:
        score -= 20
        reasons.append("issue has not been updated recently")

    return max(score, 0), reasons


def search_related_prs(ref: IssueRef) -> int:
    query = f"repo:{ref.owner}/{ref.repo} {ref.number} type:pr"
    path = "/search/issues?" + urllib.parse.urlencode({"q": query, "per_page": "10"})
    result = api_get(path)
    return int(result.get("total_count", 0))


def scout(url: str) -> dict[str, Any]:
    ref = parse_issue_url(url)
    issue = api_get(f"/repos/{ref.owner}/{ref.repo}/issues/{ref.number}")
    related_pr_count = search_related_prs(ref)
    score, reasons = score_issue(issue, related_pr_count)
    return {
        "issue": issue["html_url"],
        "title": issue["title"],
        "state": issue["state"],
        "score": score,
        "related_pr_count": related_pr_count,
        "reasons": reasons,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: bounty_scout.py https://github.com/owner/repo/issues/123", file=sys.stderr)
        return 2
    print(json.dumps(scout(argv[1]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
