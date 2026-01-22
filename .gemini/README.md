# Gemini CLI Toolkit: HMAS Lead DEV Configuration

This directory contains the configuration and prompt repository for the **Lead DEV** (Gemini CLI) within the HMAS ecosystem.

## Implementation Plan (Pull-Based Model)

The goal is to enable a seamless Pull-Based interaction where the Lead DEV acts as a high-fidelity context provider.

### Phase 1: Bridge & Documentation (Current)
- [x] Formalize the Pull-Based HMAS workflow.
- [ ] Implement the **Bridge Layer** (`tools/ask_lead.py`).
- [ ] Establish the documentation skeleton in `docs/`.

### Phase 2: Reactive Prompt Engineering
- [ ] Develop the **Reactive Lead DEV** System Prompt: Focus on concise, high-context responses to specific queries.
- [ ] Develop the **Senior DEV Pull** Prompt: Focus on how to effectively use the bridge tools.

### Phase 3: Bridge Automation
- [ ] Enhance `tools/ask_lead.py` to automatically include relevant documentation snippets.
- [ ] Implement `tools/status_check` for automated plan validation.

## Agent Personas

### Lead DEV (Gemini)
- **Role:** Reactive Architect.
- **Goal:** Provide architectural truth and clear specs when queried.
- **Interface:** Responds to `tools/ask_lead.py` triggers.

### Senior DEV (Claude)
- **Role:** Proactive Engineer.
- **Goal:** Pull necessary context to execute phases with zero-drift precision.
- **Interface:** Executes `tools/` to fetch data and report progress.