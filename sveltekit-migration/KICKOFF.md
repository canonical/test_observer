# SvelteKit Migration — Kickoff Guide

## What's been prepared

```
sveltekit-migration/
├── agents/
│   ├── architect.md       # Designs routes, data flow, types, project structure
│   ├── designer.md        # Maps Flutter → Pragma components, defines visual language
│   ├── builder.md         # Implements the SvelteKit app (TypeScript, Svelte 5 runes)
│   └── qa.md              # Validates every deliverable at every stage
├── orchestrator.sh        # CLI to drive phases, check prerequisites, show status
├── migration-context.yaml # Living state file (phase, step, issues, approvals)
└── migration-blueprint.md # Seed blueprint (to be refined by Architect agent)
```

## How to run the workflow

### Option A: AI assistant sessions (recommended)

Each agent file is a **system prompt** for a dedicated AI assistant session:

1. **Start the Architect session** — give it `architect.md` as system prompt + the context files listed in `orchestrator.sh phase1`. It produces `migration-blueprint.md`.
2. **Run QA** — give a session `qa.md` as system prompt + the blueprint. It runs Stage 1 checks.
3. **If QA passes**, mark `blueprint_approved: true` in `migration-context.yaml`.
4. **Start the Designer session** — give it `designer.md` + approved blueprint. It produces `design-spec.md`.
5. **Run QA Stage 2.** If passes, mark `design_approved: true`.
6. **Start Builder sessions** (one per step or parallel for independent steps). Give it `builder.md` + blueprint + design spec + current code.
7. **After each Builder step**, run QA Stages 3+4. Only proceed on pass.
8. **After all 8 steps**, run QA Phase 4 (final validation).

### Option B: Single-session orchestration

If your AI tool supports multi-agent delegation (e.g., Claude Code's Task tool), you can drive everything from one session using the orchestrator instructions. The orchestrator delegates to sub-agents with the appropriate persona file and context.

### Option C: Manual with orchestrator.sh

```bash
./orchestrator.sh setup     # verify prerequisites
./orchestrator.sh phase1    # get instructions for Architect
./orchestrator.sh phase2    # get instructions for Designer (after blueprint approved)
./orchestrator.sh phase3 1  # get instructions for Builder step 1
./orchestrator.sh phase4    # run final validation
./orchestrator.sh status    # check current state
```

## Prep work to do before starting

### 1. Install tooling

```bash
# Node.js 22+ (via nvm)
nvm install 24 && nvm use 24

# Bun 1.3.9+
curl -fsSL https://bun.sh/install | bash

# Verify
node --version   # v22+ or v24
bun --version    # 1.3.9+
```

### 2. Clone Pragma locally (for reference, not as a dependency)

```bash
git clone https://github.com/canonical/pragma.git /tmp/pragma
cd /tmp/pragma && bun install
# Browse packages/svelte/ds-app-launchpad/ for available Svelte components
```

### 3. Start the backend

```bash
cd /project
docker compose up -d test-observer-db
# Then either:
docker compose up -d test-observer-api   # full backend
# Or run directly:
cd backend && UV_DYNAMIC_VERSIONING_BYPASS=0.0.0 uv run uvicorn test_observer.main:app --port 30000
```

Verify: `curl http://localhost:30000/health/live` → 200

### 4. Screenshot the current Flutter app

Run the Flutter app and take screenshots of every page. These serve as the visual baseline for the Designer and for QA visual regression checks.

```bash
cd /project/frontend
flutter run -d chrome
# Navigate to: Dashboard, Artefact detail, Test results, Issues, Notifications
# Take screenshots of each
```

### 5. Export the Flutter app's JSON responses

For each page, capture the actual API response shapes. This ensures the TypeScript types are accurate.

```bash
# With the backend running and seeded:
curl http://localhost:30000/v1/artefacts?family=snap | python3 -m json.tool > /tmp/api-artefacts.json
curl http://localhost:30000/v1/artefacts/1 | python3 -m json.tool > /tmp/api-artefact-detail.json
curl http://localhost:30000/v1/test-results | python3 -m json.tool > /tmp/api-test-results.json
curl http://localhost:30000/v1/issues | python3 -m json.tool > /tmp/api-issues.json
# etc.
```

### 6. Review the "no artefact-specific logic" constraint

The biggest risk in this migration is accidentally re-implementing family-specific branching. Before starting, read the AGENTS.md constraint carefully and ensure every agent understands it. The QA agent specifically checks for this.

## Key decisions to make before starting

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Package manager | npm, pnpm, bun | **bun** (matches Pragma) |
| Component testing | vitest, playwright | **vitest** for unit, **playwright** for integration |
| CSS approach | vanilla CSS, Tailwind, CSS modules | **vanilla CSS with design tokens** (Pragma convention) |
| State management | runes only, svelte stores, external lib | **Runes in components, .svelte.ts stores for cross-page** |
| SvelteKit adapter | node, static, vercel | **adapter-node** (self-hosted, Docker) |
| API base URL config | env var, config.yaml, runtime | **VITE_API_BASE_URL env var** + fallback to config.yaml |
| SAML handling | SvelteKit hooks, backend proxy | **SvelteKit hooks** check auth, redirect to backend /v1/auth |

## Common pitfalls to watch for

1. **Don't import React Pragma packages.** Only `@canonical/svelte-ds-app-launchpad` and shared packages (styles, ds-types, ds-assets) work in Svelte.

2. **Don't use `export *`.** Pragma convention is explicit named exports in barrel files.

3. **Don't hardcode colors.** Use `var(--color-*)` CSS custom properties from `@canonical/styles`.

4. **Don't duplicate dashboard code across /snaps, /debs, /charms, /images.** These must all use the same `Dashboard` component with `family` as a parameter.

5. **Don't skip SSR.** Pragma components have SSR test requirements. All pages should work server-side.

6. **Don't forget copyright headers.** Every file needs the SPDX headers. The REUSE tool enforces this in CI.
