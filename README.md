# GitHub Bounty Scout

A small CLI for reviewing GitHub issue URLs before starting open-source bounty work.

It looks at basic public signals: issue state, assignees, labels, comment count, recent activity, and related pull requests. The score is not a guarantee; it is a fast way to decide whether a task deserves deeper review.

## Usage

```bash
python3 src/bounty_scout.py https://github.com/owner/repo/issues/123
```

Set `GITHUB_TOKEN` to increase GitHub API rate limits.

## Maintainer-Friendly Notes

- The tool favors avoiding duplicate work.
- It penalizes closed, assigned, stale, reserved, security, and crypto-related issues.
- It does not automate comments, claims, or pull requests.
