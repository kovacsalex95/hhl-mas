# HMAS Bridge Layer Tools

The Bridge Layer enables communication between Senior DEV (Claude Code) and Lead DEV (Gemini) in the Hierarchical Multi-Agent System. It implements the **pull-based** interaction model where Senior DEV requests context as needed rather than receiving pushed instructions.

## Overview

| Tool | Purpose |
|------|---------|
| `ask_lead.py` | Query Lead DEV for clarifications, architectural decisions, or implementation guidance |
| `report_progress.py` | Report phase/milestone completion status to Lead DEV |
| `status_check.py` | Validate current execution state against the active plan |
| `ingest_brief.py` | Bootstrap new projects from a raw text brief or file |
| `fetch_next.py` | Automatically transition to the next milestone after completion |
| `handoff.py` | Generate session handoff prompts for context renewal between sessions |

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
| `--mode` | `interactive`, `stub`, `api` | `interactive` | Interface mode for Lead DEV communication |

**Interface Modes (`--mode`):**

| Mode | Description |
|------|-------------|
| `interactive` | Opens an interactive session with Lead DEV (Gemini) - **default** |
| `stub` | Returns stub responses for testing without actual Lead DEV connection |
| `api` | Reserved for future API-based communication (not yet implemented) |

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

---

### `ingest_brief` - Project Inception

Bootstrap a new project or module from a raw text brief or file. This tool initializes `ARCHITECTURE.md` and `M1_Init.md`.

**Usage:**

```bash
python tools/ingest_brief.py "<brief>" [options]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `brief` | string | No* | The project brief text (required if `--file` is not used) |

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--file`, `-f` | string | none | Path to a file containing the project brief |
| `--verbose` | flag | `false` | Include debug information |
| `--dry-run` | flag | `false` | Preview files without writing them |
| `--output-dir` | string | `docs/` | Override output directory |

**Examples:**

```bash
# Bootstrap from string
python tools/ingest_brief.py "Build a simple calculator CLI"

# Bootstrap from file
python tools/ingest_brief.py --file project_brief.txt

# Preview generation
python tools/ingest_brief.py --dry-run "Create a REST API for user management"
```

---

### `fetch_next` - Milestone Progression

Automatically transition to the next milestone after completing the current one. It archives the completed milestone and fetches the next specification from Lead DEV.

**Usage:**

```bash
python tools/fetch_next.py [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--milestone` | string | auto-detected | Specify the milestone that was just completed |
| `--force`, `-f` | flag | `false` | Skip confirmation for incomplete items or overwrites |
| `--no-archive` | flag | `false` | Skip archiving the current milestone |
| `--verbose` | flag | `false` | Include debug information |
| `--dry-run` | flag | `false` | Preview the next milestone without writing |

**Examples:**

```bash
# Auto-detect current and fetch next
python tools/fetch_next.py

# Specify completed milestone
python tools/fetch_next.py --milestone M3

# Force progression despite incomplete items
python tools/fetch_next.py --force
```

---

### `handoff` - Session Context Renewal

Generate a session handoff prompt that summarizes the current project state. Use this when starting a new Senior DEV (Claude Code) session to provide full context.

**Usage:**

```bash
python tools/handoff.py [options]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--milestone`, `-m` | string | auto-detected | Specify the target milestone (e.g., M5) |
| `--next`, `-n` | flag | `false` | Generate handoff for the next milestone after current |
| `--include-audit`, `-a` | flag | `false` | Include summary from the latest audit log |
| `--compact`, `-c` | flag | `false` | Generate a more compact prompt (for smaller context windows) |
| `--verbose`, `-v` | flag | `false` | Include debug information to stderr |
| `--output`, `-o` | string | stdout | Write output to file instead of stdout |

**Examples:**

```bash
# Generate for current milestone
python tools/handoff.py

# Generate for specific milestone
python tools/handoff.py --milestone M5

# Generate for next milestone (useful for transitions)
python tools/handoff.py --next

# Include audit summary
python tools/handoff.py --include-audit

# Compact output for smaller context windows
python tools/handoff.py --compact

# Write to file for clipboard copy
python tools/handoff.py --output handoff_prompt.txt
```

**Output:**

The tool generates a structured "System Prompt" containing:

- **Header:** Project name, current milestone, generation timestamp
- **Objective:** Goal of the current milestone
- **Architecture Summary:** Key architectural decisions (omitted in compact mode)
- **Roadmap:** Current project progress status
- **Milestone Phases:** Phase checklist from the milestone spec
- **Success Criteria:** Completion criteria for the milestone
- **Audit Summary:** Latest audit results (if `--include-audit` is used)
- **Instructions:** Quick-start instructions for the new session

---

## Context Renewal Workflow

When a Senior DEV session ends (context exhaustion, timeout, or milestone transition), use the following workflow to start a new session with full context:

### Step 1: Complete the Current Milestone

After completing all phases of a milestone:

```bash
# Report final phase completion
python tools/report_progress.py --phase 3 --status done

# Fetch the next milestone (archives current, generates next)
python tools/fetch_next.py
```

### Step 2: Generate a Handoff Prompt

Generate the session initialization block for the new session:

```bash
# Generate handoff for the new milestone
python tools/handoff.py --next

# Or explicitly for a specific milestone
python tools/handoff.py --milestone M6
```

**Copy-to-clipboard shortcut:**

```bash
# macOS
python tools/handoff.py | pbcopy

# Linux (X11)
python tools/handoff.py | xclip -selection clipboard

# Linux (Wayland)
python tools/handoff.py | wl-copy
```

### Step 3: Start the New Session

1. Open a new Claude Code session
2. Paste the handoff prompt as the first message
3. The new session now has full project context

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Context Renewal Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Session N (Milestone M)                                        │
│   ┌─────────────────────────────┐                                │
│   │  1. Complete milestone      │                                │
│   │  2. report_progress --done  │                                │
│   │  3. fetch_next.py           │ ─── Archives M, creates M+1    │
│   └─────────────────────────────┘                                │
│                │                                                 │
│                ▼                                                 │
│   ┌─────────────────────────────┐                                │
│   │  4. handoff.py --next       │ ─── Generates System Prompt    │
│   └─────────────────────────────┘                                │
│                │                                                 │
│                ▼                                                 │
│   Session N+1 (Milestone M+1)                                    │
│   ┌─────────────────────────────┐                                │
│   │  5. Paste handoff prompt    │                                │
│   │  6. Begin milestone M+1     │                                │
│   └─────────────────────────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Exit Codes Reference

| Code | `ask_lead` | `report_progress` | `status_check` | `handoff` |
|------|------------|-------------------|----------------|-----------|
| 0 | Success - response received | Success - progress recorded | Aligned - no issues | Success - prompt generated |
| 1 | Error - Lead DEV unreachable | Error - Lead DEV unreachable | Warning - minor issues | Error - required files not found |
| 2 | Error - invalid query format | Error - invalid arguments | Misaligned - drift detected | Error - invalid arguments |
| 3 | Error - context aggregation failed | Error - phase not found | Error - cannot determine status | - |

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
├── hmas_boot.sh          # Master bootloader script (Project Root)
├── tools/
│   ├── ask_lead.py           # Query tool for clarifications
│   ├── report_progress.py    # Progress reporting tool
│   ├── status_check.py       # Alignment validation tool
│   ├── ingest_brief.py       # Project inception tool
│   ├── fetch_next.py         # Milestone progression tool
│   ├── handoff.py            # Session context renewal tool
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── context.py        # Context aggregation logic
│   │   └── interface.py      # Lead DEV communication interface
│   ├── config.yaml           # Bridge Layer configuration
│   ├── requirements.txt      # Python dependencies
│   └── README.md             # This file
```

## The Master Bootloader (`hmas_boot.sh`)

The `hmas_boot.sh` script (located in the project root) is the official entry point for HMAS sessions. It automates environment setup and context initialization.

**Usage:**

```bash
./hmas_boot.sh [options]
```

**Options:**

- `--check`: Run environment checks only.
- `--inception`: Start in "Project Inception" mode for new projects.
- `--milestone M#`: Boot with a specific milestone context.

It automatically copies the appropriate **Boot Prompt** to your clipboard for easy pasting into the Senior DEV (Claude Code) session.

## Further Reading

- [ARCHITECTURE.md](../docs/00_global/ARCHITECTURE.md) - Full Bridge Layer specifications
- [WORKFLOW.md](../docs/00_global/WORKFLOW.md) - HMAS workflow documentation
- [ROADMAP.md](../docs/00_global/ROADMAP.md) - Project milestones and timeline
