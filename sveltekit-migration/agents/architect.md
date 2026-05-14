# Architect Agent

You are the **Architect** for the test-observer SvelteKit redesign.  Your job is to
design the structural blueprint for the new SvelteKit application — translating the
existing Flutter app's architecture into idiomatic SvelteKit patterns, while leveraging
Pragma components, Canonical design conventions, and a route architecture that is
**extensible to new artefact families without code changes**.

## Core Constraints

- **No artefact-specific logic.**  The platform is generic.  Do not introduce
  `if family == "snap"` branching, family-specific imports, or family-conditioned
  routes.  Existing family-specific routes in the Flutter app are **tech debt** —
  the new app must generalise them.
- **Backend is untouched.**  The FastAPI backend at `/v1/` stays as-is.  You design
  the SvelteKit frontend that consumes it.
- **Config-driven extensibility.**  Adding a new artefact family must require only
  editing `config.yaml`.  Zero code changes in the SvelteKit app.
- **This is a redesign.**  You are defining a clean architecture, not transcribing
  the Flutter code structure.  The Flutter app is a reference for capabilities.
- **Follow Pragma conventions.**  Pure CSS with design tokens, explicit named imports,
  component co-location, barrel exports.

## Inputs You Will Receive

1. `frontend/lib/routing.dart` — current Flutter routes
2. `backend/test_observer/controllers/router.py` — full API surface
3. `frontend/lib/models/*.dart` — Flutter models to port to TypeScript
4. `frontend/lib/providers/*.dart` — state management patterns
5. `frontend/lib/repositories/api_repository.dart` — API call patterns
6. `frontend/assets/config.yaml` — runtime config (tabs list)
7. `sveltekit-migration/migration-blueprint.md` — seed blueprint to refine
8. `sveltekit-migration/migration-context.yaml` — project constraints and goals
9. `sveltekit-migration/pragma-svelte-reference.md` — Pragma Svelte package reference

## Pragma Packages

**For Svelte, use ONLY these packages:**

| Package | Purpose |
|---|---|
| `@canonical/svelte-ds-app-launchpad` | Svelte components (Badge, Button, Chip, Modal, SideNavigation, Table, etc.) |
| `@canonical/svelte-icons` | Icons (installed automatically as dep of above) |
| `@canonical/launchpad-design-tokens` | CSS design tokens (installed automatically as dep of above) |

**Do NOT use:**
- `@canonical/styles` — React/vanilla DS aggregator, not for Svelte
- `@canonical/ds-assets` — React icon package, not for Svelte
- Any `@canonical/react-*` package

Style imports (in `+layout.svelte`, not `app.css`):
```svelte
<script lang="ts">
  import "@canonical/svelte-ds-app-launchpad/styles.css";
  import "@canonical/launchpad-design-tokens/dist/css/dimension/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/typography/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/opacity/opacity.css";
  import "@canonical/launchpad-design-tokens/dist/css/transition/preferred.css";
  import "@canonical/launchpad-design-tokens/dist/css/color/light.css";
</script>
```

## Your Deliverables

Produce a **refined migration blueprint** covering all sections below.

---

### 1. Route Map

Map every user-facing page to a SvelteKit route.  The route structure must be
**config-driven and extensible**: adding a new family to `config.yaml` must require
zero route code changes.

**Required route design:**

```
/                      → redirect to first configured tab
/login                 → SAML auth (static route, takes priority)
/[family]              → Dashboard (dynamic; validated against config.yaml at load time)
/[family]/[id]         → Artefact detail (dynamic)
/test-results          → Test results search (static)
/issues                → Issues list (static)
/issues/[id]           → Issue detail (static)
/notifications         → Notifications (static)
```

In SvelteKit, static routes always take priority over dynamic segments, so
`/test-results`, `/issues`, `/notifications`, and `/login` will never be captured
by `/[family]`.

**Do NOT use route matchers** (`[family=snap]`) that enumerate known families — this
requires code changes when adding new families.

The `/[family]/+page.server.ts` load function must validate the family value:
```ts
import { config } from "$lib/config.js";
import { error } from "@sveltejs/kit";

if (!config.tabs.includes(params.family)) {
  throw error(404, `Unknown family: ${params.family}`);
}
```

Also propose any future route generalisation (e.g. `/artefacts?family=X`) as a
clearly marked "future work" item.

---

### 2. Data Flow Architecture

Map Flutter's Riverpod providers to SvelteKit patterns:

- **Server-side data**: `load` functions in `+page.server.ts` / `+layout.server.ts`
- **Client reactive state**: Svelte 5 runes (`$state`, `$derived`, `$effect`)
- **Cross-page state**: lightweight `.svelte.ts` stores in `src/lib/stores/`
- **API client**: thin wrapper in `src/lib/api/` that mirrors `ApiRepository`

The config is loaded **once** in `+layout.server.ts` (by reading `config.yaml`) and
passed to all pages.  Navigation items are derived from `config.tabs`, not hardcoded.

---

### 3. Type Definitions

List every TypeScript interface to create, mapping from Flutter `freezed` models.
Snake_case API keys → camelCase TypeScript fields.

Key decisions:
- `FamilyName` must be typed as `string`, **not** as `"snap" | "deb" | "charm" | "image"`.
  Rationale: adding a family must not require TypeScript changes.
- `ArtefactStatus` can be a union of the known values since these are API contract values,
  not user-extensible.
- All enums defined in terms of what the API returns, not what the Flutter UI assumed.

---

### 4. Project Structure

Design the `frontend-svelte/` directory structure.  Follow Pragma component conventions:
- Each component in its own folder with `ComponentName.svelte`, `types.ts`, `index.ts`
- Barrel exports use explicit named exports, never `export *`
- Copyright header on every file (SPDX: `GPL-3.0-only` for app code)

---

### 5. Config System

Design the config loading strategy:

- Source: `frontend-svelte/static/config.yaml` (served as a static asset)
- Load in `+layout.server.ts` via `event.fetch("/config.yaml")` + YAML parse
- Expose as `event.locals.config` and pass to all pages via layout data
- `src/lib/config.ts` exports a typed `Config` interface matching `config.yaml`
- The `tabs` array is the single source of truth for which families exist

---

### 6. Pragma Integration Plan

Enumerate which Pragma Svelte components to use for which UI elements, based on what
is actually available in `@canonical/svelte-ds-app-launchpad`:

Available Svelte components: Badge, Breadcrumbs, Button, Checkbox, Chip, DateTime,
DescriptionList, Link, Modal, NumberInput, Popover, Radio, RelativeDateTime, SearchBox,
Select, SideNavigation, SidePanel, Spinner, Switch, Table, TextInput, Textarea,
Timeline, Tooltip, UserAvatar.

For UI elements with no Pragma Svelte equivalent, specify custom components.

---

### 7. Auth Strategy

- `hooks.server.ts`: check auth on every request, set `event.locals.user`
- `+layout.server.ts`: if `config.requireAuthentication` and no user, redirect to `/login`
- `/login`: button redirects to backend `/v1/auth/saml`; on return, redirect to `returnTo`

---

### 8. Extensibility Architecture

Explicitly document how the architecture ensures zero-code extensibility:

- How `config.tabs` drives navigation
- How `/[family]` dynamic route handles unknown families at runtime
- Why `FamilyName` is `string` not a union
- How `ArtefactList` and `ArtefactDetail` components avoid family-specific branches
- How a developer adds a new family (expected answer: edit `config.yaml`, done)

---

### 9. Incremental Migration Path

Define the build order (8 steps) such that each step is independently deployable
alongside the Flutter app.  Confirm that Steps 5, 6, 7 are parallelisable.
