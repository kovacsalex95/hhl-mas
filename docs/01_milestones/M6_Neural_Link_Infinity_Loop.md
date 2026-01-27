# Milestone 6: The Neural Link & Infinity Loop

**Status:** COMPLETED
**Owner:** Lead DEV (Architecture) & Senior DEV (Implementation)
**Pre-requisites:** Milestone 5 Completed (Bridge Layer active)

## 1. Objective

To upgrade the HMAS from a "Human-in-the-loop" system to a "Human-on-the-loop" system. This involves connecting the **Gemini API** to the Bridge Layer (replacing manual Lead DEV inputs) and implementing an **Infinity Loop** script to automate session context renewal.

## 2. Success Criteria

- [ ] **API Integration:** `ask_lead.py` queries the Gemini API directly using architectural context, returning valid guidance without human typing.
- [ ] **Automated Handoff:** `handoff.py` can write context to a file (`.gemini/next_context.txt`) for consumption by the bootloader.
- [ ] **Infinity Loop:** `hmas_loop.sh` successfully restarts the Claude session with new context automatically upon previous session exit.
- [ ] **Protocol Compliance:** Claude correctly uses "Command Macros" (e.g., `>> DONE`) to trigger tools.

## 3. Progress Tracker

| Phase | Description | Status | Commit Hash |
| :--- | :--- | :--- | :--- |
| **P1** | **The Brain (Gemini API)** | [x] Done | pending |
| **P2** | **The Heartbeat (Loop Script)** | [x] Done | pending |
| **P3** | **The Protocol (Command Macros)** | [x] Done | pending |
| **P4** | **The Pilot (Validation)** | [x] Done | pending |

---

## 4. Phase Specifications

### Phase 1: The Brain (Gemini API Integration)

**Goal:** Remove the need for the Human CTO to manually type responses in `ask_lead.py`.

**Context for Senior DEV:**
- Read `tools/lib/interface.py` (current stub/interactive implementation).
- Read `tools/requirements.txt`.

**Tasks:**
1.  **Dependencies:** Add `google-generativeai` and `python-dotenv` to `tools/requirements.txt`.
2.  **Configuration:** Create a template `.env.example` containing `GEMINI_API_KEY` and `GEMINI_MODEL` (default: `gemini-1.5-pro`).
3.  **Implementation:**
    - Create `tools/lib/gemini_provider.py` to handle API connection and error handling.
    - Update `tools/lib/interface.py` to add an `api` mode that utilizes `GeminiProvider`.
    - Ensure `ask_lead.py` constructs a "System Prompt" for the API request that enforces the "Lead DEV" persona (concise, architectural, authoritative).
4.  **Verification:** Run a test query: `python tools/ask_lead.py --mode api "What is the primary goal of M6?"`.

**Deliverables:**
- Functioning `api` mode in Bridge Layer.
- `.env` configuration support.

---

### Phase 2: The Heartbeat (Infinity Loop Script)

**Goal:** Enable the system to restart itself with fresh context, bypassing the implementation agent's finite context window.

**Context for Senior DEV:**
- Read `tools/handoff.py`.
- Read `hmas_boot.sh`.

**Tasks:**
1.  **Handoff Upgrade:** Modify `tools/handoff.py` to accept an `--auto` flag.
    - If `--auto` is present, write the generated prompt to `.gemini/next_context.txt` instead of stdout.
    - Print a simple confirmation message.
2.  **Loop Script:** Create `hmas_loop.sh` (The Infinity Loop).
    - **Logic:**
        1. Source environment variables.
        2. Run the initial boot (`hmas_boot.sh`) if starting fresh, or check for `next_context.txt`.
        3. **Loop Start:**
        4. Copy current context (from boot or file) to clipboard (using `pbcopy`, `xclip`, or `clip.exe`).
        5. Launch `claude` (interactive session).
        6. **Wait** for session exit.
        7. Check for `.gemini/next_context.txt`.
        8. If found: Load content, delete file, repeat Loop.
        9. If not found: Prompt user ("Exit or Restart?").
3.  **Permissions:** Ensure `hmas_loop.sh` is executable.

**Deliverables:**
- `hmas_loop.sh`
- Updated `tools/handoff.py`

---

### Phase 3: The Protocol (Command Macros)

**Goal:** Teach the Senior DEV (Claude) to use short-hand commands to interact with the Bridge, improving speed and reducing token usage.

**Context for Senior DEV:**
- Read `hmas_boot.sh` (where the System Prompt lives).
- Read `tools/handoff.py` (where the Context Renewal prompt lives).

**Tasks:**
1.  **Define Macros:** Establish the following syntax:
    - `>> STATUS` $\rightarrow$ `python tools/status_check.py`
    - `>> DONE` $\rightarrow$ `python tools/report_progress.py --phase <Current> --status done`
    - `>> BLOCK` $\rightarrow$ `python tools/report_progress.py --phase <Current> --status blocked`
    - `>> ASK <Query>` $\rightarrow$ `python tools/ask_lead.py "<Query>"`
    - `>> HANDOFF` $\rightarrow$ `python tools/handoff.py --auto` (and then exit)
2.  **Update Prompts:**
    - Modify the HEREDOC prompt in `hmas_boot.sh` to include a "COMMAND PROTOCOLS" section.
    - Modify the prompt generator in `tools/handoff.py` to include the same section.
3.  **Documentation:** Update `tools/README.md` to reflect these macros.

**Deliverables:**
- Updated System Prompts enforcing macro usage.

---

### Phase 4: The Pilot (Validation)

**Goal:** Validate the entire "Neural Link" loop by building a dummy feature without manual context transfer.

**Context for Senior DEV:**
- Full system capability (M1-M6 features).

**Tasks:**
1.  **Setup:** Create a new folder `tests/pilot_m6/`.
2.  **Execution (The Loop):**
    - **Cycle 1:** Start `hmas_loop.sh`. Use `>> ASK` to generate a small "Hello World" spec for the pilot. Implement Phase 1 of pilot. Run `>> HANDOFF`. Exit session.
    - **Cycle 2:** (Loop should auto-restart). Verify context is present. Implement Phase 2 of pilot. Run `>> DONE`.
3.  **Audit:** Run `tools/status_check.py` to ensure the "Neural Link" (API) correctly logged the progress.

**Deliverables:**
- `docs/99_audit/M6_Pilot_Log.md` (Logs of the automated interaction).
- Validated `hmas_loop.sh` workflow.
