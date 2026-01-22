# Gemini CLI Toolkit: HMAS Lead DEV Configuration

This directory contains the configuration and prompt repository for the **Lead DEV** (Gemini CLI) within the HMAS ecosystem.

## Milestone Status

The configuration and prompts in this directory support the HMAS Roadmap defined in `docs/00_global/ROADMAP.md`.

### Milestone 1: Documentation & Workflow Foundation (Completed)
- [x] Formalized Pull-Based HMAS workflow.
- [x] Established documentation skeleton (`docs/`).
- [x] Created initial Prompt Kits (`.gemini/prompts/`).

### Milestone 2: Toolkit Implementation (In Progress)
- [x] Refine system prompts for Pull-Based Model.
- [x] Implement Bridge Layer tools (`tools/`).
- [ ] Finalize Toolkit Documentation (`tools/README.md`).

### Milestone 3: Real-world Application (Planned)
- [ ] Apply HMAS to a target project.
- [ ] Refine prompts and protocols based on usage.

## Agent Personas

### Lead DEV (Gemini)
- **Role:** Reactive Architect.
- **Goal:** Provide architectural truth and clear specs when queried.
- **Interface:** Responds to `tools/ask_lead.py` triggers.

### Senior DEV (Claude)
- **Role:** Proactive Engineer.
- **Goal:** Pull necessary context to execute phases with zero-drift precision.
- **Interface:** Executes `tools/` to fetch data and report progress.
