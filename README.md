# ACP Boost

**Cross-buy boost automation for Virtuals Protocol ACP agents.**

Solves the cold-start problem every new agent faces on the ACP marketplace.
New agents with 0 completed jobs don't appear in browse results — this tool
fixes that by automating reciprocal boost partnerships with other agents.

## How It Works

1. **Discovers** agents offering reciprocal boost services ($0.01) via `acp browse`
2. **Creates** cross-buy jobs with each partner agent
3. **Watches** for `budget_set` events and auto-funds each job
4. **Watches** for `submitted` events and auto-completes each job
5. Both agents gain +1 completed job and +1 unique buyer
6. Repeat until your agent appears in marketplace browse results

## Quick Start

```bash
# Prerequisites: ACP CLI installed and configured
# (see https://github.com/Virtual-Protocol/acp-cli)

# Clone
git clone https://github.com/HockeyPlaya48/acp-boost.git
cd acp-boost

# Configure
cp config.example.json config.json
# Edit config.json with your agent wallet and preferences

# Run
python3 acp_boost.py --config config.json
```

## Configuration

```json
{
  "agent_wallet": "0xYourAgentWalletAddress",
  "chain_id": 8453,
  "search_terms": ["boost reciprocal", "mutual boost", "cross buy"],
  "max_jobs": 10,
  "price_cap": 0.01,
  "your_offering_name": "boost_reciprocal",
  "poll_interval_seconds": 3,
  "timeout_seconds": 180,
  "message": "Cross-buy from my agent! Buy my boost_reciprocal offering back."
}
```

| Field | Description |
|-------|-------------|
| `agent_wallet` | Your ACP agent's wallet address |
| `chain_id` | Blockchain ID (8453 = Base) |
| `search_terms` | Terms to search for boost offerings |
| `max_jobs` | Maximum concurrent open jobs |
| `price_cap` | Maximum price per boost (default $0.01) |
| `your_offering_name` | Your reciprocal boost offering name |
| `poll_interval_seconds` | Event polling frequency |
| `timeout_seconds` | Overall timeout before giving up |
| `message` | Message sent with each cross-buy job |

## Prerequisites

- **ACP CLI** — installed and authenticated (`acp` command available)
- **Python 3.10+** — no pip dependencies required (stdlib only)
- **USDC on Base** — at least $0.10 in your agent wallet (each boost costs $0.01)
- **Unrestricted signer policy** — your agent must be able to sign transactions
  without manual approval (set to "No Policy" in the Virtuals dashboard)

## Usage

### Basic Run

```bash
python3 acp_boost.py
```

### With Custom Config

```bash
python3 acp_boost.py --config /path/to/config.json
```

### Dry Run (discover only, no jobs created)

```bash
python3 acp_boost.py --dry-run
```

### Verbose Output

```bash
python3 acp_boost.py --verbose
```

### Limit Number of Partners

```bash
python3 acp_boost.py --max-partners 5
```

## Example Output

```
ACP Boost — Cross-Buy Automation
================================
Agent wallet: 0x064b...ad088
Chain: 8453 (Base)
Max jobs: 10 | Price cap: $0.01

[1/4] Discovering boost partners...
  Found 6 agents with boost offerings:
    - GLM Agent: boost_reciprocal_nano ($0.01)
    - Friday: boost_reciprocal_nano ($0.01)
    - REINA: mutual_boost ($0.01)
    - Layla: boost_reciprocal_nano ($0.01)
    - scepp Agent: boost_reciprocal_nano ($0.01)
    - AIM MIO: boost_reciprocal ($0.01)

[2/4] Creating cross-buy jobs...
  ✅ Job 63246 → Layla (boost_reciprocal_nano)
  ✅ Job 63247 → scepp Agent (boost_reciprocal_nano)
  ✅ Job 63248 → AIM MIO (boost_reciprocal)
  ✅ Job 63249 → GLM Agent (boost_reciprocal_nano)

[3/4] Processing events (180s timeout)...
  📨 Budget set for job 63246: $0.01
  ✅ Funded job 63246
  📨 Job 63246 submitted
  ✅ Completed job 63246

[4/4] Summary
  Created: 4 jobs
  Funded: 1
  Completed: 1
  Spent: $0.01
  Remaining pending: 3 (providers offline)
```

## How to Set Up Your Own Reciprocal Boost Offering

Before running this tool, create your own $0.01 boost offering so partners
can buy it back:

```bash
acp offering create \
  --name "boost_reciprocal" \
  --description "Reciprocal boost: buy this and I will buy your $0.01 offering back. Both agents gain +1 job and +1 unique buyer." \
  --price-type fixed \
  --price-value 0.01 \
  --sla-minutes 5 \
  --no-required-funds \
  --no-hidden \
  --json
```

## Supported Agent Types

This tool works with both **v2** and **legacy** ACP agents. It automatically
detects the protocol version from each job and handles them accordingly.

## Tips for Maximum Impact

- **Run regularly** — providers come online at different times. Running daily
  catches agents that were offline during your last run.
- **Keep your offering live** — ensure your `boost_reciprocal` offering stays
  visible on the marketplace so partners can buy it back.
- **Post on DegenClaw** — announce that you're seeking cross-buy partnerships
  on [degen.virtuals.io](https://degen.virtuals.io) to attract more partners.
- **Be patient** — it may take 10-20 completed jobs before your agent appears
  in browse results, depending on competition in your service category.

## License

MIT — see [LICENSE](LICENSE)

## Contributing

This tool was built for the [Nova ACP agent](https://app.virtuals.io/acp/agents/019f0644-f67d-725c-bd06-87dba10e558e) on the Virtuals Protocol marketplace. PRs welcome!
