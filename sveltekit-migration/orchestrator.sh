#!/usr/bin/env bash
# orchestrator.sh — Coordinate the test-observer SvelteKit redesign workflow
#
# Usage:
#   ./orchestrator.sh setup        — verify prerequisites
#   ./orchestrator.sh phase1       — instructions for Architect agent
#   ./orchestrator.sh phase2       — instructions for Designer agent
#   ./orchestrator.sh phase3 <N>   — instructions for Builder step N (1-8)
#   ./orchestrator.sh phase4       — run final QA validation
#   ./orchestrator.sh status       — show current migration state
#
# The agent personas are implemented as LLM instructions in agents/*.md.
# Use an AI assistant with the context files described in each phase command.
#
# GitHub token (read-only, for Pragma and design-system repos):
#   Default location: ~/.github_llm_ro_token
#   Override: export GITHUB_TOKEN_FILE=/path/to/token

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
    case "$NODE_VER" in
      v22.*|v24.*) ;;
      *) warn "Node 22 or 24 recommended (current: $NODE_VER)" ;;
    esac
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

  # GitHub token (for Pragma and design-system repos)
  GITHUB_TOKEN_FILE="${GITHUB_TOKEN_FILE:-$HOME/.github_llm_ro_token}"
  if [ -f "$GITHUB_TOKEN_FILE" ]; then
    TOKEN=$(cat "$GITHUB_TOKEN_FILE")
    # Check access to the public Pragma repo
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: token $TOKEN" \
      "https://api.github.com/repos/canonical/pragma")
    if [ "$STATUS" = "200" ]; then
      ok "GitHub token valid — Pragma repo accessible"
    else
      warn "GitHub token may be invalid or Pragma repo inaccessible (HTTP $STATUS)"
    fi
    # Check access to the private design-system repo
    DS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: token $TOKEN" \
      "https://api.github.com/repos/canonical/design-system")
    if [ "$DS_STATUS" = "200" ]; then
      ok "GitHub token valid — design-system repo accessible"
    else
      warn "design-system repo inaccessible (HTTP $DS_STATUS) — check token permissions"
    fi
  else
    warn "GitHub token not found at $GITHUB_TOKEN_FILE"
    warn "Agents won't be able to read the private design-system repo."
    warn "Set GITHUB_TOKEN_FILE=/path/to/token to override."
  fi

  # Backend health
  if curl -sf http://localhost:30000/health/live &>/dev/null; then
    ok "Backend is running at localhost:30000"
  else
    warn "Backend not running. Start with: docker compose up -d test-observer-db test-observer-api"
  fi

  log ""
  log "Agent instructions available:"
  for f in "$AGENTS"/*.md; do
    echo "  - $(basename "$f" .md)"
  done

  log ""
  log "Quick reference: $SCRIPT_DIR/pragma-svelte-reference.md"
  log "Ready to begin Phase 1 (Architecture)"
}

cmd_phase1() {
  log "=== PHASE 1: Architecture ==="
  log "Agent persona: $AGENTS/architect.md"
  log ""
  log "Provide these files as context to the Architect agent:"
  log "  - frontend/lib/routing.dart"
  log "  - frontend/lib/models/*.dart  (all model files)"
  log "  - frontend/lib/providers/     (for state pattern reference)"
  log "  - frontend/lib/repositories/api_repository.dart"
  log "  - frontend/assets/config.yaml"
  log "  - backend/test_observer/controllers/router.py"
  log "  - sveltekit-migration/migration-blueprint.md  (seed to refine)"
  log "  - sveltekit-migration/migration-context.yaml"
  log "  - sveltekit-migration/pragma-svelte-reference.md"
  log ""
  log "Expected output: refined migration-blueprint.md"
  log ""
  log "After Architect delivers, run QA Stage 1 review (qa.md)."
  log "If QA passes, set blueprint_approved: true in migration-context.yaml,"
  log "then run: ./orchestrator.sh phase2"
}

cmd_phase2() {
  APPROVED=$(read_ctx blueprint_approved)
  if [ "$APPROVED" != "True" ] && [ "$APPROVED" != "true" ]; then
    fail "Blueprint not approved. Complete Phase 1 and QA Stage 1 first."
  fi

  log "=== PHASE 2: Design ==="
  log "Agent persona: $AGENTS/designer.md"
  log ""
  log "Provide these files as context to the Designer agent:"
  log "  - sveltekit-migration/migration-blueprint.md  (approved)"
  log "  - sveltekit-migration/migration-context.yaml"
  log "  - sveltekit-migration/pragma-svelte-reference.md"
  log "  - frontend/lib/ui/  (all Flutter UI files — capability reference)"
  log "  - GitHub: https://github.com/canonical/design-system  (use token)"
  log ""
  log "Expected output: design-spec.md in sveltekit-migration/"
  log ""
  log "After Designer delivers, run QA Stage 2 review."
  log "If QA passes, set design_approved: true in migration-context.yaml,"
  log "then run: ./orchestrator.sh phase3 1"
}

cmd_phase3() {
  APPROVED=$(read_ctx design_approved)
  if [ "$APPROVED" != "True" ] && [ "$APPROVED" != "true" ]; then
    fail "Design not approved. Complete Phase 2 and QA Stage 2 first."
  fi

  STEP="${1:-}"
  if [ -z "$STEP" ]; then
    fail "Usage: $0 phase3 <step_number>  (1-8)"
  fi

  STEP_NAMES=(
    ""
    "Project scaffolding + app shell (config-driven nav)"
    "Auth hooks + login page"
    "Dashboard page (generic /[family] route)"
    "Artefact detail page"
    "Test results page"
    "Issues list + detail pages"
    "Notifications page"
    "Polish + a11y audit"
  )

  if [ "$STEP" -lt 1 ] || [ "$STEP" -gt 8 ]; then
    fail "Step must be 1-8"
  fi

  log "=== PHASE 3: Implementation — Step $STEP: ${STEP_NAMES[$STEP]} ==="
  log "Agent persona: $AGENTS/builder.md"
  log ""
  log "Provide to the Builder:"
  log "  - sveltekit-migration/migration-blueprint.md"
  log "  - sveltekit-migration/design-spec.md"
  log "  - sveltekit-migration/migration-context.yaml"
  log "  - sveltekit-migration/pragma-svelte-reference.md"
  log "  - Current frontend-svelte/ codebase (if step > 1)"
  log ""
  log "After Builder completes, run:"
  log "  cd frontend-svelte && bun run svelte-check && bun run biome check . && bun run vitest --run"
  log ""
  log "Run extensibility check:"
  log "  rg '\"snap\"\|\"deb\"\|\"charm\"\|\"image\"' frontend-svelte/src/ | wc -l  # must be 0"
  log ""
  log "Then run QA Stages 3+4."
  log "If QA passes, update migration-context.yaml current_step to $((STEP + 1)),"
  log "then run: ./orchestrator.sh phase3 $((STEP + 1))"
}

cmd_phase4() {
  log "=== PHASE 4: Final Validation ==="
  log "Agent persona: $AGENTS/qa.md"
  log ""

  SVELTE_DIR="$SCRIPT_DIR/../frontend-svelte"

  if [ ! -d "$SVELTE_DIR" ]; then
    fail "frontend-svelte/ not found. Complete Phase 3 first."
  fi

  log "1. Type checking..."
  (cd "$SVELTE_DIR" && bun run svelte-check --threshold error) \
    && ok "svelte-check passed" || warn "svelte-check has errors"

  log "2. Linting..."
  (cd "$SVELTE_DIR" && bun run biome check .) \
    && ok "biome passed" || warn "biome has issues"

  log "3. Unit tests..."
  (cd "$SVELTE_DIR" && bun run vitest --run) \
    && ok "tests passed" || warn "test failures"

  log "4. Extensibility check (no hardcoded family names)..."
  COUNT=$(cd "$SVELTE_DIR" && rg '"snap"\|"deb"\|"charm"\|"image"' src/ 2>/dev/null | wc -l || echo 0)
  if [ "$COUNT" -eq 0 ]; then
    ok "No hardcoded family names found in source code"
  else
    warn "Found $COUNT hardcoded family name occurrences — review for legitimacy"
  fi

  log "5. Architecture compliance..."
  (cd "$SVELTE_DIR" && bun run check:webarchitect 2>/dev/null) \
    && ok "webarchitect passed" \
    || warn "webarchitect issues (skip if not applicable to SvelteKit app)"

  log ""
  log "Review warnings above. If all clear, set current_phase: 4 in migration-context.yaml"
}

cmd_status() {
  log "Migration status:"
  echo ""
  echo "  Phase:      $(read_ctx current_phase)"
  echo "  Step:       $(read_ctx current_step)"
  echo "  Completed:  $(read_ctx completed_steps)"
  echo "  Arch OK:    $(read_ctx blueprint_approved)"
  echo "  Design OK:  $(read_ctx design_approved)"
  echo ""
  echo "  Deliverables:"
  # The seed blueprint always exists; show if it's been approved instead
  ARCH_DONE=$(read_ctx blueprint_approved)
  [ "$ARCH_DONE" = "True" ] || [ "$ARCH_DONE" = "true" ] \
    && echo "    [x] migration-blueprint.md (approved)" \
    || echo "    [ ] migration-blueprint.md (pending Architect)"
  [ -f "$SCRIPT_DIR/design-spec.md" ] \
    && echo "    [x] design-spec.md" \
    || echo "    [ ] design-spec.md"
  [ -d "$SCRIPT_DIR/../frontend-svelte" ] \
    && echo "    [x] frontend-svelte/" \
    || echo "    [ ] frontend-svelte/"
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
