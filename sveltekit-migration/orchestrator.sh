#!/usr/bin/env bash
# orchestrator.sh — Drive the Flutter-to-SvelteKit migration end-to-end
#
# Usage:
#   ./orchestrator.sh <phase> [step]
#   ./orchestrator.sh setup        — verify prerequisites
#   ./orchestrator.sh phase1       — run Architect (blueprint)
#   ./orchestrator.sh phase2       — run Designer (component mapping)
#   ./orchestrator.sh phase3 1     — run Builder step N (1-8)
#   ./orchestrator.sh phase4       — final QA validation
#   ./orchestrator.sh status       — show current migration state
#
# This script is a coordination layer. The actual agent personas are
# implemented as LLM agent instructions in agents/*.md. Use an
# MCP-capable AI assistant (Claude Code, Cursor, Windsurf) with the
# .mcp.json configuration from the Pragma repo to drive the agents.
#
# Alternatively, use each agent file as a system prompt for a dedicated
# agent session.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CTX="$SCRIPT_DIR/migration-context.yaml"
AGENTS="$SCRIPT_DIR/agents"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[orchestrator]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

read_ctx() {
  python3 -c "
import yaml, sys
with open('$CTX') as f:
    d = yaml.safe_load(f)
print(d.get('$1', ''))
"
}

write_ctx() {
  python3 -c "
import yaml, sys
key, val = sys.argv[1], sys.argv[2]
with open('$CTX') as f:
    d = yaml.safe_load(f)
d[key] = val
with open('$CTX', 'w') as f:
    yaml.dump(d, f, default_flow_style=False)
" "$1" "$2"
}

cmd_setup() {
  log "Verifying prerequisites..."

  # Node
  if command -v node &>/dev/null; then
    NODE_VER=$(node --version)
    ok "Node $NODE_VER found"
  else
    fail "Node 22+ required. Install via nvm: nvm install 24"
  fi

  # Bun
  if command -v bun &>/dev/null; then
    BUN_VER=$(bun --version)
    ok "Bun $BUN_VER found"
  else
    warn "Bun not found. Install: curl -fsSL https://bun.sh/install | bash"
  fi

  # GitHub token for private repos
  if [ -f "$SCRIPT_DIR/../.github_llm_ro_token" ]; then
    TOKEN=$(cat "$SCRIPT_DIR/../.github_llm_ro_token")
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: token $TOKEN" "https://api.github.com/repos/canonical/pragma")
    if [ "$STATUS" = "200" ]; then
      ok "GitHub token valid — Pragma repo accessible"
    else
      fail "GitHub token invalid or Pragma repo inaccessible (HTTP $STATUS)"
    fi
  else
    fail "GitHub token not found at .github_llm_ro_token"
  fi

  # Backend health
  if curl -sf http://localhost:30000/health/live &>/dev/null; then
    ok "Backend is running at localhost:30000"
  else
    warn "Backend not running. Start with: docker compose up"
  fi

  log "Agent instructions available:"
  for f in "$AGENTS"/*.md; do
    echo "  - $(basename "$f" .md)"
  done

  log "Ready to begin Phase 1 (Architecture)"
}

cmd_phase1() {
  log "=== PHASE 1: Architecture ==="
  log "Agent: Architect ($AGENTS/architect.md)"
  log ""
  log "Provide these files as context to the Architect agent:"
  log "  - frontend/lib/routing.dart"
  log "  - frontend/lib/models/*.dart"
  log "  - frontend/lib/providers/*.dart"
  log "  - frontend/lib/repositories/api_repository.dart"
  log "  - frontend/assets/config.yaml"
  log "  - backend/test_observer/controllers/router.py"
  log "  - migration-context.yaml"
  log ""
  log "Expected output: migration-blueprint.md in $SCRIPT_DIR/"
  log ""
  log "After the Architect produces the blueprint, run QA Stage 1 review."
  log "If QA passes, update context: write_ctx blueprint_approved true"
  log "Then proceed to Phase 2."
}

cmd_phase2() {
  APPROVED=$(read_ctx blueprint_approved)
  if [ "$APPROVED" != "True" ] && [ "$APPROVED" != "true" ]; then
    fail "Blueprint not approved yet. Complete Phase 1 and QA first."
  fi

  log "=== PHASE 2: Design ==="
  log "Agent: Designer ($AGENTS/designer.md)"
  log ""
  log "Provide these files as context to the Designer agent:"
  log "  - migration-blueprint.md"
  log "  - frontend/lib/ui/**/*.dart"
  log "  - Pragma Svelte component docs (clone pragma repo)"
  log "  - Design System Ontology data files"
  log ""
  log "Expected output: design-spec.md in $SCRIPT_DIR/"
  log ""
  log "After the Designer produces the spec, run QA Stage 2 review."
  log "If QA passes, update context: write_ctx design_approved true"
  log "Then proceed to Phase 3."
}

cmd_phase3() {
  APPROVED=$(read_ctx design_approved)
  if [ "$APPROVED" != "True" ] && [ "$APPROVED" != "true" ]; then
    fail "Design not approved yet. Complete Phase 2 and QA first."
  fi

  STEP="${1:-}"
  if [ -z "$STEP" ]; then
    fail "Usage: $0 phase3 <step_number>  (1-8)"
  fi

  STEP_NAMES=(
    ""                       # 0-index placeholder
    "Project scaffolding + app shell"
    "Auth hooks + login page"
    "Dashboard page"
    "Artefact detail page"
    "Test results page"
    "Issues pages"
    "Notifications page"
    "Polish + a11y audit"
  )

  if [ "$STEP" -lt 1 ] || [ "$STEP" -gt 8 ]; then
    fail "Step must be 1-8"
  fi

  log "=== PHASE 3: Implementation — Step $STEP: ${STEP_NAMES[$STEP]} ==="
  log "Agent: Builder ($AGENTS/builder.md)"
  log ""
  log "Scope for step $STEP: ${STEP_NAMES[$STEP]}"
  log ""
  log "Provide these to the Builder:"
  log "  - migration-blueprint.md"
  log "  - design-spec.md"
  log "  - migration-context.yaml"
  log "  - Previous step's completed code (frontend-svelte/)"
  log ""
  log "After Builder completes, run:"
  log "  cd frontend-svelte && bun run svelte-check && bun run biome check . && bun run vitest --run"
  log ""
  log "Then run QA Stage 3+4 review."
  log "If QA passes, commit and update context:"
  log "  write_ctx current_step $((STEP + 1))"
}

cmd_phase4() {
  log "=== PHASE 4: Final Validation ==="
  log "Agent: QA ($AGENTS/qa.md)"
  log ""
  log "Running comprehensive validation..."
  log ""

  SVELTE_DIR="$SCRIPT_DIR/../frontend-svelte"

  if [ ! -d "$SVELTE_DIR" ]; then
    fail "frontend-svelte/ not found. Complete Phase 3 first."
  fi

  log "1. Type checking..."
  (cd "$SVELTE_DIR" && bun run svelte-check --threshold error) && ok "svelte-check passed" || warn "svelte-check has errors"

  log "2. Linting..."
  (cd "$SVELTE_DIR" && bun run biome check .) && ok "biome passed" || warn "biome has issues"

  log "3. Unit tests..."
  (cd "$SVELTE_DIR" && bun run vitest --run) && ok "tests passed" || warn "test failures"

  log "4. Architecture compliance..."
  (cd "$SVELTE_DIR" && bun run webarchitect package-svelte -v 2>/dev/null) && ok "webarchitect passed" || warn "webarchitect issues (install if needed)"

  log "5. Artefact-specific logic check..."
  COUNT=$(cd "$SVELTE_DIR" && grep -r "if.*family.*snap\|if.*family.*deb\|if.*family.*charm\|if.*family.*image" src/ 2>/dev/null | wc -l || echo 0)
  if [ "$COUNT" -eq 0 ]; then
    ok "No artefact-specific conditionals found in shared code"
  else
    warn "Found $COUNT artefact-specific conditionals — review for legitimacy"
  fi

  log ""
  log "Final validation complete. Review warnings above."
  log "If all clear, update: write_ctx current_phase 4"
}

cmd_status() {
  log "Migration status:"
  echo ""
  echo "  Phase:    $(read_ctx current_phase)"
  echo "  Step:     $(read_ctx current_step)"
  echo "  Done:     $(read_ctx completed_steps)"
  echo "  Arch OK:  $(read_ctx blueprint_approved)"
  echo "  Design OK: $(read_ctx design_approved)"
  echo ""
  echo "  Deliverables:"
  [ -f "$SCRIPT_DIR/migration-blueprint.md" ] && echo "    [x] migration-blueprint.md" || echo "    [ ] migration-blueprint.md"
  [ -f "$SCRIPT_DIR/design-spec.md" ] && echo "    [x] design-spec.md" || echo "    [ ] design-spec.md"
  [ -d "$SCRIPT_DIR/../frontend-svelte" ] && echo "    [x] frontend-svelte/" || echo "    [ ] frontend-svelte/"
}

case "${1:-status}" in
  setup)   cmd_setup ;;
  phase1)  cmd_phase1 ;;
  phase2)  cmd_phase2 ;;
  phase3)  cmd_phase3 "${2:-}" ;;
  phase4)  cmd_phase4 ;;
  status)  cmd_status ;;
  *)       echo "Usage: $0 {setup|phase1|phase2|phase3 <step>|phase4|status}" ;;
esac
