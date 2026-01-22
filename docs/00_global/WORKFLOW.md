# AI-Driven Development Workflow: HMAS Protocol

This document details the **Hierarchical Multi-Agent System (HMAS)** protocol for software development.

## 1. The Core Thesis
Traditional AI coding fails because of **Context Drift**. This protocol solves this by decoupling **Context (Memory/Strategy)** from **Execution (Logic/Coding)** and utilizing a **Pull-Based** communication model.

## 2. Roles (The Triangle of Power)

### 2.1 CTO (Human Operator)
- **Access:** Root / God Mode.
- **Function:** "The Stop Button." Ensures the project aligns with business value.
- **Deliverables:** Project briefs, UAT logs, Green lights.

### 2.2 Lead DEV (The "Brain" - Gemini CLI)
- **Persona:** Engineering Manager and Software Architect.
- **Function:** Manages global state, documentation, and high-level planning.
- **Interaction:** Passive/Reactive. Responds to queries from Senior DEV via the Bridge.
- **Deliverables:** `ARCHITECTURE.md`, Milestone Specs, responses to `ask_lead`.

### 2.3 Senior DEV (The "Hands" - Claude Code)
- **Persona:** Pragmatic Software Engineer.
- **Function:** Executes plans, writes code, runs tests.
- **Interaction:** Active/Pull. Uses `tools/` to fetch context.
- **Deliverables:** Source code, Unit tests, Technical Plans.

## 3. Inter-Agent Communication (The Bridge)
The Senior DEV **pulls** instructions rather than waiting for them.

- **Clarification:** `python tools/ask_lead.py "How should I handle the user auth?"`
- **Progress:** `python tools/report_progress.py --phase 1 --status done`

## 4. The Grand Workflow Lifecycle

### Phase 1: Inception & Architecture
- CTO writes `project_brief.txt`.
- Lead DEV generates `ARCHITECTURE.md` and `ROADMAP.md`.

### Phase 2: The Build Loop (Feature Milestones)
- **2A: Planning**: Lead DEV publishes Milestone Spec in `docs/01_milestones/`. Senior DEV reads it and creates a Technical Plan.
- **2B: Execution**: 
    1. Senior DEV pulls current phase context.
    2. Senior DEV writes code/tests.
    3. Senior DEV runs `tools/report_progress.py`.
    4. Loop.

### Phase 3: Human Interface (UAT)
- CTO tests features; logs in `docs/99_audit/`.

### Phase 4: Consolidation
- Lead DEV synthesizes feedback.
- Senior DEV pulls consolidation plan.

### Phase 5: Deployment
- Senior DEV generates artifacts using Lead DEV's environment context.