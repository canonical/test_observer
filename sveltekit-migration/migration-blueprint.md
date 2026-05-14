# Migration Blueprint — test-observer Flutter → SvelteKit + UI Redesign

> This is the seed blueprint.  The **Architect agent** refines and finalises it before
> the Designer or Builder may proceed.

---

## 0. Guiding Principles

1. **Redesign, not port.** The Flutter UI is a reference for capabilities.  Layout,
   interaction patterns, information architecture, and visual language are all open
   to change.  Use Pragma components and Canonical design conventions as the basis
   for a new design.

2. **No artefact-specific logic.** No source file may contain a literal family name
   (`snap`, `deb`, `charm`, `image`) as a hard-coded string.  Family names come only
   from `config.yaml` at runtime.

3. **Config-driven extensibility.** Adding support for a new artefact family must
   require only editing `config.yaml`.  Zero code changes.

---

## 1. Route Map

### Current SvelteKit routes (seed — Architect may revise)

| URL pattern | SvelteKit file | Layout | Notes |
|---|---|---|---|
| `/` | `+page.svelte` | Root | Redirect to first configured tab |
| `/login` | `login/+page.svelte` | Blank | SAML auth redirect |
| `/[family]` | `[family]/+page.svelte` | Shell | Dashboard for any family. `family` is a dynamic segment validated against `config.yaml` tabs at load time — no matcher needed |
| `/[family]/[id]` | `[family]/[id]/+page.svelte` | Shell | Artefact detail |
| `/test-results` | `test-results/+page.svelte` | Shell | Test results search |
| `/issues` | `issues/+page.svelte` | Shell | Issues list |
| `/issues/[id]` | `issues/[id]/+page.svelte` | Shell | Issue detail |
| `/notifications` | `notifications/+page.svelte` | Shell | User notifications |

**Key design decision:** The route uses a single `/[family]` dynamic segment rather
than a family-specific matcher.  SvelteKit static routes (`/test-results`, `/issues`,
`/notifications`, `/login`) take priority over the dynamic `[family]` route, so there
is no ambiguity.  The load function for `/[family]` validates the segment against the
runtime config and returns a 404 if the family is not listed in `config.yaml`.

**Future work:** If the backend gains a generic `/v1/artefacts?family=X` endpoint
that supersedes the family-specific ones, the frontend routes can stay unchanged.

---

## 2. Project Structure

```
frontend-svelte/
├── package.json
├── svelte.config.js
├── vite.config.ts
├── tsconfig.json
├── biome.json
├── src/
│   ├── app.html
│   ├── app.d.ts
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts          # Generic fetch wrapper + ApiError
│   │   │   ├── artefacts.ts       # Artefact CRUD
│   │   │   ├── test-executions.ts # Test execution endpoints
│   │   │   ├── test-results.ts    # Test results endpoints
│   │   │   ├── issues.ts          # Issues CRUD + attach/detach
│   │   │   ├── environments.ts    # Environments endpoints
│   │   │   ├── users.ts           # Users + notifications
│   │   │   └── auth.ts            # Auth endpoints
│   │   ├── components/
│   │   │   ├── app-shell/
│   │   │   │   ├── AppShell.svelte
│   │   │   │   ├── Sidebar.svelte      # Nav items from config.yaml; no hardcoded families
│   │   │   │   ├── Header.svelte
│   │   │   │   └── index.ts
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardHeader.svelte
│   │   │   │   ├── ArtefactList.svelte    # Generic: works for any family
│   │   │   │   ├── ArtefactCard.svelte
│   │   │   │   ├── StageColumn.svelte
│   │   │   │   └── index.ts
│   │   │   ├── artefact-detail/
│   │   │   │   ├── ArtefactInfoSection.svelte
│   │   │   │   ├── TestExecutionSection.svelte
│   │   │   │   ├── EnvironmentSection.svelte
│   │   │   │   ├── BulkReviewDialog.svelte
│   │   │   │   └── index.ts
│   │   │   ├── test-results/
│   │   │   │   ├── TestResultsTable.svelte
│   │   │   │   ├── TestResultsFilters.svelte
│   │   │   │   ├── BulkOperationsBar.svelte
│   │   │   │   └── index.ts
│   │   │   ├── issues/
│   │   │   │   ├── IssueCard.svelte
│   │   │   │   ├── AttachmentRuleSection.svelte
│   │   │   │   └── index.ts
│   │   │   └── common/
│   │   │       ├── StatusBadge.svelte
│   │   │       ├── SearchBox.svelte
│   │   │       ├── ExpandableSection.svelte
│   │   │       └── index.ts
│   │   ├── stores/
│   │   │   ├── auth.svelte.ts       # Current user, auth state
│   │   │   ├── notifications.svelte.ts
│   │   │   └── ui.svelte.ts         # Sidebar state, density pref
│   │   ├── types/
│   │   │   ├── artefact.ts
│   │   │   ├── environment.ts
│   │   │   ├── issue.ts
│   │   │   ├── test-result.ts
│   │   │   ├── user.ts
│   │   │   ├── enums.ts             # StageName, ArtefactStatus, ViewModes
│   │   │   └── api.ts               # Paginated responses, ApiError
│   │   ├── utils/
│   │   │   ├── sorting.ts
│   │   │   ├── formatting.ts
│   │   │   └── filters.ts
│   │   └── config.ts                # Parsed config.yaml: tabs, requireAuthentication
│   └── routes/
│       ├── +layout.svelte           # AppShell; imports Pragma styles
│       ├── +layout.server.ts        # Auth check, shared data
│       ├── +page.svelte             # Redirect to first tab
│       ├── login/
│       │   └── +page.svelte
│       ├── [family]/
│       │   ├── +page.svelte         # Dashboard (generic — works for all families)
│       │   ├── +page.server.ts      # Validates family vs config; fetches artefacts
│       │   └── [id]/
│       │       ├── +page.svelte     # Artefact detail (generic)
│       │       └── +page.server.ts
│       ├── test-results/
│       │   ├── +page.svelte
│       │   └── +page.server.ts
│       ├── issues/
│       │   ├── +page.svelte
│       │   ├── +page.server.ts
│       │   └── [id]/
│       │       ├── +page.svelte
│       │       └── +page.server.ts
│       └── notifications/
│           ├── +page.svelte
│           └── +page.server.ts
```

---

## 3. Data Flow

### Server-side data loading
- `+layout.server.ts`: Check auth, fetch current user, notification count
- `+page.server.ts`: Pre-fetch page-specific data using `event.fetch`
- All API calls use `event.fetch` for SSR cookie forwarding

### Client-side state
- Svelte 5 runes for component-local state (filters, selections, form inputs)
- `.svelte.ts` stores for cross-page state (auth, UI preferences)
- `$effect` for side effects (API calls on filter change)

### Config loading
- `src/lib/config.ts` exports a `config` object parsed from `public/config.yaml` (static file served by SvelteKit) or from a `+layout.server.ts` load that reads `config.yaml` at startup.
- Navigation items and route validation both read from `config.tabs` — no other code knows which families exist.

### API client
```ts
// src/lib/api/client.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:30000";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  fetchFn: typeof fetch = fetch,
): Promise<T> {
  const response = await fetchFn(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.json();
}

export class ApiError extends Error {
  constructor(public status: number, body: string) {
    super(`API error ${status}: ${body}`);
  }
}
```

---

## 4. Pragma Integration

### Dependencies

```json
{
  "dependencies": {
    "@canonical/svelte-ds-app-launchpad": "^0.27.0"
  }
}
```

> `@canonical/svelte-icons` and `@canonical/launchpad-design-tokens` are direct
> dependencies of `@canonical/svelte-ds-app-launchpad` and will be installed
> automatically.  Do NOT add `@canonical/styles` or `@canonical/ds-assets` —
> those are for the React/vanilla Canonical DS, not the Svelte Launchpad package.

### Style setup (`+layout.svelte`)

```svelte
<script lang="ts">
  import "@canonical/svelte-ds-app-launchpad/styles.css";
  import "@canonical/launchpad-design-tokens/dist/css/dimension/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/typography/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/opacity/opacity.css";
  import "@canonical/launchpad-design-tokens/dist/css/transition/preferred.css";
  import "@canonical/launchpad-design-tokens/dist/css/color/light.css"; // or dark.css / system.css
</script>
```

### Component usage

```svelte
<script lang="ts">
  import { SideNavigation, Button, Badge, Chip, SearchBox } from "@canonical/svelte-ds-app-launchpad";
  import { SomeIcon } from "@canonical/svelte-icons";
</script>
```

### Custom components

Follow Pragma's BEM-like class namespace:
```css
.ds.artefact-card { ... }
.ds.artefact-card__name { ... }
.ds.artefact-card.negative { ... }
```

---

## 5. Auth Strategy

```
hooks.server.ts
  → on each request, call GET /v1/users/me with forwarded cookies
  → if 401 and require_authentication=true, redirect to /login
  → if 200, set event.locals.user

/login/+page.svelte
  → SAML redirect button: link to /v1/auth/saml
  → After SAML callback (redirects back to /login?returnTo=...), redirect to returnTo
```

---

## 6. Extensibility for New Artefact Families

The new UI achieves zero-code extensibility for new families via:

1. **Config-driven nav**: `Sidebar.svelte` reads `config.tabs` to render nav items.
   Tab label = family name (capitalised by the component, e.g. `snap` → `Snaps`).
   No icons or colours are specific to any family.

2. **Generic dynamic route**: `/[family]` handles all families.  The `+page.server.ts`
   load function reads `config.tabs` and returns a 404 if the family is not listed.

3. **Shared components**: `ArtefactList`, `ArtefactCard`, `ArtefactDetail` accept a
   `family: string` prop.  They never branch on its value.

4. **No enum for family names in frontend code**: The `FamilyName` type in TypeScript
   is defined as `string` (or `string & {}` for better inference), not a union of
   `"snap" | "deb" | "charm" | "image"`.  Adding a family requires no type changes.

---

## 7. Incremental Migration Path

| Step | Scope | Deployable? |
|------|-------|-------------|
| 1 | Scaffold + app shell (nav reads config.yaml) | Yes (empty pages) |
| 2 | Auth + login | Yes (auth flow works) |
| 3 | Dashboard (artefact list, cards, filters) | Yes (primary use case covered) |
| 4 | Artefact detail | Yes |
| 5 | Test results | Yes |
| 6 | Issues | Yes |
| 7 | Notifications | Yes |
| 8 | Polish + a11y audit | Yes (final) |

Both frontend apps (Flutter and SvelteKit) can coexist — they share the same backend
and SAML IdP.  Run the SvelteKit app on a different port (e.g. 30001) during development.
