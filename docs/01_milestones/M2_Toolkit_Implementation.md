# Milestone 2: Toolkit Implementation

## Objective
Implement the "Bridge Layer" tooling and refine the prompt kits to enable the pull-based HMAS workflow.

## Phases

### Phase 1: Core Scripts (Completed)
- [x] Implement `ask_lead.py`
- [x] Implement `report_progress.py`
- [x] Implement `status_check.py`

### Phase 2: Library & Support (Completed)
- [x] Implement `lib/` module structure
- [x] Create `config.yaml` and `requirements.txt`

### Phase 3: Toolkit Documentation (In Progress)
- [ ] Create `tools/README.md`
  - [ ] Document installation/requirements
  - [ ] Document usage for all 3 tools (arguments, outputs)
  - [ ] Document configuration options

## Deliverables
- [x] **Bridge Layer Tools** (`tools/`):
    - `ask_lead.py`: Context-aware query tool.
    - `report_progress.py`: Milestone tracking tool.
    - `status_check.py`: Drift detection tool.
- [x] **Prompt Kits** (`.gemini/prompts/`):
    - `lead_dev_system.md`: Reactive architect persona.
    - `senior_dev_system.md`: Proactive engineer persona.
    - `tool_specs.md`: Documentation for bridge tools.
- [ ] **Documentation**: `tools/README.md`

## Success Criteria
- [x] All scripts in `tools/` are executable and lint-free.
- [ ] Comprehensive documentation exists in `tools/README.md`.