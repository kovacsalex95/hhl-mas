# Global Architecture

## Technology Stack
- **AI Agents:** Gemini CLI (Lead DEV), Claude Code (Senior DEV).
- **Bridge Layer:** Python 3.x scripts (`tools/`) for inter-agent communication.
- **Environment:** Linux / CLI.
- **Documentation:** Markdown-based tracking in `docs/` and `.gemini/`.

## Core Principles
1. **Decoupled Strategy & Execution:** Lead DEV plans, Senior DEV executes.
2. **Pull-Based Interaction:** Senior DEV queries Lead DEV for instructions; Lead DEV does not "push" commands.
3. **Atomic Commits:** Every phase completion in a Technical Plan corresponds to a git commit.
4. **Auditability:** Every decision must be traceable through documentation.

## The Bridge Layer
To prevent context bloat, the Senior DEV uses lightweight tools to query the Lead DEV's global context.

- **Location:** `tools/` directory.
- **Mechanism:** Python scripts that parse local state and query the Lead DEV agent via API or CLI hooks.
- **Key Tools:**
    - `ask_lead`: Fetches clarification or architectural decisions.
    - `status_check`: Validates progress against the active plan.