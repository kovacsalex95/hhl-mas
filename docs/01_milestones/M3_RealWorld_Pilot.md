# Milestone 3: Real-world Application (The Pilot)

## Objective
Build a "Pilot Application" (a simple Python-based REST API for a Todo List) inside the `src/` directory to stress-test the HMAS workflow. This is not just about building the app, but about validating the **Lead DEV (Gemini) <-> Bridge <-> Senior DEV (Claude)** interaction model.

## Phases

### Phase 1: Initialization & Architecture (Completed)
- [x] **Setup:** Initialize `src/` directory and Python environment structure.
- [x] **Architecture Query:** Senior DEV must use `ask_lead` to determine the authorized Tech Stack (Framework, Database, Testing).
- [x] **Scaffolding:** Create `requirements.txt` and initial project skeleton based on the decision.

### Phase 2: Core Implementation (Completed)
- [x] **Models:** Implement the Todo Item data model.
- [x] **API:** Implement CRUD endpoints (GET, POST, PUT, DELETE).
- [x] **Persistence:** Implement simple storage (in-memory or SQLite as decided).

### Phase 3: Verification & Delivery (In Progress)
- [x] **Testing:** Implement unit tests.
- [ ] **Validation:** Verify endpoints with `curl` or a test script.
- [ ] **Final Report:** Submit completion report via `report_progress`.

## The CTO Operations Manual

### 1. Initialization (The Boot Prompt)
Paste the following block into the Senior DEV's (Claude Code) terminal to initiate the session:

```text
ACT AS: Senior DEV (HMAS Proactive Engineer).
CURRENT OBJECTIVE: Execute Milestone 3 (Real-world Pilot).
SOURCE OF TRUTH: docs/01_milestones/M3_RealWorld_Pilot.md

PROTOCOL:
1. Read the Milestone Specification above.
2. Verify your environment by running: python tools/status_check.py
3. START Phase 1 immediately.
4. CRITICAL: Do NOT assume the tech stack. You must use `python tools/ask_lead.py` to obtain architectural decisions (e.g., "Which web framework should I use?").
5. Report progress after each phase: python tools/report_progress.py
```

### 2. Monitoring
Run this command in a separate terminal window to watch the Bridge Layer traffic:

```bash
# Monitor the Bridge Logs (Lead DEV interactions)
tail -f tools/logs/bridge.log
```

*(Note: Ensure `tools/logs/` directory exists or is created by the tools)*

### 3. The "Happy Path" Checklist
If the HMAS is working correctly, you should observe:
1.  [ ] **Startup:** Senior DEV reads the file and runs `status_check.py`.
2.  [ ] **The Pull:** Within 2 minutes, Senior DEV runs `ask_lead.py` asking about the framework (e.g., FastAPI vs Flask).
3.  [ ] **The Response:** Lead DEV (Gemini) provides the decision.
4.  [ ] **Execution:** Senior DEV creates files in `src/`.
5.  [ ] **Reporting:** Senior DEV runs `report_progress.py` after scaffolding.
6.  [ ] **Atomic Commits:** `git log` shows clean commits corresponding to the phases.

## Audit Protocol
The CTO must maintain a log to validate the system. Create `docs/99_audit/M3_Pilot_Log.md` and track:

| Event | Metric | Pass/Fail |
|-------|--------|-----------|
| **Context Pull** | Did Senior DEV ask before building? | [ ] |
| **Atomic Commits** | Are commits clean and descriptive? | [ ] |
| **Bridge Stability** | Did tools run without crashing? | [ ] |
| **Protocol Adherence** | Did Senior DEV follow the phases? | [ ] |

## Success Criteria (System Level)
- **Zero Hallucination:** Senior DEV did not invent requirements; it fetched them.
- **Zero Drift:** The final implementation matches the decisions given via `ask_lead`.
- **Operational Health:** The Bridge Layer handled all queries and reports successfully.