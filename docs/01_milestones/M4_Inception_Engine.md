# Milestone 4: The Inception Engine (Day 0 Capabilities)

## Objective
Build the "Inception Engine" to enable autonomous project bootstrapping. The goal is to allow the Senior DEV (Claude) to take a raw user brief (text or file) and autonomously generate the project structure and the first milestone specification, removing the need for the CTO to manually author markdown files.

## Phases

### Phase 1: Ingest Capability
- [x] **Tool Implementation:** Create `tools/ingest_brief.py`.
    - **Input:** Accepts a raw text string or a filepath via command line arguments.
    - **Logic:** Constructs a "Project Inception" prompt containing the brief and sends it to the Lead DEV.
    - **Output:** Automatically generates `docs/00_global/ARCHITECTURE.md` and `docs/01_milestones/M1_Init.md` based on the Lead DEV's response.
- [x] **Integration:** Ensure the tool handles directory creation if `docs/` paths do not exist.

### Phase 2: Continuous Progression
- [x] **Tool Implementation:** Create `tools/fetch_next.py`.
    - **Trigger:** Designed to be called when a milestone is 100% complete.
    - **Logic:**
        1. Archives the current specification (e.g., moves to `docs/history/`).
        2. Sends a query to Lead DEV: "Milestone X is complete. What is the next logical step?"
        3. Writes the response to a new file (e.g., `docs/01_milestones/M{X+1}_Title.md`).
- [x] **Safety:** Ensure it doesn't overwrite existing incomplete milestones without confirmation.

### Phase 3: The Bootloader
- [x] **Script Implementation:** Create `hmas_boot.sh` (Master Shell Script).
    - **Environment:** Checks for and creates the Python virtual environment (`.venv`) if missing.
    - **Dependencies:** Installs `tools/requirements.txt`.
    - **Configuration:** Verifies existence of `.env` or API keys.
    - **Launch:** Starts the Senior DEV (Claude Code) session.
    - **Context:** Automatically pre-loads the system prompt (via clipboard or argument if supported) to reduce manual copy-pasting.

## The CTO Operations Manual

### 1. Initialization (The Boot Prompt)
Paste the following block into the Senior DEV's (Claude Code) terminal to initiate the session:

```text
ACT AS: Senior DEV (HMAS Proactive Engineer).
CURRENT OBJECTIVE: Execute Milestone 4 (The Inception Engine).
SOURCE OF TRUTH: docs/01_milestones/M4_Inception_Engine.md

PROTOCOL:
1. Read the Milestone Specification above.
2. Verify your environment by running: python tools/status_check.py
3. START Phase 1 immediately.
4. Implement the requested tools in the `tools/` directory.
5. Report progress after each phase: python tools/report_progress.py
```

### 2. Verification Test
To verify the Inception Engine works:
1.  **Backup:** Commit all current work.
2.  **Destruction:** Delete the `src/` directory (or a test subdirectory).
3.  **Inception:** Run `python tools/ingest_brief.py "Build a simple calculator CLI"`
4.  **Check:** Verify that a new Milestone 1 and Architecture doc have been created for the calculator.

## Success Criteria
- [x] **Autonomous Bootstrap:** The system can go from a one-line prompt to a documented plan (`M1_Init.md`) without human editing.
- [x] **Seamless Continuity:** `fetch_next.py` correctly identifies the next logical step after a milestone is marked complete.
- [x] **One-Click Start:** `hmas_boot.sh` successfully sets up the environment and gets the Senior DEV ready to work with minimal human intervention.
