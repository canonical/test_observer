# SvelteKit Redesign — Kickoff Guide

## What's been prepared

```
sveltekit-migration/
├── agents/
│   ├── orchestrator.md    # Coordinates all agents; read this first
│   ├── architect.md       # Designs routes, data flow, types, project structure
│   ├── designer.md        # Maps capabilities to Pragma components, defines visual language
│   ├── builder.md         # Implements the SvelteKit app (TypeScript, Svelte 5 runes)
│   └── qa.md              # Validates every deliverable at every stage
├── orchestrator.sh        # CLI helper to check prerequisites and show phase instructions
├── migration-blueprint.md # Seed blueprint (refined by Architect in Phase 1)
├── migration-context.yaml # Living state file (phase, step, issues, approvals)
└── pragma-svelte-reference.md  # Quick reference for Pragma Svelte package
```

## What this effort is

This is a **redesign**, not a port.  Goals:

1. Replace the Flutter frontend with SvelteKit
2. Apply Canonical design principles and the Pragma component framework
3. Make the UI ready for new artefact families with **zero code changes** — only
   `config.yaml` needs to be updated

Read `AGENTS.md` (repo root) and `migration-context.yaml` (`extensibility_goal`)
before starting.

---

## How to run the workflow

### Option A: VS Code Copilot Chat — Agent mode (recommended)

VS Code Copilot Chat in **Agent mode** handles each phase without copy-pasting
file contents — the agent reads files directly and can write output files.
Agent mode uses subagents internally, which is more billing-efficient than
running a single large-context model session.

**Setup:** Open the VS Code Copilot Chat panel, click the model-selector
dropdown at the bottom of the input box, and switch to **Agent** mode.
Use `#file:` to attach specific files; the agent can also browse `@workspace`.

**Each phase = a fresh chat session** (avoids context window exhaustion).
Phase 1 (Architecture) is already complete.

#### Phase 2 — Designer

Paste this into a new Agent-mode chat session:

```
Act as the Designer agent described in #file:sveltekit-migration/agents/designer.md

**Current state:** Phase 2 — Design. Blueprint is approved (Phase 1 complete).

**Your inputs:**
- Approved architecture: #file:sveltekit-migration/migration-blueprint.md
- Project goals & constraints: #file:sveltekit-migration/migration-context.yaml
- Pragma Svelte reference: #file:sveltekit-migration/pragma-svelte-reference.md
- Runtime config: #file:frontend/assets/config.yaml
- Flutter UI (capability reference only): read the files in frontend/lib/ui/
  using your file tools — you are redesigning, not porting.

**Deliverable:** Create sveltekit-migration/design-spec.md covering all
sections listed in your agent persona.

**Critical constraints:**
- No artefact-specific logic; no hardcoded family names (snap/deb/charm/image)
- Config-driven navigation: family list comes only from config.yaml
- Use only Pragma Svelte components (@canonical/svelte-ds-app-launchpad)
```

After `design-spec.md` is written, start a **new** chat session for QA:

```
Act as the QA agent described in #file:sveltekit-migration/agents/qa.md

Run the Stage 2 (Design Review) checklist against:
- #file:sveltekit-migration/design-spec.md
- #file:sveltekit-migration/migration-blueprint.md
- #file:sveltekit-migration/migration-context.yaml

Report all blockers, criticals, and warnings.
If no blockers, set design_approved: true in sveltekit-migration/migration-context.yaml.
```

#### Phase 3 — Builder (one chat session per step)

Start a **new** Agent-mode session for each step (1–8):

```
Act as the Builder agent described in #file:sveltekit-migration/agents/builder.md

Implement Step N: <step name from migration-blueprint.md>

**Your inputs:**
- #file:sveltekit-migration/migration-blueprint.md
- #file:sveltekit-migration/design-spec.md
- #file:sveltekit-migration/migration-context.yaml
- #file:sveltekit-migration/pragma-svelte-reference.md
- Current frontend-svelte/ codebase (read it with your file tools; skip on Step 1)

The project lives at frontend-svelte/ (create it on Step 1).
After completing the step, run these checks in the terminal:
  cd frontend-svelte && bun run svelte-check && bun run biome check . && bun run vitest --run
Also run: rg '"snap"\|"deb"\|"charm"\|"image"' frontend-svelte/src/ | wc -l  (must be 0)
Report the results.
```

After the Builder finishes each step, run QA in a **new** session:

```
Act as the QA agent described in #file:sveltekit-migration/agents/qa.md

Run QA Stages 3 and 4 for Step N against the current frontend-svelte/ codebase.
Reference: #file:sveltekit-migration/migration-blueprint.md
           #file:sveltekit-migration/design-spec.md
           #file:sveltekit-migration/migration-context.yaml

Report results. If QA passes (no blockers), update migration-context.yaml:
mark step N complete and advance current_step to N+1.
```

#### Phase 4 — Final QA

```
Act as the QA agent described in #file:sveltekit-migration/agents/qa.md

Run the full Phase 4 final validation against frontend-svelte/.
Reference: #file:sveltekit-migration/migration-blueprint.md
           #file:sveltekit-migration/design-spec.md
           #file:sveltekit-migration/migration-context.yaml

Run all validation commands in the terminal and report results.
```

### Option B: opencode

opencode drives each phase directly — no copy-pasting of file contents.

**Each phase = a fresh opencode conversation** (avoids context window exhaustion
across the full 8-step build).  Phase 1 (Architecture) is already complete.

#### Phase 2 — Designer
Start a new opencode conversation and say:

```
Read sveltekit-migration/agents/designer.md and act as that agent.
Your inputs are:
  - sveltekit-migration/migration-blueprint.md  (approved architecture)
  - sveltekit-migration/migration-context.yaml  (constraints and goals)
  - sveltekit-migration/pragma-svelte-reference.md
  - frontend/assets/config.yaml
  - frontend/lib/  (Flutter UI for capability reference only)
Produce design-spec.md in sveltekit-migration/ as instructed.
```

After the Designer produces `design-spec.md`, ask opencode to act as the QA
agent (`agents/qa.md`) and run Stage 2 validation.  On pass, set
`design_approved: true` in `migration-context.yaml`.

#### Phase 3 — Builder (one conversation per step)
Start a fresh opencode conversation for each step:

```
Read sveltekit-migration/agents/builder.md and act as that agent.
Implement Step N as described in sveltekit-migration/migration-blueprint.md
and sveltekit-migration/design-spec.md.
The project lives at frontend-svelte/ (create it on Step 1).
After completing the step, run the self-check commands and report results.
```

Run QA (Stage 3+4) at the end of each step by asking opencode to act as
`agents/qa.md`.  opencode can directly update `migration-context.yaml`
(mark steps completed, log issues).

#### Phase 4 — Final QA
```
Read sveltekit-migration/agents/qa.md.  Run the full Phase 4 final validation
against frontend-svelte/.
```

### Option B: Traditional AI assistant sessions

Each agent file is a **persona prompt** for a dedicated AI assistant session.
Copy-paste the agent file content + the relevant input files into the session.

1. **Architect** — `architect.md` + `./orchestrator.sh phase1` context → `migration-blueprint.md`
2. QA Stage 1 → mark `blueprint_approved: true`
3. **Designer** — `designer.md` + approved blueprint + Flutter UI → `design-spec.md`
4. QA Stage 2 → mark `design_approved: true`
5. **Builder** (one session per step) → code in `frontend-svelte/`
6. QA Stage 3+4 after each step

### Option C: Manual with orchestrator.sh

```bash
./orchestrator.sh setup     # verify prerequisites
./orchestrator.sh phase1    # instructions for Architect  [COMPLETE]
./orchestrator.sh phase2    # instructions for Designer (after blueprint approved)
./orchestrator.sh phase3 1  # instructions for Builder step 1
./orchestrator.sh phase4    # run final validation
./orchestrator.sh status    # current state
```

---

## Prep work before starting

### 1. Install tooling

```bash
# Node.js 22 or 24 (via nvm — do not install via snap)
nvm install 24 && nvm use 24

# Bun 1.3.9+ (do not install via snap)
curl -fsSL https://bun.sh/install | bash

# Verify
node --version   # v22.x or v24.x
bun --version    # 1.3.9+
```

### 2. Clone Pragma for Storybook reference

```bash
# The npm package is what gets installed in the app.
# Clone the repo only to run Storybook for visual component reference.
git clone https://github.com/canonical/pragma /tmp/pragma
cd /tmp/pragma && bun install

# Run Storybook for the Svelte launchpad package
cd packages/svelte/ds-app-launchpad
bun run storybook   # opens http://localhost:6006
```

The Svelte components available are:
Badge, Breadcrumbs, Button, Checkbox, Chip, DateTime, DescriptionList, Link,
Modal, NumberInput, Popover, Radio, RelativeDateTime, SearchBox, Select,
SideNavigation, SidePanel, Spinner, Switch, Table, TextInput, Textarea,
Timeline, Tooltip, UserAvatar — plus icons from `@canonical/svelte-icons`.

See `pragma-svelte-reference.md` for the full reference.

### 3. Start the backend

```bash
cd /path/to/project
docker compose up -d test-observer-db test-observer-api

# Verify
curl http://localhost:30000/health/live   # should return 200
```

### 4. Export API response shapes

With the backend seeded, capture actual API shapes for TypeScript type accuracy.
Use a family from `config.yaml` (any of: snap, deb, charm, image):

```bash
FAMILY=snap   # or deb, charm, image
curl "http://localhost:30000/v1/artefacts?family=$FAMILY" | python3 -m json.tool \
  > /tmp/api-artefacts.json
curl http://localhost:30000/v1/artefacts/1 | python3 -m json.tool \
  > /tmp/api-artefact-detail.json
curl "http://localhost:30000/v1/test-results" | python3 -m json.tool \
  > /tmp/api-test-results.json
curl http://localhost:30000/v1/issues | python3 -m json.tool \
  > /tmp/api-issues.json
```

### 5. Review the constraints

Read these before starting any agent session:
- `AGENTS.md` (repo root) — "no artefact-specific logic" constraint
- `migration-context.yaml` — `extensibility_goal` field
- `pragma-svelte-reference.md` — correct Pragma Svelte packages and imports

---

## Key decisions already made

| Decision | Choice | Rationale |
|---|---|---|
| Package manager | bun | Matches Pragma toolchain |
| Pragma Svelte package | `@canonical/svelte-ds-app-launchpad` v0.27.0 | Launchpad-tier Svelte components |
| CSS tokens | `@canonical/launchpad-design-tokens` | Bundled with above package |
| Icons | `@canonical/svelte-icons` | Bundled with above package |
| Style approach | Pure CSS, launchpad design tokens | Pragma convention |
| Route structure | Single `/[family]` dynamic route | Zero-code extensibility |
| Family type | `string` (not union) | Adding family = no TypeScript changes |
| State management | Svelte 5 runes; `.svelte.ts` stores for cross-page | Modern idiomatic Svelte |
| SvelteKit adapter | `adapter-node` | Self-hosted, Docker |
| API base URL | `VITE_API_BASE_URL` env var, default `http://localhost:30000` | |
| SvelteKit base path | `BASE_PATH` env var, default `/svelte` | Set `BASE_PATH=` (empty) to cut over |
| SAML handling | `hooks.server.ts` checks auth, redirects to backend `/v1/auth` | |
| Testing | vitest + Playwright browser mode | Pragma convention |

---

## Common pitfalls to watch for

1. **Don't import `@canonical/styles`.** For Svelte, import
   `@canonical/svelte-ds-app-launchpad/styles.css` and
   `@canonical/launchpad-design-tokens/dist/css/...` instead.

2. **Don't import `@canonical/ds-assets`.** For icons in Svelte, use
   `@canonical/svelte-icons`.

3. **Don't use `SideNavigation` as `Navigation`.** The component is called
   `SideNavigation` in the Svelte package, not `Navigation`.

4. **Don't hardcode family names in source code.** No `"snap"`, `"deb"`, `"charm"`,
   or `"image"` in `.svelte` or `.ts` files.  Family names come from `config.yaml`.

5. **Don't use route matchers that enumerate families.**  `/[family=snap]` defeats
   the extensibility goal.  Use `/[family]` with runtime validation instead.

6. **Don't duplicate dashboard code per family.**  One `[family]` route, one Dashboard
   component, one ArtefactList component — all family-agnostic.

7. **Don't use `export *` in barrel files.**  Pragma convention requires explicit
   named exports.

8. **Don't skip copyright headers.**  Every file needs SPDX headers.
   The REUSE tool enforces this in CI.

9. **Don't hardcode `/svelte` in source code.**  The base path comes from
   `svelte.config.js` via `process.env.BASE_PATH`.  Use `base` imported from
   `$app/paths` whenever constructing a URL or checking the current path.
   `href="/svelte/issues"` is wrong; `href="{base}/issues"` is correct.
   Forgetting this is the most common cause of broken links after a cutover.
