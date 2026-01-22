#!/usr/bin/env bash
#
# hmas_boot.sh - HMAS Master Bootloader
#
# Part of the HMAS Inception Engine (Milestone 4).
#
# This script initializes the HMAS environment and starts a Senior DEV session
# with the appropriate context pre-loaded.
#
# Usage:
#   ./hmas_boot.sh              # Normal boot (uses current milestone)
#   ./hmas_boot.sh --inception  # Start with inception prompt for new project
#   ./hmas_boot.sh --milestone M3  # Boot with specific milestone context
#   ./hmas_boot.sh --check      # Only run environment checks, don't start session
#
# Requirements:
#   - Python 3.8+
#   - Claude Code CLI (claude command)
#   - Git

set -e

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_DIR="$PROJECT_ROOT/.venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/tools/requirements.txt"
MILESTONES_DIR="$PROJECT_ROOT/docs/01_milestones"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          HMAS - Hierarchical Multi-Agent System                ║"
    echo "║                    Environment Bootloader                      ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# ============================================================================
# Environment Checks
# ============================================================================

check_python() {
    log_info "Checking Python installation..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            log_success "Python $PYTHON_VERSION found"
            return 0
        else
            log_error "Python 3.8+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        log_error "Python 3 not found"
        return 1
    fi
}

check_claude() {
    log_info "Checking Claude Code CLI..."

    if command -v claude &> /dev/null; then
        log_success "Claude Code CLI found"
        return 0
    else
        log_warn "Claude Code CLI not found in PATH"
        log_info "Install with: npm install -g @anthropic-ai/claude-code"
        return 1
    fi
}

check_git() {
    log_info "Checking Git installation..."

    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        log_success "Git $GIT_VERSION found"
        return 0
    else
        log_error "Git not found"
        return 1
    fi
}

check_env_file() {
    log_info "Checking environment configuration..."

    if [ -f "$ENV_FILE" ]; then
        log_success "Environment file found: $ENV_FILE"
        return 0
    else
        log_warn "No .env file found (optional)"
        return 0
    fi
}

# ============================================================================
# Virtual Environment Management
# ============================================================================

setup_venv() {
    log_info "Setting up Python virtual environment..."

    if [ -d "$VENV_DIR" ]; then
        log_success "Virtual environment exists: $VENV_DIR"
    else
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        log_success "Virtual environment created"
    fi

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
}

install_dependencies() {
    log_info "Installing dependencies..."

    if [ -f "$REQUIREMENTS_FILE" ]; then
        pip install -q --upgrade pip
        pip install -q -r "$REQUIREMENTS_FILE"
        log_success "Dependencies installed from $REQUIREMENTS_FILE"
    else
        log_warn "No requirements.txt found at $REQUIREMENTS_FILE"
    fi
}

# ============================================================================
# Milestone Detection
# ============================================================================

detect_current_milestone() {
    # Find the highest numbered milestone file
    local latest=""
    local highest_num=0

    if [ -d "$MILESTONES_DIR" ]; then
        for f in "$MILESTONES_DIR"/M*_*.md; do
            if [ -f "$f" ]; then
                # Extract milestone number
                local filename=$(basename "$f")
                local num=$(echo "$filename" | sed -n 's/M\([0-9]*\)_.*/\1/p')
                if [ -n "$num" ] && [ "$num" -gt "$highest_num" ]; then
                    highest_num=$num
                    latest="$filename"
                fi
            fi
        done
    fi

    echo "$latest"
}

# ============================================================================
# Boot Prompt Generation
# ============================================================================

generate_boot_prompt() {
    local milestone_file="$1"
    local mode="$2"

    if [ "$mode" = "inception" ]; then
        cat << 'INCEPTION_PROMPT'
ACT AS: Senior DEV (HMAS Proactive Engineer).
MODE: Project Inception
TOOLS AVAILABLE: tools/ingest_brief.py

PROTOCOL:
1. Ask the user for their project brief (or accept a file path).
2. Run: python tools/ingest_brief.py "<brief or --file path>"
3. Review the generated ARCHITECTURE.md and M1_Init.md
4. Begin implementing Milestone 1.
INCEPTION_PROMPT
    else
        cat << MILESTONE_PROMPT
ACT AS: Senior DEV (HMAS Proactive Engineer).
CURRENT OBJECTIVE: Execute $milestone_file
SOURCE OF TRUTH: docs/01_milestones/$milestone_file

PROTOCOL:
1. Read the Milestone Specification above.
2. Verify your environment by running: python tools/status_check.py
3. START Phase 1 immediately.
4. Implement the requested tools in the \`tools/\` directory.
5. Report progress after each phase: python tools/report_progress.py
MILESTONE_PROMPT
    fi
}

copy_to_clipboard() {
    local content="$1"

    # Try various clipboard commands
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
    fi

    return 1
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local check_only=false
    local inception_mode=false
    local specific_milestone=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check)
                check_only=true
                shift
                ;;
            --inception)
                inception_mode=true
                shift
                ;;
            --milestone)
                specific_milestone="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --check        Only run environment checks"
                echo "  --inception    Start in inception mode for new project"
                echo "  --milestone M# Boot with specific milestone"
                echo "  -h, --help     Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    print_banner

    # Run environment checks
    log_info "Running environment checks..."
    echo ""

    local checks_passed=true

    check_python || checks_passed=false
    check_git || checks_passed=false
    check_claude || checks_passed=false
    check_env_file

    echo ""

    if [ "$checks_passed" = false ]; then
        log_error "Some environment checks failed"
        exit 1
    fi

    log_success "All critical checks passed"
    echo ""

    if [ "$check_only" = true ]; then
        log_info "Check-only mode, exiting"
        exit 0
    fi

    # Setup virtual environment
    setup_venv
    install_dependencies
    echo ""

    # Determine milestone
    local milestone_file=""
    if [ -n "$specific_milestone" ]; then
        # Find the specific milestone file
        milestone_file=$(ls "$MILESTONES_DIR"/${specific_milestone}_*.md 2>/dev/null | head -1)
        if [ -z "$milestone_file" ]; then
            log_error "Milestone $specific_milestone not found"
            exit 1
        fi
        milestone_file=$(basename "$milestone_file")
    else
        milestone_file=$(detect_current_milestone)
    fi

    # Generate boot prompt
    local boot_mode="normal"
    [ "$inception_mode" = true ] && boot_mode="inception"

    local prompt=""
    if [ "$inception_mode" = true ]; then
        prompt=$(generate_boot_prompt "" "inception")
        log_info "Mode: Project Inception"
    elif [ -n "$milestone_file" ]; then
        prompt=$(generate_boot_prompt "$milestone_file" "normal")
        log_info "Target: $milestone_file"
    else
        log_warn "No milestones found, switching to inception mode"
        prompt=$(generate_boot_prompt "" "inception")
    fi

    echo ""
    log_info "Boot prompt generated:"
    echo "─────────────────────────────────────────────────────────────────"
    echo "$prompt"
    echo "─────────────────────────────────────────────────────────────────"
    echo ""

    # Try to copy to clipboard
    if copy_to_clipboard "$prompt"; then
        log_success "Boot prompt copied to clipboard"
    else
        log_warn "Could not copy to clipboard (install xclip, xsel, or pbcopy)"
    fi

    echo ""
    log_info "Starting Claude Code session..."
    echo ""

    # Start Claude Code
    # Note: Claude Code doesn't have a direct --prompt flag, so the user
    # will need to paste the prompt. The clipboard copy helps with this.
    cd "$PROJECT_ROOT"

    if command -v claude &> /dev/null; then
        exec claude
    else
        log_error "Claude Code CLI not available"
        log_info "Please install Claude Code and run 'claude' manually"
        log_info "Then paste the boot prompt above to initialize the session"
        exit 1
    fi
}

# Run main function
main "$@"
