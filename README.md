# HHL-MAS: Hierarchical Multi-Agent System for Software Development

This repository implements and documents the **AI-Driven Development Workflow**, a methodology centered around a Hierarchical Multi-Agent System (HMAS) utilizing a **Pull-Based** interaction model.

## Core Philosophy

Traditional AI coding often suffers from **Context Drift**. This protocol solves that by decoupling **Context (Memory/Strategy)** from **Execution (Logic/Coding)** and establishing a **Bridge Layer** for inter-agent communication.

### The "Triangle of Power"

- **The Architect (Human CTO):** Provides the **Will** and the **Taste**.
- **The Manager (Lead DEV - Gemini CLI):** The reactive "Brain" that maintains global context and architectural integrity.
- **The Engineer (Senior DEV - Claude Code):** The proactive "Hands" that pulls instructions and executes technical plans.

## The Bridge Layer

The Senior DEV (Claude) **pulls** context from the Lead DEV (Gemini) using specialized tools. This ensures the execution context remains lean, focused, and free from strategic drift.

- **`ask_lead.py`**: Query for architectural decisions or clarifications (Interactive mode).
- **`report_progress.py`**: Mark phases as done, blocked, or ready for review.
- **`status_check.py`**: Verify alignment between the current code/git state and the plan.
- **`ingest_brief.py`**: Bootstrap new projects/milestones from a raw text brief.
- **`fetch_next.py`**: Seamlessly transition to the next milestone.
- **`handoff.py`**: Generate a "Context Renewal" prompt to start fresh sessions.

## Repository Structure

The project follows a strict documentation and execution skeleton:

- `hmas_boot.sh`: The **Master Bootloader** for starting new sessions.
- `docs/00_global/`: Architectural vision, [WORKFLOW.md](./docs/00_global/WORKFLOW.md), and [ROADMAP.md](./docs/00_global/ROADMAP.md).
- `docs/01_milestones/`: Detailed specifications and technical plans.
- `docs/99_audit/`: Human-led User Acceptance Testing (UAT) and progression logs.
- `tools/`: The **Bridge Layer** implementation and [README](./tools/README.md).
- `.gemini/`: Meta-documentation and prompt kits for the Lead DEV.

## Getting Started

### 1. Bootstrap or Join
If starting a new project, use the **Inception Engine**:
```bash
python3 tools/ingest_brief.py "Your project brief here"
```

### 2. Boot the Session
Use the bootloader to generate your first prompt for the Senior DEV (Claude):
```bash
./hmas_boot.sh
```
*This copies the boot prompt to your clipboard.*

### 3. Execute and Renew
When a milestone is complete or context is exhausted:
1. Run `python3 tools/fetch_next.py` to prepare the next milestone.
2. Run `python3 tools/handoff.py --next` to generate a renewal prompt.
3. Start a clean Claude session and paste the prompt.
