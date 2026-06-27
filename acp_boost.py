#!/usr/bin/env python3
"""
ACP Boost — Cross-buy boost automation for Virtuals Protocol ACP agents.

Discovers agents offering reciprocal boost services, creates $0.01 cross-buy
jobs, auto-funds them when budgets are set, and auto-completes them when
submitted. Solves the cold-start problem for new agents on the ACP marketplace.

Usage:
    python3 acp_boost.py [--config config.json] [--dry-run] [--verbose] [--max-partners N]
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "agent_wallet": "",
    "chain_id": 8453,
    "search_terms": ["boost reciprocal", "mutual boost", "cross buy"],
    "max_jobs": 10,
    "price_cap": 0.01,
    "your_offering_name": "boost_reciprocal",
    "poll_interval_seconds": 3,
    "timeout_seconds": 180,
    "events_file": "/tmp/acp_boost_events.jsonl",
    "message": "Cross-buy from my agent! Buy my boost_reciprocal offering back and we both gain.",
}

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def log(msg, verbose=False, level="INFO"):
    """Print a timestamped log message."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    prefix = f"[{ts}]"
    if level == "ERROR":
        prefix = f"[{ts}] ❌"
    elif level == "OK":
        prefix = f"[{ts}] ✅"
    elif level == "EVENT":
        prefix = f"[{ts}] 📨"
    elif level == "WAIT":
        prefix = f"[{ts}] ⏳"
    print(f"  {prefix} {msg}", file=sys.stderr)


def run_acp(*args, timeout=30):
    """Run an acp CLI command and return (success, parsed_json_or_raw_output)."""
    cmd = ["acp"] + list(args) + ["--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            return False, result.stderr.strip() or result.stdout.strip()
        try:
            return True, json.loads(result.stdout)
        except json.JSONDecodeError:
            return True, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError:
        return False, "acp CLI not found. Install it first."


# ---------------------------------------------------------------------------
# Phase 1: Discover boost partners
# ---------------------------------------------------------------------------

def discover_partners(config, verbose=False):
    """Browse the ACP marketplace for agents offering reciprocal boost services."""
    partners = []
    seen_wallets = set()
    my_wallet = config["agent_wallet"].lower()

    for term in config["search_terms"]:
        if verbose:
            log(f"Searching: '{term}'", verbose=True)

        ok, data = run_acp("browse", term, "--top-k", "10", timeout=30)
        if not ok or not isinstance(data, dict):
            if verbose:
                log(f"Search failed for '{term}': {data}", level="ERROR")
            continue

        agents = data.get("data", [])
        for agent in agents:
            wallet = agent.get("walletAddress", "").lower()
            if not wallet or wallet == my_wallet or wallet in seen_wallets:
                continue

            name = agent.get("name", "Unknown")
            offerings = agent.get("offerings", [])

            for offering in offerings:
                oname = offering.get("name", "").lower()
                price = float(offering.get("priceValue", 0))

                # Match boost/reciprocal offerings within price cap
                if any(kw in oname for kw in ["boost", "reciprocal", "mutual", "cross"]):
                    if price <= config["price_cap"]:
                        partners.append({
                            "name": name,
                            "wallet": agent["walletAddress"],
                            "offering_name": offering["name"],
                            "offering_id": offering.get("id", ""),
                            "price": price,
                        })
                        seen_wallets.add(wallet)
                        break  # One offering per agent

    return partners


# ---------------------------------------------------------------------------
# Phase 2: Create cross-buy jobs
# ---------------------------------------------------------------------------

def create_jobs(partners, config, dry_run=False, verbose=False):
    """Create cross-buy jobs with each partner agent."""
    jobs = []
    max_jobs = config["max_jobs"]

    for partner in partners:
        if len(jobs) >= max_jobs:
            log(f"Reached max_jobs limit ({max_jobs})", verbose=verbose)
            break

        if dry_run:
            log(f"[DRY RUN] Would create job → {partner['name']} ({partner['offering_name']})", verbose=verbose)
            jobs.append({"jobId": "dry-run", "partner": partner, "status": "dry-run"})
            continue

        # Build requirements payload
        requirements = json.dumps({
            "agent_wallet": config["agent_wallet"],
            "offering_name": config["your_offering_name"],
            "message": config["message"],
        })

        ok, data = run_acp(
            "client", "create-job",
            "--provider", partner["wallet"],
            "--offering-name", partner["offering_name"],
            "--requirements", requirements,
            "--chain-id", str(config["chain_id"]),
            timeout=30,
        )

        if ok and isinstance(data, dict) and data.get("success"):
            job_id = data.get("jobId", "?")
            jobs.append({"jobId": job_id, "partner": partner, "status": "created"})
            log(f"Job {job_id} → {partner['name']} ({partner['offering_name']})", level="OK")
        else:
            # Some agents use different requirement field names (e.g. "wallet" not "agent_wallet")
            requirements_alt = json.dumps({
                "wallet": config["agent_wallet"],
                "offering_name": config["your_offering_name"],
                "message": config["message"],
            })
            ok2, data2 = run_acp(
                "client", "create-job",
                "--provider", partner["wallet"],
                "--offering-name", partner["offering_name"],
                "--requirements", requirements_alt,
                "--chain-id", str(config["chain_id"]),
                timeout=30,
            )
            if ok2 and isinstance(data2, dict) and data2.get("success"):
                job_id = data2.get("jobId", "?")
                jobs.append({"jobId": job_id, "partner": partner, "status": "created"})
                log(f"Job {job_id} → {partner['name']} ({partner['offering_name']})", level="OK")
            else:
                err = data if isinstance(data, str) else data.get("error", str(data))
                log(f"Failed to create job for {partner['name']}: {err[:80]}", level="ERROR")

    return jobs


# ---------------------------------------------------------------------------
# Phase 3: Process events (fund + complete)
# ---------------------------------------------------------------------------

def process_events(jobs, config, verbose=False):
    """Watch for budget_set and submitted events, fund and complete jobs."""
    pending_ids = {j["jobId"] for j in jobs if j["status"] == "created"}
    funded = set()
    completed = set()
    total_spent = 0.0

    if not pending_ids:
        log("No jobs to process", verbose=verbose)
        return {"funded": 0, "completed": 0, "spent": 0.0, "remaining": 0}

    timeout = config["timeout_seconds"]
    interval = config["poll_interval_seconds"]
    start = time.time()
    max_iterations = timeout // interval

    for i in range(max_iterations):
        # Drain events
        ok, data = run_acp("events", "drain",
                          "--file", config["events_file"],
                          "--limit", "20",
                          timeout=15)

        if not ok or not isinstance(data, dict):
            time.sleep(interval)
            continue

        events = data.get("events", [])
        for event in events:
            job_id = str(event.get("jobId", ""))
            status = event.get("status", "")
            chain_id = event.get("chainId", config["chain_id"])

            if job_id not in pending_ids:
                continue

            # Budget set → fund the job
            if status == "budget_set" and job_id not in funded:
                amount = event.get("entry", {}).get("event", {}).get("amount", config["price_cap"])
                log(f"Budget set for job {job_id}: ${amount}", level="EVENT")
                ok, _ = run_acp("client", "fund",
                               "--job-id", job_id,
                               "--amount", str(amount),
                               "--chain-id", str(chain_id),
                               timeout=120)
                if ok:
                    funded.add(job_id)
                    total_spent += float(amount)
                    log(f"Funded job {job_id} (${amount})", level="OK")
                else:
                    log(f"Fund failed for job {job_id}", level="ERROR")

            # Submitted → complete the job
            elif status == "submitted" and job_id in funded and job_id not in completed:
                log(f"Job {job_id} submitted by provider", level="EVENT")
                ok, _ = run_acp("client", "complete",
                               "--job-id", job_id,
                               "--chain-id", str(chain_id),
                               "--reason", "Thanks for the cross-buy boost partnership!",
                               timeout=120)
                if ok:
                    completed.add(job_id)
                    log(f"Completed job {job_id}", level="OK")
                else:
                    log(f"Complete failed for job {job_id}", level="ERROR")

            # Already completed
            elif status == "completed" and job_id in pending_ids:
                completed.add(job_id)
                log(f"Job {job_id} confirmed completed", level="OK")

        # Check if all done
        remaining = pending_ids - completed
        if not remaining:
            log("All jobs completed!", level="OK")
            break

        if verbose and i % 10 == 0:
            log(f"Waiting... {len(remaining)} jobs pending ({i*interval}s elapsed)", level="WAIT")

        time.sleep(interval)

    return {
        "funded": len(funded),
        "completed": len(completed),
        "spent": round(total_spent, 4),
        "remaining": len(pending_ids - completed),
    }


# ---------------------------------------------------------------------------
# Phase 4: Summary
# ---------------------------------------------------------------------------

def print_summary(jobs, result, config):
    """Print a final summary of the boost run."""
    print("\n" + "=" * 50)
    print("ACP Boost — Summary")
    print("=" * 50)
    print(f"  Jobs created:  {len(jobs)}")
    print(f"  Funded:        {result['funded']}")
    print(f"  Completed:     {result['completed']}")
    print(f"  Spent:         ${result['spent']}")
    print(f"  Still pending: {result['remaining']}")
    print(f"  Chain:         {config['chain_id']}")
    print()

    if result["remaining"] > 0:
        print("  Pending jobs will complete when provider agents come online.")
        print("  Run this tool again later to catch newly online agents.")
    print()


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(config_path):
    """Load config from file, merged with defaults."""
    config = DEFAULT_CONFIG.copy()

    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            user_config = json.load(f)
        config.update(user_config)

    # Also check env vars
    if os.environ.get("ACP_AGENT_WALLET"):
        config["agent_wallet"] = os.environ["ACP_AGENT_WALLET"]

    if not config["agent_wallet"]:
        print("ERROR: agent_wallet not configured.", file=sys.stderr)
        print("Set it in config.json or via ACP_AGENT_WALLET env var.", file=sys.stderr)
        sys.exit(1)

    return config


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ACP Boost — Cross-buy boost automation for ACP agents"
    )
    parser.add_argument("--config", default="config.json",
                       help="Path to config file (default: config.json)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Discover partners only, don't create jobs")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--max-partners", type=int, default=None,
                       help="Limit number of partners")
    args = parser.parse_args()

    # Load config
    config_path = args.config if os.path.exists(args.config) else None
    if not config_path:
        # Try config.json in same directory as this script
        script_dir = Path(__file__).parent
        if (script_dir / "config.json").exists():
            config_path = str(script_dir / "config.json")

    config = load_config(config_path)

    if args.max_partners:
        config["max_jobs"] = min(args.max_partners, config["max_jobs"])

    # Header
    wallet_short = config["agent_wallet"][:10] + "..." + config["agent_wallet"][-6:]
    print("\n" + "=" * 50)
    print("ACP Boost — Cross-Buy Automation")
    print("=" * 50)
    print(f"  Agent wallet: {wallet_short}")
    print(f"  Chain: {config['chain_id']} (Base)")
    print(f"  Max jobs: {config['max_jobs']} | Price cap: ${config['price_cap']}")
    print(f"  Dry run: {args.dry_run}")
    print()

    # Phase 1: Discover
    print("[1/4] Discovering boost partners...")
    partners = discover_partners(config, verbose=args.verbose)
    if not partners:
        print("  No boost partners found. Try different search terms in config.")
        return
    print(f"  Found {len(partners)} agents with boost offerings:")
    for p in partners:
        print(f"    - {p['name']}: {p['offering_name']} (${p['price']:.2f})")
    print()

    # Phase 2: Create jobs
    print(f"[2/4] Creating cross-buy jobs...")
    jobs = create_jobs(partners, config, dry_run=args.dry_run, verbose=args.verbose)
    print(f"  Created {len(jobs)} jobs")
    print()

    if args.dry_run:
        print("[DRY RUN] No jobs created. Remove --dry-run to execute.")
        print_summary(jobs, {"funded": 0, "completed": 0, "spent": 0, "remaining": 0}, config)
        return

    # Phase 3: Process events
    print(f"[3/4] Processing events ({config['timeout_seconds']}s timeout)...")
    result = process_events(jobs, config, verbose=args.verbose)
    print()

    # Phase 4: Summary
    print("[4/4] Summary")
    print_summary(jobs, result, config)


if __name__ == "__main__":
    main()
