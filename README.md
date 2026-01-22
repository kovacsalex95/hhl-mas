# HHL-MAS: Hierarchical Multi-Agent System for Software Development

This repository implements and documents the **AI-Driven Development Workflow**, a methodology centered around a Hierarchical Multi-Agent System (HMAS) utilizing a **Pull-Based** interaction model.

## Core Philosophy

Traditional AI coding often suffers from **Context Drift**. This protocol solves that by decoupling **Context (Memory/Strategy)** from **Execution (Logic/Coding)** and establishing a **Bridge Layer** for inter-agent communication.

### The "Triangle of Power"

- **The Architect (Human CTO):** Provides the **Will** and the **Taste**.
- **The Manager (Lead DEV - Gemini CLI):** The reactive "Brain" that maintains global context and architectural integrity.
- **The Engineer (Senior DEV - Claude Code):** The proactive "Hands" that pulls instructions and executes technical plans.

## The Bridge Layer

Unlike traditional workflows, the Senior DEV (Claude) **pulls** context from the Lead DEV (Gemini) using specialized tools in the `tools/` directory. This keeps the execution context lean and focused.

## Repository Structure

The project follows a strict documentation and execution skeleton:

- `docs/00_global/`: Architectural vision, Pull-based [WORKFLOW.md](./docs/00_global/WORKFLOW.md), and roadmap.
- `docs/01_milestones/`: Detailed specifications and technical plans.
- `docs/99_audit/`: Human-led User Acceptance Testing (UAT) logs.
- `tools/`: The **Bridge Layer** scripts (`ask_lead`, `report_progress`).
- `.gemini/`: Meta-documentation and prompt kits for the Lead DEV.

## Getting Started

1.  Review the [Architecture](./docs/00_global/ARCHITECTURE.md) and [Workflow](./docs/00_global/WORKFLOW.md).
2.  Check the [Roadmap](./docs/00_global/ROADMAP.md) for project status.
3.  Utilize the `tools/` directory to facilitate inter-agent communication.
