# Bridge Layer Tool Specifications

Quick-reference for HMAS Bridge tools. For full API details, see `docs/00_global/ARCHITECTURE.md`.

## Command Syntax

### ask_lead

```bash
python tools/ask_lead.py "<question>"
python tools/ask_lead.py --format json "<question>"
python tools/ask_lead.py --verbose "<question>"
```

| Option | Default | Description |
|--------|---------|-------------|
| `--format` | `text` | Output format: `text`, `json`, `markdown` |
| `--context` | auto | Override automatic context selection |
| `--verbose` | false | Include debug information |

### report_progress

```bash
python tools/report_progress.py --phase <N> --status <status>
python tools/report_progress.py --phase <N> --status <status> --message "<details>"
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--phase` | Yes | Phase number from Technical Plan |
| `--status` | Yes | `done`, `blocked`, or `review` |
| `--message` | No | Additional details |
| `--milestone` | No | Override milestone identifier |

### status_check

```bash
python tools/status_check
python tools/status_check --verbose
python tools/status_check --fix
```

| Option | Default | Description |
|--------|---------|-------------|
| `--verbose` | false | Detailed status information |
| `--fix` | false | Auto-remediate minor issues |
| `--milestone` | auto | Check specific milestone |

## Exit Codes

| Code | ask_lead | report_progress | status_check |
|------|----------|-----------------|--------------|
| 0 | Success | Success | Aligned |
| 1 | Lead unreachable | Lead unreachable | Warning (can proceed) |
| 2 | Invalid query | Invalid arguments | Misaligned (drift detected) |
| 3 | Context error | Phase not found | Cannot determine |

## Output Examples

### ask_lead Success

```
[LEAD DEV RESPONSE]
Use PostgreSQL for the primary database. Redis is acceptable
for caching layer. See ARCHITECTURE.md section 4.2 for
connection pooling requirements.
[END RESPONSE]
```

### report_progress Success

```
[PROGRESS RECORDED]
Phase: 2
Status: done
Milestone: M1_Documentation
Timestamp: 2024-01-15T10:30:00Z
[END REPORT]
```

### status_check Aligned

```
[STATUS CHECK - ALIGNED]
Milestone: M1_Documentation
Current Phase: 2 of 4
Completed Phases: 1
Git Status: Clean
Last Commit: abc123 "docs: update WORKFLOW.md"
[END STATUS]
```

### status_check Warning

```
[STATUS CHECK - WARNING]
Milestone: M1_Documentation
Current Phase: 2 of 4
Warnings:
  - Uncommitted changes detected (3 files)
Recommendation: Commit changes before proceeding
[END STATUS]
```

## When to Use Each Tool

| Situation | Tool | Example |
|-----------|------|---------|
| Ambiguous requirement | `ask_lead` | "Should sessions persist across restarts?" |
| Architecture decision needed | `ask_lead` | "Which auth method should I use?" |
| Edge case not in spec | `ask_lead` | "How should I handle concurrent updates?" |
| Phase completed | `report_progress` | `--phase 1 --status done` |
| Cannot proceed | `report_progress` | `--phase 2 --status blocked` |
| Ready for review | `report_progress` | `--phase 3 --status review` |
| Starting new work | `status_check` | Validate alignment |
| After session restart | `status_check` | Recover context |
| Mid-task sanity check | `status_check` | Verify no drift |

## Common Usage Patterns

### Starting a New Phase

```bash
python tools/status_check
# Read phase requirements
# Implement
# Test
git commit -m "feat: description

Phase: M1.2"
python tools/report_progress.py --phase 2 --status done
```

### Handling Uncertainty

```bash
# Check if answer is in docs first
# If not, ask Lead DEV
python tools/ask_lead.py "The spec mentions 'secure storage' but doesn't specify encryption. Should I use AES-256 or defer to a secrets manager?"
```

### Reporting a Blocker

```bash
python tools/report_progress.py --phase 2 --status blocked --message "External API returns 503. Cannot proceed with integration testing."
```

### Context Recovery

```bash
# After session restart
python tools/status_check --verbose
git log --oneline -5
# Resume from identified phase
```

## Decision Flowchart

```
Start
  │
  ├─ Need guidance/clarification?
  │   ├─ In existing docs? → Read docs directly
  │   └─ Not in docs?
  │       ├─ Strategic/architectural? → ask_lead
  │       └─ Implementation detail? → Decide yourself
  │
  ├─ Reporting progress?
  │   ├─ Phase complete → report_progress --status done
  │   ├─ Blocked → report_progress --status blocked
  │   └─ Need review → report_progress --status review
  │
  └─ Validating state? → status_check
```
