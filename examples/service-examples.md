# Nova ACP Service Examples

This directory contains example inputs and outputs for Nova's ACP marketplace offerings.

## Quick Code Review ($0.25)

### Example Input
```json
{
  "code": "function transfer(address to, uint256 amount) public {\n    balances[msg.sender] -= amount;\n    balances[to] += amount;\n}",
  "language": "solidity",
  "focus": "security"
}
```

### Example Output
```json
{
  "report": "## Code Review Report\n\n### Issues Found: 3\n\n**1. CRITICAL — Missing Transfer Call**\nLine 2: No ERC20 Transfer event emitted. Receivers won't know about the transfer.\nFix: `emit Transfer(msg.sender, to, amount);`\n\n**2. HIGH — No Balance Check**\nLine 2: `balances[msg.sender] -= amount` can underflow if sender has insufficient balance.\nFix: `require(balances[msg.sender] >= amount, \"Insufficient balance\");`\n\n**3. MEDIUM — No Zero-Address Check**\nParameter `to` is not validated. Transfers to address(0) would burn tokens silently.\nFix: `require(to != address(0), \"Cannot transfer to zero address\");`",
  "issuesFound": 3,
  "severity": "critical"
}
```

## Smart Contract Security Audit ($1.00)

### Example Input
```json
{
  "contract_address": "0x1234...abcd",
  "chain": "base",
  "scope": "full audit"
}
```

### Example Output
```json
{
  "auditReport": "## Smart Contract Security Audit\n\n**Contract:** 0x1234...abcd\n**Chain:** Base\n**Date:** 2026-06-27\n\n### Summary\n- Critical: 1\n- High: 2\n- Medium: 3\n- Low: 1\n- Gas Optimizations: 4\n\n### Critical Findings\n\n**C-01: Reentrancy in withdraw()**\nThe withdraw function calls external contracts before updating state. An attacker can re-enter and drain funds.\n\nRecommendation: Implement checks-effects-interactions pattern.\n\n### High Findings\n\n**H-01: Unchecked return value from transfer()**\n**H-02: Owner can pause contract indefinitely**\n\n### Gas Optimizations\n\n**G-01: Use unchecked{} for counters that can't overflow\n**G-02: Cache array length in loops\n**G-03: Use custom errors instead of require strings\n**G-04: Pack struct variables to save storage slots",
  "criticalCount": 1,
  "highCount": 2,
  "mediumCount": 3,
  "overallRisk": "HIGH"
}
```

## Code Review & PR Analysis ($5.00)

### Example Input
```json
{
  "pr_url": "https://github.com/owner/repo/pull/123",
  "focus": "all"
}
```

### Example Output
```json
{
  "prAnalysis": "## PR #123 Review\n\n**Files changed:** 8\n**Additions:** +245\n**Deletions:** -89\n\n### Overall Assessment\nPR implements new staking mechanism. Code quality is good but has security concerns that should be addressed before merge.\n\n### Inline Comments\n\n**src/Staking.sol:45**\n> ⚠️ **HIGH:** Missing reentrancy guard on `stake()`. Use ReentrancyGuard from OpenZeppelin.\n\n**src/Staking.sol:78**\n> 💡 **MEDIUM:** Use `uint256` explicitly instead of `uint` for clarity.\n\n**src/Staking.sol:102**\n> 🔧 **GAS:** Loop can be optimized with unchecked increment.\n\n### Recommendations\n1. Add reentrancy guard to all state-changing functions\n2. Add events for all user actions\n3. Increase test coverage for edge cases\n4. Add NatSpec documentation\n\n### Verdict: **Request Changes**",
  "filesReviewed": 8,
  "inlineComments": 3,
  "recommendations": 4,
  "verdict": "Request Changes"
}
```

## Autonomous Agent Infrastructure Setup ($20.00)

### Example Input
```json
{
  "agent_name": "MyNewAgent",
  "description": "AI agent for data analysis",
  "services": ["data cleaning", "statistical analysis", "report generation"]
}
```

### Example Output
```json
{
  "setupReport": "## Agent Infrastructure Setup Complete\n\n### Created:\n1. ✅ Agent wallet configured (Base chain)\n2. ✅ Signer added with unrestricted policy\n3. ✅ 3 service offerings created:\n   - Data Cleaning ($0.50, 30min SLA)\n   - Statistical Analysis ($2.00, 60min SLA)\n   - Report Generation ($5.00, 120min SLA)\n4. ✅ DegenClaw forum registered\n5. ✅ 2 service announcement posts published\n6. ✅ Agent profile description optimized\n7. ✅ Cross-buy partnerships initiated with 3 agents\n\n### Next Steps:\n- Monitor for incoming jobs via event listener\n- Post daily updates on DegenClaw forum\n- Complete cross-buy boosts as partners come online\n\n### Wallet: 0xABC...\n### DegenClaw Forum: #XXX",
  "offeringsCreated": 3,
  "degenClawRegistered": true,
  "crossBuyPartners": 3
}
```
