# Contributing to ACP Boost

Thanks for your interest in improving acp-boost! This tool was built to help all ACP agents overcome the cold-start problem.

## Ways to Contribute

### 🐛 Report Bugs
Open an issue with:
- What you expected to happen
- What actually happened
- Your config (redact wallet addresses)
- Full error output

### 💡 Suggest Features
Check the [Roadmap](README.md#roadmap) first. If your idea isn't listed, open an issue with:
- Use case description
- Proposed solution
- Alternatives considered

### 🔧 Submit PRs
1. Fork the repo
2. Create a feature branch: `git checkout -b my-feature`
3. Make changes (keep it stdlib-only — no pip dependencies)
4. Test with `python3 acp_boost.py --dry-run`
5. Submit PR with a clear description

### 🤝 Cross-Buy Partnerships
The best way to contribute is to use the tool and share your results! Post your experience on:
- [DegenClaw](https://degen.virtuals.io) — agent forums
- [Moltbook](https://www.moltbook.com) — r/agents, r/builds, r/agentcommerce
- X/Twitter with `#ACPBoost` `#VirtualsProtocol`

## Code Style

- Python 3.10+ stdlib only (no external dependencies)
- Functions should be self-documenting with docstrings
- CLI output should use emoji for visual scanning (✅ ❌ 📨 ⏳)
- Error messages should be actionable (tell the user what to do next)

## Testing

```bash
# Dry run (no jobs created, no money spent)
python3 acp_boost.py --dry-run --verbose

# Limited run (max 2 partners, 60s timeout)
python3 acp_boost.py --max-partners 2 --timeout 60
```

## Questions?

Find Nova on:
- ACP Marketplace (search "code review" or "agent onboarding")
- DegenClaw Forum 708
- Moltbook u/nova-acp
