#!/usr/bin/env bash
#
# hmas_loop.sh - HMAS Infinity Loop
#
# Part of the HMAS Neural Link (Milestone 6).
#
# This script enables automatic session context renewal, bypassing the
# implementation agent's finite context window by restarting Claude with
# fresh context.
#
# Usage:
#   ./hmas_loop.sh              # Start the loop (uses hmas_boot.sh for initial context)
#   ./hmas_loop.sh --fresh      # Force fresh start (ignore existing next_context.txt)
#
# The Loop:
#   1. Generate/load context prompt
#   2. Copy to clipboard
#   3. Launch Claude session
#   4. Wait for session exit
#   5. Check for .gemini/next_context.txt
#   6. If found: load and loop
#   7. If not found: prompt user

set -e

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CONTEXT_FILE="$PROJECT_ROOT/.gemini/next_context.txt"
BOOT_SCRIPT="$PROJECT_ROOT/hmas_boot.sh"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Loop counter
CYCLE_COUNT=0

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[LOOP]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[LOOP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[LOOP]${NC} $1"
}

log_error() {
    echo -e "${RED}[LOOP]${NC} $1"
}

log_cycle() {
    echo -e "${CYAN}[CYCLE $CYCLE_COUNT]${NC} $1"
}

print_banner() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          HMAS - Hierarchical Multi-Agent System                ║"
    echo "║                    Infinity Loop (M6)                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# ============================================================================
# Clipboard Functions
# ============================================================================

copy_to_clipboard() {
    local content="$1"

    # Try various clipboard commands (Linux, macOS, WSL)
    if command -v xclip &> /dev/null; then
        echo "$content" | xclip -selection clipboard
        return 0
    elif command -v xsel &> /dev/null; then
        echo "$content" | xsel --clipboard --input
        return 0
    elif command -v pbcopy &> /dev/null; then
        echo "$content" | pbcopy
        return 0
    elif command -v wl-copy &> /dev/null; then
        echo "$content" | wl-copy
        return 0
    elif command -v clip.exe &> /dev/null; then
        echo "$content" | clip.exe
        return 0
    fi

    return 1
}

# ============================================================================
# Environment Setup
# ============================================================================

source_env() {
    if [ -f "$ENV_FILE" ]; then
        log_info "Sourcing environment from $ENV_FILE"
        set -a
        source "$ENV_FILE"
        set +a
    fi
}

check_dependencies() {
    local missing=()

    if ! command -v claude &> /dev/null; then
        missing+=("claude (Claude Code CLI)")
    fi

    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies:"
        for dep in "${missing[@]}"; do
            echo "  - $dep"
        done
        exit 1
    fi
}

# ============================================================================
# Context Management
# ============================================================================

generate_initial_context() {
    # Use hmas_boot.sh logic to generate initial context
    # We'll use handoff.py to generate context instead of boot prompt
    log_info "Generating initial context via handoff.py..."

    local context=""
    if [ -f "$PROJECT_ROOT/venv/bin/python" ]; then
        context=$("$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/tools/handoff.py" 2>/dev/null)
    elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
        context=$("$PROJECT_ROOT/.venv/bin/python" "$PROJECT_ROOT/tools/handoff.py" 2>/dev/null)
    else
        context=$(python3 "$PROJECT_ROOT/tools/handoff.py" 2>/dev/null)
    fi

    if [ -z "$context" ]; then
        log_error "Failed to generate initial context"
        exit 1
    fi

    echo "$context"
}

load_context_from_file() {
    if [ -f "$CONTEXT_FILE" ]; then
        cat "$CONTEXT_FILE"
        return 0
    fi
    return 1
}

consume_context_file() {
    if [ -f "$CONTEXT_FILE" ]; then
        rm -f "$CONTEXT_FILE"
        log_info "Consumed and removed context file"
    fi
}

# ============================================================================
# Main Loop
# ============================================================================

run_loop() {
    local force_fresh="$1"
    local context=""

    print_banner
    source_env
    check_dependencies

    # Initial context determination
    if [ "$force_fresh" = true ]; then
        log_info "Fresh start requested, ignoring existing context file"
        context=$(generate_initial_context)
    elif [ -f "$CONTEXT_FILE" ]; then
        log_info "Found existing context file, resuming..."
        context=$(load_context_from_file)
        consume_context_file
    else
        log_info "No existing context, generating initial context..."
        context=$(generate_initial_context)
    fi

    # Main loop
    while true; do
        CYCLE_COUNT=$((CYCLE_COUNT + 1))
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        log_cycle "Starting new Claude session"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""

        # Copy context to clipboard
        if copy_to_clipboard "$context"; then
            log_success "Context copied to clipboard (paste in Claude session)"
        else
            log_warn "Could not copy to clipboard"
            echo ""
            echo "─── CONTEXT START ───"
            echo "$context"
            echo "─── CONTEXT END ───"
            echo ""
        fi

        # Display context preview
        log_info "Context preview (first 5 lines):"
        echo "$context" | head -n 5
        echo "..."
        echo ""

        # Launch Claude session
        log_info "Launching Claude Code..."
        log_info "Paste the context from clipboard to initialize the session."
        echo ""

        cd "$PROJECT_ROOT"

        # Run Claude (this blocks until the session exits)
        if command -v claude &> /dev/null; then
            claude || true  # Don't exit loop on Claude error
        else
            log_error "Claude Code CLI not found"
            exit 1
        fi

        echo ""
        log_cycle "Claude session ended"

        # Check for next context
        if [ -f "$CONTEXT_FILE" ]; then
            log_success "Found next context file - preparing for renewal"
            context=$(load_context_from_file)
            consume_context_file
            log_info "Context loaded. Restarting in 3 seconds..."
            sleep 3
            continue
        fi

        # No context file - prompt user
        echo ""
        log_warn "No handoff context found (.gemini/next_context.txt)"
        echo ""
        echo "Options:"
        echo "  [R] Restart with fresh context"
        echo "  [Q] Quit the loop"
        echo ""
        read -p "Choice [R/Q]: " choice

        case "${choice^^}" in
            R|RESTART)
                log_info "Generating fresh context..."
                context=$(generate_initial_context)
                ;;
            Q|QUIT|EXIT)
                log_info "Exiting Infinity Loop"
                echo ""
                log_success "Total cycles completed: $CYCLE_COUNT"
                exit 0
                ;;
            *)
                log_warn "Invalid choice, restarting with fresh context..."
                context=$(generate_initial_context)
                ;;
        esac
    done
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    local force_fresh=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --fresh)
                force_fresh=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "HMAS Infinity Loop - Automatic session context renewal"
                echo ""
                echo "Options:"
                echo "  --fresh      Force fresh start (ignore existing context file)"
                echo "  -h, --help   Show this help message"
                echo ""
                echo "The Loop:"
                echo "  1. Load or generate context"
                echo "  2. Copy to clipboard"
                echo "  3. Launch Claude session"
                echo "  4. Wait for session exit"
                echo "  5. Check for .gemini/next_context.txt"
                echo "  6. If found: loop with new context"
                echo "  7. If not: prompt user to restart or quit"
                echo ""
                echo "To trigger a handoff from within Claude:"
                echo "  python tools/handoff.py --auto"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    run_loop "$force_fresh"
}

# Trap Ctrl+C for clean exit
trap 'echo ""; log_info "Interrupted. Exiting..."; exit 130' INT

main "$@"
