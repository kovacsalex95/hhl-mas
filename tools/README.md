# HMAS Bridge Layer Tools

The Bridge Layer enables communication between Senior DEV (Claude Code) and Lead DEV (Gemini) in the Hierarchical Multi-Agent System. It implements the **pull-based** interaction model where Senior DEV requests context as needed rather than receiving pushed instructions.

## Overview

| Tool | Purpose |
|------|---------|
| `ask_lead.py` | Query Lead DEV for clarifications, architectural decisions, or implementation guidance |
| `report_progress.py` | Report phase/milestone completion status to Lead DEV |
| `status_check.py` | Validate current execution state against the active plan |

## Installation

**Requirements:**
- Python 3.8+
- POSIX-compliant shell (bash/zsh)
- Git 2.x+

**Install dependencies:**

```bash
pip install -r tools/requirements.txt
```

The only external dependency is `PyYAML>=6.0`. All other functionality uses Python standard library modules.

## Configuration

### Configuration File

The Bridge Layer is configured via `tools/config.yaml`:

```yaml
bridge:
  lead_dev:
    interface: "gemini-cli"   # Lead DEV interface type
    timeout: 30               # Connection timeout (seconds)
    retry_count: 3            # Number of retry attempts
    retry_delay: 5            # Delay between retries (seconds)

  context:
    max_tokens: 8000          # Maximum context size
    include_architecture: true
    include_roadmap: false
    truncation_strategy: "recent_first"

  output:
    default_format: "text"    # text, json, or markdown
    include_timestamps: true
    log_queries: true
    log_file: "tools/logs/bridge.log"

project:
  docs_path: "docs/"
  milestones_path: "docs/01_milestones/"
  architecture_file: "docs/00_global/ARCHITECTURE.md"
  roadmap_file: "docs/00_global/ROADMAP.md"
```

### Environment Variables

Configuration can also be set via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `HMAS_LEAD_INTERFACE` | Lead DEV interface type | `gemini-cli` |
| `HMAS_CONTEXT_MAX_TOKENS` | Maximum context size | `8000` |
| `HMAS_LOG_LEVEL` | Logging verbosity | `INFO` |
| `HMAS_CONFIG_PATH` | Path to config file | `tools/config.yaml` |

## Tools Reference

### `ask_lead` - Query Lead DEV

Query Lead DEV for architectural decisions, requirement clarifications, or implementation guidance.

**Usage:**

```bash
python tools/ask_lead.py "<question>" [options]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `question` | string | Yes | The question to ask Lead DEV |

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--context` | `auto`, `minimal`, `full` | `auto` | Context selection mode |
| `--format` | `text`, `json`, `markdown` | `text` | Output format |
| `--verbose` | flag | `false` | Include debug information |
| `--milestone` | string | auto-detected | Override milestone identifier |
| `--phase` | string | auto-detected | Override phase identifier |

**Examples:**

```bash
# Basic query
python tools/ask_lead.py "Should user sessions persist across server restarts?"

# With JSON output
python tools/ask_lead.py --format json "What authentication method should I use?"

# With verbose logging
python tools/ask_lead.py --verbose "How should errors be reported to users?"

# With specific context mode
python tools/ask_lead.py --context full "What is the overall architecture?"
```

**Output formats:**

Text (default):
```
[LEAD DEV RESPONSE]
<response content>
[END RESPONSE]
```

JSON:
```json
{
  "status": "success",
  "response": "<response content>",
  "context_used": ["ARCHITECTURE.md", "M2_Toolkit_Implementation.md"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### `report_progress` - Report Phase Status

Report phase/milestone completion status to Lead DEV, enabling global state updates.

**Usage:**

```bash
python tools/report_progress.py --phase <N> --status <status> [options]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--phase` | integer | Yes | Phase number from Technical Plan |
| `--status` | enum | Yes | Status: `done`, `blocked`, or `review` |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--message` | string | none | Additional details or notes |
| `--milestone` | string | auto-detected | Override milestone identifier |
| `--verbose` | flag | `false` | Include debug information |

**Status Values:**

| Status | Meaning | Lead DEV Action |
|--------|---------|-----------------|
| `done` | Phase completed successfully | Update progress tracker, unlock next phase |
| `blocked` | Cannot proceed without intervention | Flag for CTO/Lead attention |
| `review` | Ready for human or Lead review | Notify stakeholders, pause execution |

**Examples:**

```bash
# Phase completed
python tools/report_progress.py --phase 1 --status done

# Phase blocked with details
python tools/report_progress.py --phase 2 --status blocked --message "Waiting for API credentials"

# Ready for review
python tools/report_progress.py --phase 3 --status review --message "Authentication flow ready for UAT"
```

**Output:**

```
[PROGRESS RECORDED]
Phase: 1
Status: done
Milestone: M2_Toolkit_Implementation
Timestamp: 2024-01-15T10:30:00Z
[END REPORT]
```

---

### `status_check` - Validate Alignment

Validate current execution state against the active plan; detect drift or misalignment.

**Usage:**

```bash
python tools/status_check.py [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose` | flag | `false` | Show detailed status information |
| `--fix` | flag | `false` | Attempt automatic remediation of minor issues |
| `--milestone` | string | auto-detected | Check specific milestone instead of current |

**Checks Performed:**

1. **Git State:**
   - Current branch identification
   - Uncommitted changes detection
   - Commit history alignment

2. **Documentation State:**
   - Technical Plan existence
   - Current phase identification
   - Milestone spec accessibility

3. **Progress Alignment:**
   - Completed phases match git history
   - Current phase validity

**Examples:**

```bash
# Basic status check
python tools/status_check.py

# Verbose output with debug information
python tools/status_check.py --verbose

# Check specific milestone
python tools/status_check.py --milestone M2_Toolkit_Implementation

# Attempt automatic fixes
python tools/status_check.py --fix
```

**Output (Aligned):**

```
[STATUS CHECK - ALIGNED]
Milestone: M2_Toolkit_Implementation
Current Phase: 2 of 4
Completed Phases: 1
Git Status: Clean
Last Commit: abc123 "feat: implement ask_lead tool"
[END STATUS]
```

**Output (Warning):**

```
[STATUS CHECK - WARNING]
Milestone: M2_Toolkit_Implementation
Current Phase: 2 of 4
Warnings:
  - Uncommitted changes detected (3 files)
Recommendation: Review warnings before proceeding
[END STATUS]
```

**Output (Misaligned):**

```
[STATUS CHECK - MISALIGNED]
Milestone: M2_Toolkit_Implementation
Issues:
  - ARCHITECTURE.md not found
  - Cannot determine current git branch
Action Required: Run 'ask_lead' for remediation guidance
[END STATUS]
```

## Troubleshooting

### Exit Codes Reference

| Code | `ask_lead` | `report_progress` | `status_check` |
|------|------------|-------------------|----------------|
| 0 | Success - response received | Success - progress recorded | Aligned - no issues |
| 1 | Error - Lead DEV unreachable | Error - Lead DEV unreachable | Warning - minor issues |
| 2 | Error - invalid query format | Error - invalid arguments | Misaligned - drift detected |
| 3 | Error - context aggregation failed | Error - phase not found | Error - cannot determine status |

### Common Issues

**Exit code 1 (Lead DEV unreachable):**
- Ensure the Lead DEV (Gemini) session is active
- Check network connectivity
- Verify `config.yaml` settings for timeout and retry values

**Exit code 2 (Invalid input):**
- For `ask_lead`: Ensure question is not empty
- For `report_progress`: Check that `--phase` is a positive integer and `--status` is one of: `done`, `blocked`, `review`

**Exit code 3 (Context/configuration error):**
- Verify `config.yaml` exists and is valid YAML
- Check that project documentation paths are correct
- Ensure `ARCHITECTURE.md` exists at the configured location

**status_check returns WARNING:**
- Review uncommitted changes and commit or stash them
- Warnings are informational; work can proceed with caution

**status_check returns MISALIGNED:**
- Critical issues detected that may cause drift
- Run `ask_lead` for remediation guidance before proceeding

## Directory Structure

```
tools/
├── ask_lead.py           # Query tool for clarifications
├── report_progress.py    # Progress reporting tool
├── status_check.py       # Alignment validation tool
├── lib/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── context.py        # Context aggregation logic
│   └── interface.py      # Lead DEV communication interface
├── config.yaml           # Bridge Layer configuration
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Further Reading

- [ARCHITECTURE.md](../docs/00_global/ARCHITECTURE.md) - Full Bridge Layer specifications
- [WORKFLOW.md](../docs/00_global/WORKFLOW.md) - HMAS workflow documentation
- [ROADMAP.md](../docs/00_global/ROADMAP.md) - Project milestones and timeline
