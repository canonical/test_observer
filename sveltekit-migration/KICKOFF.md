# SvelteKit Redesign — Kickoff Guide

## What's been prepared

```
.github/agents/
└── sveltekit-migration.agent.md  # VS Code orchestrator agent — drives the full migration

sveltekit-migration/
├── agents/
│   ├── orchestrator.md    # Orchestrator reference (persona prompts for subagents)
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

### Option A: VS Code Copilot Chat — Orchestrator Agent (recommended)

A single orchestrator agent drives the entire migration autonomously. It
delegates to specialised subagents (Designer, Builder, QA), manages hand-offs,
runs QA gates after every deliverable, and handles rework loops when QA fails.

**Setup:**

1. Open the VS Code Copilot Chat panel
2. Click the agent/mode selector at the bottom of the input box
3. Select **"SvelteKit Migration Orchestrator"** from the list
   (defined in `.github/agents/sveltekit-migration.agent.md`)

**Run it:**

```
Start the SvelteKit migration. Phase 1 (Architecture) is already complete.
Continue from the current state.
```

That's it. The orchestrator will:

1. Read `migration-context.yaml` to determine current state
2. Run the **Designer** subagent → produce `design-spec.md`
3. Run the **QA** subagent (Stage 2) → validate the design
4. If QA fails, rework: re-invoke Designer with QA findings (up to 3 retries)
5. On QA pass, advance to Phase 3 and run **Builder** subagent for each step (1-8)
6. After each Builder step, run **QA** subagent (Stage 3+4)
7. On QA failure, route back to Builder with specific fix instructions
8. After all 8 steps pass, run **QA** subagent (Phase 4 final validation)
9. Update `migration-context.yaml` at every transition

**The orchestrator handles:**
- **Hand-offs:** Automatically composes the right context for each subagent
- **QA gates:** Runs QA after every deliverable — nothing proceeds without passing
- **Rework loops:** Routes QA failures back to the responsible agent with specifics
- **Backtracking:** If a build-phase issue traces to a design flaw, routes back to Designer
- **State tracking:** Updates `migration-context.yaml` after each successful gate
- **Progress reporting:** Tells you what completed, what failed, what's next

**Manual intervention points:**
- The orchestrator asks for confirmation before starting the first subagent
- After 3 failed rework attempts on any issue, it stops and asks you for guidance
- You can pause at any time; the orchestrator resumes from `migration-context.yaml`

**Agent file locations:**
| Agent | File | Purpose |
|-------|------|---------|
| Orchestrator | `.github/agents/sveltekit-migration.agent.md` | Coordinates everything |
| Designer | `sveltekit-migration/agents/designer.md` | Persona used by subagent |
| Builder | `sveltekit-migration/agents/builder.md` | Persona used by subagent |
| QA | `sveltekit-migration/agents/qa.md` | Persona used by subagent |
| Architect | `sveltekit-migration/agents/architect.md` | Phase 1 (already complete) |

### Option B: VS Code Copilot Chat — Manual per-phase sessions

If you prefer manual control over each phase, you can run each agent in a
separate chat session. See the agent persona files in `sveltekit-migration/agents/`
for the prompts to use. The general pattern:

1. **Designer** — paste `agents/designer.md` persona + input files → `design-spec.md`
2. **QA Stage 2** — paste `agents/qa.md` persona → validate design
3. **Builder** (one session per step) — paste `agents/builder.md` persona → code
4. **QA Stage 3+4** after each step
5. **QA Stage 5** — final validation

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
