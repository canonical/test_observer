# Migration Blueprint — test-observer Flutter → SvelteKit

> This is a seed blueprint. The Architect agent should refine and finalize it.

## 1. Route Map

| Flutter Route | SvelteKit Route | Layout | Notes |
|---|---|---|---|
| `/` | `/` → redirect | Root layout | Redirect to first configured tab |
| `/login` | `/login` | Blank | SAML auth redirect |
| `/snaps` | `/[family=snaps]` | Shell layout | Dashboard view |
| `/snaps/:id` | `/[family=snaps]/[id]` | Shell layout | Artefact detail |
| `/debs` | `/[family=debs]` | Shell layout | Dashboard view |
| `/debs/:id` | `/[family=debs]/[id]` | Shell layout | Artefact detail |
| `/charms` | `/[family=charms]` | Shell layout | Dashboard view |
| `/charms/:id` | `/[family=charms]/[id]` | Shell layout | Artefact detail |
| `/images` | `/[family=images]` | Shell layout | Dashboard view |
| `/images/:id` | `/[family=images]/[id]` | Shell layout | Artefact detail |
| `/test-results` | `/test-results` | Shell layout | Test results search |
| `/issues` | `/issues` | Shell layout | Issues list |
| `/issues/:id` | `/issues/[id]` | Shell layout | Issue detail |
| `/notifications` | `/notifications` | Shell layout | User notifications |

**Future work:** Generalize `/[family]` → `/artefacts?family=X` with shared `[id]` detail route.

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
│   ├── app.css                    # @import "@canonical/styles"
│   ├── app.d.ts
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts          # Generic fetch wrapper
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
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   ├── Header.svelte
│   │   │   │   └── index.ts
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardHeader.svelte
│   │   │   │   ├── DashboardBody.svelte
│   │   │   │   ├── ArtefactCard.svelte
│   │   │   │   ├── ArtefactListView.svelte
│   │   │   │   ├── ArtefactColumnsView.svelte
│   │   │   │   ├── StageColumn.svelte
│   │   │   │   └── index.ts
│   │   │   ├── artefact-detail/
│   │   │   │   ├── ArtefactInfoSection.svelte
│   │   │   │   ├── TestExecutionExpandable.svelte
│   │   │   │   ├── EnvironmentExpandable.svelte
│   │   │   │   ├── EnvironmentReviewersAvatars.svelte
│   │   │   │   ├── BulkEnvironmentReviewDialog.svelte
│   │   │   │   ├── ManualTestButton.svelte
│   │   │   │   └── index.ts
│   │   │   ├── test-results/
│   │   │   │   ├── TestResultsTable.svelte
│   │   │   │   ├── TestResultsFilters.svelte
│   │   │   │   ├── BulkOperationButtons.svelte
│   │   │   │   ├── CreateAttachmentRuleForm.svelte
│   │   │   │   ├── BulkModifyRerunsForm.svelte
│   │   │   │   ├── BulkIssueAttachmentForm.svelte
│   │   │   │   └── index.ts
│   │   │   ├── issues/
│   │   │   │   ├── IssueCard.svelte
│   │   │   │   ├── AttachmentRuleSection.svelte
│   │   │   │   └── index.ts
│   │   │   ├── common/
│   │   │   │   ├── StatusBadge.svelte
│   │   │   │   ├── MultiSelect.svelte
│   │   │   │   ├── ExpandableSection.svelte
│   │   │   │   ├── DialogModal.svelte
│   │   │   │   ├── SearchBar.svelte
│   │   │   │   ├── ViewModeToggle.svelte
│   │   │   │   └── index.ts
│   │   │   └── icons/
│   │   │       └── index.ts       # Re-exports from @canonical/ds-assets
│   │   ├── stores/
│   │   │   ├── auth.svelte.ts     # Current user, auth state
│   │   │   ├── notifications.svelte.ts
│   │   │   └── ui.svelte.ts       # Sidebar state, density pref
│   │   ├── types/
│   │   │   ├── artefact.ts
│   │   │   ├── environment.ts
│   │   │   ├── issue.ts
│   │   │   ├── test-result.ts
│   │   │   ├── user.ts
│   │   │   ├── enums.ts           # FamilyName, StageName, ViewModes
│   │   │   └── api.ts             # Paginated responses, error types
│   │   ├── utils/
│   │   │   ├── sorting.ts
│   │   │   ├── formatting.ts
│   │   │   └── filters.ts
│   │   └── config.ts              # Load from /config.yaml at build or runtime
│   └── routes/
│       ├── +layout.svelte         # AppShell
│       ├── +layout.server.ts      # Auth check, shared data
│       ├── +page.svelte           # Redirect to first tab
│       ├── login/
│       │   └── +page.svelte
│       ├── [family]/
│       │   ├── +page.svelte       # Dashboard
│       │   ├── +page.server.ts    # Fetch artefacts
│       │   └── [id]/
│       │       ├── +page.svelte   # Artefact detail
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

## 3. Data Flow

### Server-side data loading
- `+layout.server.ts`: Check auth, fetch user, notification count
- `+page.server.ts`: Pre-fetch page-specific data using `event.fetch`
- All API calls use `event.fetch` for SSR cookie forwarding

### Client-side state
- Svelte 5 runes for component-local state (filters, selections, form inputs)
- `.svelte.ts` stores for cross-page state (auth, UI preferences)
- `$effect` for side effects (API calls on filter change)
- No global state management library needed

### API client
- Single `apiFetch<T>(path, options, fetchFn)` wrapper
- Per-domain modules (artefacts.ts, issues.ts, etc.) with typed methods
- Error handling via `ApiError` class with status code
- Base URL from `VITE_API_BASE_URL` env var (default: `http://localhost:30000`)

## 4. Pragma Integration

```json
{
  "dependencies": {
    "@canonical/svelte-ds-app-launchpad": "^0.27.0",
    "@canonical/styles": "^0.27.0",
    "@canonical/ds-assets": "^0.27.0",
    "@canonical/ds-types": "^0.27.0"
  }
}
```

### Style setup (app.css)
```css
@import "@canonical/styles";
```

### Component usage
```svelte
<script lang="ts">
  import { Navigation } from "@canonical/svelte-ds-app-launchpad";
  import { Icon } from "@canonical/ds-assets";
</script>
```

### Custom components
Follow the `ds` class namespace pattern:
```css
.ds.artefact-card { ... }
.ds.artefact-card__name { ... }
.ds.artefact-card.negative { ... }
```

## 5. Auth Strategy

```
hooks.server.ts
  → on each request, call /v1/users/me with forwarded cookies
  → if 401 and require_authentication=true, redirect to /login
  → if 200, set event.locals.user

/login/+page.svelte
  → SAML redirect button: link to /v1/auth/saml
  → After SAML callback (redirects back to /login?returnTo=...), redirect to returnTo
```

## 6. Incremental Migration Path

| Step | Scope | Deployable? |
|------|-------|-------------|
| 1 | Scaffold + app shell | Yes (empty pages) |
| 2 | Auth + login | Yes (auth flow works) |
| 3 | Dashboard | Yes (primary use case covered) |
| 4 | Artefact detail | Yes |
| 5 | Test results | Yes |
| 6 | Issues | Yes |
| 7 | Notifications | Yes |
| 8 | Polish + a11y | Yes (final) |

Both frontend apps can coexist — they share the same backend and SAML IdP.
