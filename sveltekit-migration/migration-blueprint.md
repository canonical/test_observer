# Migration Blueprint — test-observer Flutter → SvelteKit + UI Redesign

> **Refined by Architect agent.**  This document is the authoritative design
> reference for the Designer (Phase 2) and Builder (Phase 3).  Do not modify
> without re-running the QA Stage 1 checklist.

---

## 0. Guiding Principles

1. **Redesign, not port.** The Flutter UI is a reference for capabilities.
   Layout, interaction patterns, information architecture, and visual language
   are all open to change.  Use Pragma components and Canonical design
   conventions as the basis for a new design.

2. **No artefact-specific logic.** No source file may contain a literal family
   name (`snap`, `deb`, `charm`, `image`) as a hard-coded string.  Family
   names come only from `config.yaml` at runtime.

3. **Config-driven extensibility.** Adding support for a new artefact family
   must require only editing `config.yaml`.  Zero code changes in the
   SvelteKit app.

4. **Stage groups are data-driven.** The Flutter `familyStages()` function
   (which maps each family to a fixed set of stages) is **not ported**.
   Stages come from the API — the dashboard groups artefacts by the distinct
   `stage` values present in the fetched data.

---

## 1. Route Map

| URL pattern            | SvelteKit file                          | Layout | Notes |
|------------------------|-----------------------------------------|--------|-------|
| `/`                    | `+page.svelte`                          | Root   | Redirect to first configured tab |
| `/login`               | `login/+page.svelte`                    | Blank  | SAML auth redirect |
| `/[family]`            | `[family]/+page.svelte`                 | Shell  | Dashboard for any family; validated at load time |
| `/[family]/[id]`       | `[family]/[id]/+page.svelte`            | Shell  | Artefact detail; supports `?testExecutionId=&testResultId=` |
| `/test-results`        | `test-results/+page.svelte`             | Shell  | Test results search; all filters live in URL query params |
| `/issues`              | `issues/+page.svelte`                   | Shell  | Issues list |
| `/issues/[id]`         | `issues/[id]/+page.svelte`              | Shell  | Issue detail; supports `?attachmentRule=` |
| `/notifications`       | `notifications/+page.svelte`            | Shell  | User notifications |

**Key design decision:** A single `/[family]` dynamic segment handles all
families.  SvelteKit static routes (`/test-results`, `/issues`,
`/notifications`, `/login`) take priority over the dynamic segment, so there
is no ambiguity.

**No route matchers.**  Do NOT use `[family=snap]` or similar — this would
require code changes to add a family.

**Family validation in `[family]/+page.server.ts`:**
```ts
import { config } from "$lib/config.js";
import { error } from "@sveltejs/kit";

if (!config.tabs.includes(params.family)) {
  error(404, `Unknown family: ${params.family}`);
}
```

**Future work:** If the backend gains a generic `/v1/artefacts?family=X` query
param that supersedes family-specific routes, the frontend routes stay unchanged.
The backend already accepts `family` as a query param to `GET /v1/artefacts`.

---

## 2. Project Structure

```
frontend-svelte/
├── package.json                  # bun; @canonical/svelte-ds-app-launchpad ^0.27.0
├── svelte.config.js              # adapter-node
├── vite.config.ts
├── tsconfig.json                 # strict: true
├── biome.json                    # lint + format
├── static/
│   └── config.yaml               # copy of frontend/assets/config.yaml
├── src/
│   ├── app.html
│   ├── app.d.ts                  # App.Locals, App.PageData types
│   ├── hooks.server.ts           # auth check on every request
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts              # apiFetch, ApiError
│   │   │   ├── artefacts.ts           # Artefact CRUD + search + history
│   │   │   ├── test-executions.ts     # start, rerun, results, events
│   │   │   ├── test-results.ts        # search, submit
│   │   │   ├── test-cases.ts          # reported issues CRUD + search
│   │   │   ├── issues.ts              # issues CRUD, attach/detach, attachment-rules
│   │   │   ├── environments.ts        # search + reported issues CRUD
│   │   │   ├── execution-metadata.ts  # GET /v1/execution-metadata
│   │   │   ├── artefact-matching-rules.ts  # CRUD for matching rules
│   │   │   ├── teams.ts               # teams CRUD + members
│   │   │   ├── permissions.ts         # GET /v1/permissions
│   │   │   ├── applications.ts        # GET /v1/applications
│   │   │   ├── reports.ts             # GET /v1/reports (CSV download)
│   │   │   ├── users.ts               # users list, get, me
│   │   │   ├── notifications.ts       # notifications list, count, dismiss
│   │   │   └── auth.ts                # GET /v1/auth, GET /v1/version
│   │   ├── components/
│   │   │   ├── app-shell/
│   │   │   │   ├── AppShell.svelte
│   │   │   │   ├── Sidebar.svelte     # nav items from config.tabs; never hardcoded
│   │   │   │   ├── Header.svelte      # user avatar, notification badge
│   │   │   │   └── index.ts
│   │   │   ├── dashboard/
│   │   │   │   ├── ArtefactList.svelte      # generic; works for any family
│   │   │   │   ├── ArtefactCard.svelte      # generic; no family branching
│   │   │   │   ├── StageGroup.svelte        # groups artefacts by stage from data
│   │   │   │   ├── DashboardFilters.svelte
│   │   │   │   └── index.ts
│   │   │   ├── artefact-detail/
│   │   │   │   ├── ArtefactHeader.svelte
│   │   │   │   ├── BuildSection.svelte
│   │   │   │   ├── EnvironmentSection.svelte
│   │   │   │   ├── TestExecutionRow.svelte
│   │   │   │   ├── BulkReviewDialog.svelte
│   │   │   │   ├── VersionHistory.svelte
│   │   │   │   └── index.ts
│   │   │   ├── test-results/
│   │   │   │   ├── TestResultsTable.svelte
│   │   │   │   ├── TestResultsFiltersPanel.svelte
│   │   │   │   ├── BulkActionsBar.svelte
│   │   │   │   └── index.ts
│   │   │   ├── issues/
│   │   │   │   ├── IssueCard.svelte
│   │   │   │   ├── AttachmentRuleRow.svelte
│   │   │   │   ├── AttachmentRuleDialog.svelte
│   │   │   │   └── index.ts
│   │   │   └── common/
│   │   │       ├── StatusBadge.svelte        # maps ArtefactStatus → Pragma severity
│   │   │       ├── TestStatusChip.svelte     # maps TestExecutionStatus → Pragma severity
│   │   │       ├── ExpandableSection.svelte
│   │   │       ├── UserAvatar.svelte         # wraps Pragma UserAvatar
│   │   │       ├── NotificationBadge.svelte
│   │   │       └── index.ts
│   │   ├── stores/
│   │   │   ├── auth.svelte.ts          # current user, auth state
│   │   │   ├── notifications.svelte.ts # unread count (polled)
│   │   │   └── ui.svelte.ts            # sidebar open, density preference
│   │   ├── types/
│   │   │   ├── artefact.ts
│   │   │   ├── build.ts
│   │   │   ├── environment.ts
│   │   │   ├── test-execution.ts
│   │   │   ├── test-result.ts
│   │   │   ├── issue.ts
│   │   │   ├── attachment-rule.ts
│   │   │   ├── artefact-matching-rule.ts
│   │   │   ├── team.ts
│   │   │   ├── user.ts
│   │   │   ├── notification.ts
│   │   │   ├── filters.ts              # TestResultsFilters, IntListFilter
│   │   │   └── config.ts               # Config interface
│   │   ├── utils/
│   │   │   ├── url.ts                  # buildArtefactPath, buildIssuePath
│   │   │   ├── formatting.ts           # dates, labels
│   │   │   ├── execution-metadata.ts   # base64 encode/decode for query params
│   │   │   └── filters.ts              # TestResultsFilters ↔ URLSearchParams
│   │   └── config.ts                   # loadConfig(), Config interface re-export
│   └── routes/
│       ├── +layout.svelte              # AppShell; Pragma style imports
│       ├── +layout.server.ts           # load config.yaml; auth check
│       ├── +page.svelte                # redirect to first tab
│       ├── login/
│       │   └── +page.svelte
│       ├── [family]/
│       │   ├── +page.svelte            # Dashboard (generic)
│       │   ├── +page.server.ts         # validate family; fetch artefacts
│       │   └── [id]/
│       │       ├── +page.svelte        # Artefact detail (generic)
│       │       └── +page.server.ts     # fetch builds, env-reviews; read query params
│       ├── test-results/
│       │   ├── +page.svelte
│       │   └── +page.server.ts         # parse URL filter params; fetch results
│       ├── issues/
│       │   ├── +page.svelte
│       │   ├── +page.server.ts
│       │   └── [id]/
│       │       ├── +page.svelte
│       │       └── +page.server.ts     # fetch issue + attachment rules
│       └── notifications/
│           ├── +page.svelte
│           └── +page.server.ts
```

---

## 3. TypeScript Type Definitions

All snake_case API fields map to camelCase TypeScript fields.  SPDX header
`GPL-3.0-only` on every source file.

### `src/lib/types/artefact-matching-rule.ts`
```ts
// Matching rules that automatically link new artefact builds to test executions
export interface ArtefactMatchingRule {
  id: number;
  series?: string;
  repo?: string;
  source?: string;
  model?: string;
  project?: string;
  baseImageTag?: string;
  launchpadHosted?: boolean;
  // team association
  team?: TeamMinimal;
}

export interface TeamMinimal {
  id: number;
  name: string;
}

export interface ArtefactMatchingRulePatch {
  // partial update; all fields optional
  series?: string | null;
  repo?: string | null;
  source?: string | null;
  model?: string | null;
  project?: string | null;
  baseImageTag?: string | null;
  launchpadHosted?: boolean | null;
  teamId?: number | null;
}
```

### `src/lib/types/team.ts`
```ts
export interface Team {
  id: number;
  name: string;
}
```

### UI-only types (not in `types/` — defined inline where used)
```ts
// Replaces Flutter's ViewModes enum
export type ViewMode = "dashboard" | "list";
```

### `src/lib/types/config.ts`
```ts
export interface Config {
  requireAuthentication: boolean;
  tabs: string[];                   // e.g. ["snaps", "debs", "charms", "images"]
}
```

### `src/lib/types/artefact.ts`
```ts
export type ArtefactStatus = "APPROVED" | "MARKED_AS_FAILED" | "UNDECIDED";

// stage is a plain string derived from data — no enum, no per-family list
export interface Artefact {
  id: number;
  name: string;
  version: string;
  family: string;           // plain string — NOT a union of known families
  track: string;
  store: string;
  branch: string;
  series: string;
  repo: string;
  source: string;
  os: string;
  release: string;
  owner: string;
  sha256: string;
  imageUrl: string;
  status: ArtefactStatus;
  comment: string;
  stage: string;            // plain string; dashboard groups on distinct values
  allEnvironmentReviewsCount: number;
  completedEnvironmentReviewsCount: number;
  reviewers: User[];
  bugLink: string;
  dueDate?: string;         // ISO date string
  // derived:
  // remainingTestExecutionCount = allEnvironmentReviewsCount - completedEnvironmentReviewsCount
}

export interface ArtefactVersion {
  artefactId: number;
  version: string;
}

export interface ArtefactHistoryItem {
  artefactId: number;
  name: string;
  version: string;
  stage: string;
  createdAt: string;
}

export interface ArtefactHistory {
  count: number;
  items: ArtefactHistoryItem[];
}

export interface ArtefactSearchResult {
  artefacts: string[];
  count: number;
  limit: number;
  offset: number;
}
```

### `src/lib/types/build.ts`
```ts
export interface ArtefactBuild {
  id: number;
  architecture: string;
  revision: number | null;
  testExecutions: TestExecution[];
}

export interface ArtefactBuildMinimal {
  id: number;
  architecture: string;
  revision?: number;
}
```

### `src/lib/types/environment.ts`
```ts
export interface Environment {
  id: number;
  name: string;
  architecture: string;
}

export type EnvironmentReviewDecision =
  | "REJECTED"
  | "APPROVED_INCONSISTENT_TEST"
  | "APPROVED_UNSTABLE_PHYSICAL_INFRA"
  | "APPROVED_CUSTOMER_PREREQUISITE_FAIL"
  | "APPROVED_FAULTY_HARDWARE"
  | "APPROVED_ALL_TESTS_PASS";

export interface EnvironmentReviewArtefactBuild {
  id: number;
  architecture: string;
  revision: number | null;
}

export interface EnvironmentReview {
  id: number;
  artefactBuild: EnvironmentReviewArtefactBuild;
  environment: Environment;
  reviewComment: string;
  reviewDecision: EnvironmentReviewDecision[];
  reviewers: User[];
}

export interface EnvironmentIssue {
  id: number;
  environmentName: string;
  description: string;
  url: string | null;
  isConfirmed: boolean;
}

// Client-side derived: combines EnvironmentReview with its TestExecutions
export interface ArtefactEnvironment {
  review: EnvironmentReview;
  runsDescending: TestExecution[];  // sorted newest first
  // helpers: name = review.environment.name, arch = review.environment.architecture
}
```

### `src/lib/types/test-execution.ts`
```ts
export type TestExecutionStatus =
  | "FAILED"
  | "NOT_STARTED"
  | "NOT_TESTED"
  | "IN_PROGRESS"
  | "PASSED"
  | "ENDED_PREMATURELY";

export interface TestExecutionRelevantLink {
  id: number;
  label: string;
  url: string;
}

export interface TestExecution {
  id: number;
  ciLink: string | null;
  c3Link: string | null;
  status: TestExecutionStatus;
  environment: Environment;
  isRerunRequested: boolean;
  artefactBuildId?: number;
  testPlan: string;
  relevantLinks: TestExecutionRelevantLink[];
  createdAt: string;
  executionMetadata: ExecutionMetadata;
  isTriaged: boolean;
}

export interface TestEvent {
  eventName: string;
  timestamp: string;
  detail: string;
}

export interface RerunRequest {
  testExecutionId: number;
  ciLink: string;
}

// Client-side derived: TestExecution paired with its EnvironmentReview
// (ported from enriched_test_execution.dart; used in artefact detail view)
export interface EnrichedTestExecution {
  testExecution: TestExecution;
  environmentReview: EnvironmentReview;
}
```

### `src/lib/types/test-result.ts`
```ts
export type TestResultStatus = "FAILED" | "PASSED" | "SKIPPED";

export interface PreviousTestResult {
  status: TestResultStatus;
  version: string;
  artefactId: number;
  testExecutionId: number;
  testResultId: number;
}

export interface TestResult {
  id: number;
  name: string;
  status: TestResultStatus;
  createdAt: string;
  category: string;
  comment: string;
  templateId: string;
  ioLog: string;
  previousResults: PreviousTestResult[];
  issueAttachments: IssueAttachment[];
}

export interface TestResultWithContext {
  testResult: TestResult;
  testExecution: TestExecution;
  artefact: Artefact;
  artefactBuild: ArtefactBuildMinimal;
}

export interface TestResultsSearchResult {
  count: number;
  testResults: TestResultWithContext[];
}

export interface TestIssue {
  id: number;
  templateId: string;
  caseName: string;
  description: string;
  url: string;
}
```

### `src/lib/types/issue.ts`
```ts
export type IssueSource = "github" | "jira" | "launchpad";
export type IssueStatus = "unknown" | "closed" | "open";

export interface Issue {
  id: number;
  source: IssueSource;
  project: string;
  key: string;
  title: string;
  status: IssueStatus;
  url: string;
  autoRerunEnabled: boolean;
  testExecutionsCount: number;
}

export interface IssueWithContext extends Issue {
  attachmentRules: AttachmentRule[];
}
```

### `src/lib/types/attachment-rule.ts`
```ts
export interface AttachmentRule {
  id: number;
  enabled: boolean;
  families: string[];
  environmentNames: string[];
  testCaseNames: string[];
  templateIds: string[];
  executionMetadata: ExecutionMetadata;
  testResultStatuses: TestResultStatus[];
}

export interface AttachmentRuleFilters {
  families: string[];
  environmentNames: string[];
  testCaseNames: string[];
  templateIds: string[];
  executionMetadata: ExecutionMetadata;
  testResultStatuses: TestResultStatus[];
}

export interface IssueAttachment {
  issue: Issue;
  attachmentRule?: AttachmentRule;
}
```

### `src/lib/types/filters.ts`
```ts
// Discriminated union replacing Flutter's sealed IntListFilter
export type IntListFilter =
  | { type: "list"; values: number[] }
  | { type: "any" }
  | { type: "none" };

export interface ExecutionMetadata {
  data: Record<string, string[]>;
}

export interface TestResultsFilters {
  families: string[];
  testResultStatuses: TestResultStatus[];
  artefacts: string[];
  artefactIsArchived?: boolean;
  rerunIsRequested?: boolean;
  executionIsLatest?: boolean;
  environments: string[];
  testCases: string[];
  templateIds: string[];
  executionMetadata: ExecutionMetadata;
  issues: IntListFilter;
  assignees: IntListFilter;
  fromDate?: string;
  untilDate?: string;
  offset?: number;
  limit?: number;
}
```

### `src/lib/types/user.ts`
```ts
export interface User {
  id: number;
  name: string;
  email: string;
  launchpadHandle?: string;
}
```

### `src/lib/types/notification.ts`
```ts
export type NotificationType =
  | "USER_ASSIGNED_ARTEFACT_REVIEW"
  | "USER_ASSIGNED_ENVIRONMENT_REVIEW";

export interface UserNotification {
  id: number;
  userId: number;
  notificationType: NotificationType;
  targetUrl?: string;
  createdAt: string;
  dismissedAt?: string;
}
```

### `src/app.d.ts`
```ts
declare global {
  namespace App {
    interface Locals {
      user: User | null;
      config: Config;
    }
    interface PageData {
      user: User | null;
      config: Config;
    }
  }
}
```

### Notes on type decisions

- **`FamilyName` is `string`** — not `"snap" | "deb" | "charm" | "image"`.
  Adding a family requires zero TypeScript changes.
- **`StageName` is `string`** — the Flutter enum `StageName` and its
  `familyStages()` helper are not ported.  Stage values come from the API.
  The dashboard derives stage groups dynamically: `[...new Set(artefacts.map(a => a.stage))]`.
- **`ArtefactStatus` is a union** — these are API contract values, not
  user-extensible, so a union type is appropriate.
- **`ExecutionMetadata`** uses `Record<string, string[]>`.  The base64 encode/
  decode logic for URL query params lives in `src/lib/utils/execution-metadata.ts`.
- **`IntListFilter`** is a discriminated union (not a sealed class).  Helper
  functions live in `src/lib/utils/filters.ts`.

---

## 4. Data Flow Architecture

### Server-side loading
```
hooks.server.ts
  → every request: GET /v1/users/me with forwarded cookies
  → sets event.locals.user (null if unauthenticated)

+layout.server.ts
  → reads static/config.yaml (once per server start via import or fetch)
  → sets event.locals.config
  → if config.requireAuthentication && !locals.user → redirect /login
  → returns { user, config } to all pages

[family]/+page.server.ts
  → validate params.family ∈ config.tabs → error(404) if not
  → GET /v1/artefacts?family={params.family}
  → return { artefacts, family }

[family]/[id]/+page.server.ts
  → GET /v1/artefacts/{id}
  → GET /v1/artefacts/{id}/builds
  → GET /v1/artefacts/{id}/environment-reviews
  → GET /v1/artefacts/{id}/versions
  → read url.searchParams: testExecutionId, testResultId
  → return { artefact, builds, reviews, versions, activeTestExecutionId, activeTestResultId }

test-results/+page.server.ts
  → parse URL query params → TestResultsFilters
  → GET /v1/test-results with filter params
  → return { filters, results }

issues/+page.server.ts
  → GET /v1/issues (with optional query params)
  → return { issues }

issues/[id]/+page.server.ts
  → GET /v1/issues/{id}
  → read url.searchParams: attachmentRule
  → return { issue, activeAttachmentRuleId }
```

### Client-side state (Svelte 5 runes)
- Component-local state: `$state`, `$derived`, `$effect` in `.svelte` files
- Cross-route state: `.svelte.ts` stores in `src/lib/stores/`
  - `auth.svelte.ts`: current user (set from page data)
  - `notifications.svelte.ts`: unread count, polled every 60 s via `$effect`
  - `ui.svelte.ts`: sidebar open/collapsed, density preference

### Config loading
```ts
// +layout.server.ts
import { parse } from "yaml";
import { readFileSync } from "node:fs";

let _config: Config | null = null;

function loadConfig(): Config {
  if (_config) return _config;
  const raw = readFileSync("static/config.yaml", "utf-8");
  _config = parse(raw) as Config;
  return _config;
}
```
The `tabs` array from config is the **sole source of truth** for which families
exist.  No other code knows the list of families.

### API client
```ts
// src/lib/api/client.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:30000";

export async function apiFetch<T>(
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
  return response.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public readonly status: number, body: string) {
    super(`API error ${status}: ${body}`);
  }
}
```

### URL path helpers (`src/lib/utils/url.ts`)
```ts
// Never hardcodes family names; family is always a string parameter
export function artefactPath(
  family: string,
  artefactId: number,
  opts?: { testExecutionId?: number; testResultId?: number },
): string {
  const base = `/${family}/${artefactId}`;
  const params = new URLSearchParams();
  if (opts?.testExecutionId) params.set("testExecutionId", String(opts.testExecutionId));
  if (opts?.testResultId) params.set("testResultId", String(opts.testResultId));
  return params.size > 0 ? `${base}?${params}` : base;
}

export function issuePath(issueId: number, attachmentRuleId?: number): string {
  const base = `/issues/${issueId}`;
  if (attachmentRuleId) return `${base}?attachmentRule=${attachmentRuleId}`;
  return base;
}
```

---

## 5. Pragma Integration Plan

### Package dependencies
```json
{
  "dependencies": {
    "@canonical/svelte-ds-app-launchpad": "^0.27.0"
  }
}
```
`@canonical/svelte-icons` and `@canonical/launchpad-design-tokens` are
installed automatically as transitive dependencies.  Do NOT add them
explicitly, and do NOT add `@canonical/styles` or `@canonical/ds-assets`.

### Style setup (`+layout.svelte`)
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

### Component mapping

| UI element | Pragma component | Notes |
|---|---|---|
| Side navigation | `SideNavigation` | Items from `config.tabs`; never hardcoded |
| Artefact status | `Badge` with severity | `APPROVED`→`positive`, `MARKED_AS_FAILED`→`negative`, `UNDECIDED`→`neutral` |
| Test execution status | `Chip` with severity | `PASSED`→`positive`, `FAILED`→`negative`, `IN_PROGRESS`→`caution`, `NOT_STARTED`→`neutral` |
| Search box | `SearchBox` | Dashboard filter, test results filter |
| Test results table | `Table` | Paginated; bulk select via `Checkbox` |
| Bulk review dialog | `Modal` | Bulk environment review actions |
| Issue list | `Table` or card layout | `Link` for external issue URLs |
| Attachment rule dialog | `Modal` | Create/edit attachment rules |
| User avatar | `UserAvatar` | Header, reviewer display |
| Notifications badge | `Badge` | Unread count in header |
| Date display | `RelativeDateTime` | Test result timestamps |
| Loading states | `Spinner` | API call pending states |
| Status details popover | `Popover` | Hover detail on status chips |
| Environment review decision | `Select` | Review decision dropdown |
| Artefact detail expandables | `SidePanel` or custom | Build/env sections |
| Breadcrumbs | `Breadcrumbs` | Artefact detail page |
| Tooltips | `Tooltip` | Status explanations |
| Filter chips | `Chip` | Active filters in test results |
| Review decision checkboxes | `Checkbox` | Multi-decision review form |
| Timeline of test events | `Timeline` | Status update events in test execution |

### Custom components (no Pragma equivalent)

| Component | Why custom |
|---|---|
| `StageGroup.svelte` | Stage-grouped artefact layout (data-driven) |
| `StatusBadge.svelte` | Maps `ArtefactStatus` → Pragma `Badge` severity |
| `TestStatusChip.svelte` | Maps `TestExecutionStatus` → Pragma `Chip` severity |
| `ExpandableSection.svelte` | Collapsible build/environment rows |
| `BulkActionsBar.svelte` | Floating bar for bulk rerun/attach operations |
| `NotificationBadge.svelte` | Wraps Pragma `Badge` with polling logic |

Custom component CSS follows the `ds` namespace pattern:
```css
.ds.artefact-card { padding: var(--spacing-2); }
.ds.artefact-card.negative { border-color: var(--color-negative-border); }
.ds.stage-group__header { font-size: var(--font-size-small); }
```

---

## 6. Auth Strategy

```
hooks.server.ts
  → every request: GET /v1/users/me (with event.fetch for cookie forwarding)
  → 200 → set event.locals.user
  → 401 → set event.locals.user = null

+layout.server.ts
  → if config.requireAuthentication && !locals.user
       && url.pathname !== "/login"
    → redirect(302, `/login?returnTo=${encodeURIComponent(url.pathname + url.search)}`)
  → return { user: locals.user, config: locals.config }

/login/+page.svelte
  → "Sign in" button → link to /v1/auth/saml
  → after SAML callback (backend redirects to /login?returnTo=...)
  → on mount: if user already authenticated → redirect to returnTo
```

SAML IdP test credentials (dev only): `certbot`/`password`, `mark`/`password`.

---

## 7. Base Path Strategy

The SvelteKit UI is deployed **alongside** the existing Flutter UI, not as a
replacement.  The Flutter UI continues to serve its current URLs
(`/snaps`, `/debs`, `/charms`, `/images`, `/test-results`, `/issues`, etc.).
The SvelteKit UI is served from a different web root (`/svelte/` by default).

### Single source of truth: `BASE_PATH` env var

```js
// svelte.config.js
import adapter from "@sveltejs/adapter-node";

const config = {
  kit: {
    adapter: adapter(),
    paths: {
      // Change BASE_PATH="" (empty string) in production to cut over.
      // Zero code changes required — all links and redirects adapt automatically.
      base: process.env.BASE_PATH ?? "/svelte",
    },
  },
};

export default config;
```

**Deployment side-by-side (current):** `BASE_PATH=/svelte`  
**Cut over to SvelteKit as main UI:** `BASE_PATH=` (empty, or unset)

### Using `base` in application code

SvelteKit injects `base` everywhere it matters.  Rules for the Builder:

| Situation | What to write |
|---|---|
| `<a href>` tags in Svelte | `import { base } from '$app/paths'` → `href="{base}/issues"` |
| `goto()` calls (client navigation) | Use path without base: `goto('/issues')` — SvelteKit prepends base automatically |
| `redirect()` in server load | `import { base } from '$app/paths'` → `redirect(302, \`${base}/login\`)` |
| `url.pathname` matching | Strip base first: `url.pathname.replace(base, '')` or use `page.url` |
| Static asset fetch | `event.fetch('/config.yaml')` — SvelteKit resolves relative to origin, not base |

### URL helpers (`src/lib/utils/url.ts`)

```ts
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only
import { base } from "$app/paths";

export function artefactPath(
  family: string,
  artefactId: number,
  opts?: { testExecutionId?: number; testResultId?: number },
): string {
  const path = `${base}/${family}/${artefactId}`;
  const params = new URLSearchParams();
  if (opts?.testExecutionId) params.set("testExecutionId", String(opts.testExecutionId));
  if (opts?.testResultId) params.set("testResultId", String(opts.testResultId));
  return params.size > 0 ? `${path}?${params}` : path;
}

export function issuePath(issueId: number, attachmentRuleId?: number): string {
  const path = `${base}/issues/${issueId}`;
  if (attachmentRuleId) return `${path}?attachmentRule=${attachmentRuleId}`;
  return path;
}

export function familyPath(family: string): string {
  return `${base}/${family}`;
}
```

### Sidebar nav items

```svelte
<script lang="ts">
  import { base } from "$app/paths";
  import { SideNavigation } from "@canonical/svelte-ds-app-launchpad";

  const { tabs, currentPath }: Props = $props();

  const navItems = $derived([
    ...tabs.map(family => ({
      href: `${base}/${family}`,
      label: family.charAt(0).toUpperCase() + family.slice(1),
      active: currentPath.startsWith(`${base}/${family}`),
    })),
    { href: `${base}/test-results`, label: "Test Results", active: currentPath === `${base}/test-results` },
    { href: `${base}/issues`,       label: "Issues",       active: currentPath.startsWith(`${base}/issues`) },
    { href: `${base}/notifications`, label: "Notifications", active: currentPath === `${base}/notifications` },
  ]);
</script>

<SideNavigation items={navItems} />
```

### Root redirect

```ts
// src/routes/+page.server.ts
import { redirect } from "@sveltejs/kit";
import { base } from "$app/paths";
import type { PageServerLoad } from "./$types.js";

export const load: PageServerLoad = async ({ parent }) => {
  const { config } = await parent();
  const target = config.tabs.length > 0 ? `${base}/${config.tabs[0]}` : `${base}/test-results`;
  redirect(302, target);
};
```

### Login redirect

```ts
// src/hooks.server.ts (auth redirect portion)
import { base } from "$app/paths";
import { redirect } from "@sveltejs/kit";

if (config.requireAuthentication && !user && url.pathname !== `${base}/login`) {
  redirect(302, `${base}/login?returnTo=${encodeURIComponent(url.pathname + url.search)}`);
}
```

---

## 8. Extensibility Architecture

This is the primary design goal.  The following table shows exactly how each
extensibility requirement is met:

| Requirement | How it is met |
|---|---|
| Adding a new family requires only `config.yaml` change | `config.tabs` drives all family-aware code; no other source of truth |
| Nav renders new family automatically | `Sidebar.svelte` maps `tabs.map(f => ({ href: \`/${f}\`, label: capitalise(f) }))` |
| Dashboard works for new family | `/[family]/+page.server.ts` fetches `GET /v1/artefacts?family={params.family}` with the string from the URL |
| Artefact detail works for new family | `/[family]/[id]/+page.server.ts` uses `params.id`; no family branching |
| No TypeScript changes needed | `FamilyName` is `string`; `stage` is `string`; no union types enumerate families |
| Stage columns are correct for new family | Dashboard derives columns from `[...new Set(artefacts.map(a => a.stage))]` |
| 404 for unknown families | `+page.server.ts` checks `config.tabs.includes(params.family)` |

**How to add a new family (e.g. `kernel`):**
1. Edit `static/config.yaml`: add `- kernels` to `tabs`
2. Restart the SvelteKit server (or wait for hot-reload in dev)
3. Done.  `/kernels` dashboard, `/kernels/[id]` detail, and sidebar nav item
   all appear automatically.

---

## 9. API Client Coverage

All endpoints from `backend/test_observer/controllers/router.py`.

### `src/lib/api/artefacts.ts`
- `getArtefacts(family: string, fetch): Promise<Artefact[]>`
  → `GET /v1/artefacts?family={family}`
- `getArtefact(id: number, fetch): Promise<Artefact>`
  → `GET /v1/artefacts/{id}`
- `patchArtefact(id: number, patch: Partial<ArtefactPatch>, fetch): Promise<Artefact>`
  → `PATCH /v1/artefacts/{id}`
- `getArtefactBuilds(id: number, fetch): Promise<ArtefactBuild[]>`
  → `GET /v1/artefacts/{id}/builds`
- `getArtefactVersions(id: number, fetch): Promise<ArtefactVersion[]>`
  → `GET /v1/artefacts/{id}/versions`
- `getArtefactEnvironmentReviews(id: number, fetch): Promise<EnvironmentReview[]>`
  → `GET /v1/artefacts/{id}/environment-reviews`
- `patchEnvironmentReview(artefactId: number, reviewId: number, patch, fetch): Promise<EnvironmentReview>`
  → `PATCH /v1/artefacts/{id}/environment-reviews/{reviewId}`
- `bulkPatchEnvironmentReviews(artefactId: number, reviews, fetch): Promise<EnvironmentReview[]>`
  → `PATCH /v1/artefacts/{id}/environment-reviews`
- `searchArtefacts(params, fetch): Promise<ArtefactSearchResult>`
  → `GET /v1/artefacts/search`
- `getArtefactHistory(params, fetch): Promise<ArtefactHistory>`
  → `GET /v1/artefacts/history`

### `src/lib/api/test-executions.ts`
- `startTestExecution(data, fetch): Promise<void>`
  → `PUT /v1/test-executions/start-test`
- `createReruns(data, fetch): Promise<void>`
  → `POST /v1/test-executions/reruns`
- `deleteReruns(data, fetch): Promise<void>`
  → `DELETE /v1/test-executions/reruns`
- `getTestExecutionResults(id: number, fetch): Promise<TestResult[]>`
  → `GET /v1/test-executions/{id}/test-results`
- `getTestExecutionEvents(id: number, fetch): Promise<TestEvent[]>`
  → `GET /v1/test-executions/{id}/status_update`

### `src/lib/api/test-results.ts`
- `searchTestResults(filters: TestResultsFilters, fetch): Promise<TestResultsSearchResult>`
  → `GET /v1/test-results`
- `submitTestResult(testExecutionId: number, data, fetch): Promise<void>`
  → `POST /v1/test-executions/{id}/test-results`

### `src/lib/api/test-cases.ts`
- `getTestIssues(fetch): Promise<TestIssue[]>`
  → `GET /v1/test-cases/reported-issues`
- `createTestIssue(data, fetch): Promise<TestIssue>`
  → `POST /v1/test-cases/reported-issues`
- `updateTestIssue(id: number, data, fetch): Promise<TestIssue>`
  → `PUT /v1/test-cases/reported-issues/{id}`
- `deleteTestIssue(id: number, fetch): Promise<void>`
  → `DELETE /v1/test-cases/reported-issues/{id}`
- `searchTestCases(params, fetch): Promise<string[]>`
  → `GET /v1/test-cases`

### `src/lib/api/issues.ts`
- `getIssues(params, fetch): Promise<Issue[]>`
  → `GET /v1/issues`
- `createIssue(data, fetch): Promise<Issue>`
  → `PUT /v1/issues`
- `getIssue(id: number, fetch): Promise<IssueWithContext>`
  → `GET /v1/issues/{id}`
- `attachIssue(id: number, data, fetch): Promise<Issue>`
  → `POST /v1/issues/{id}/attach`
- `detachIssue(id: number, data, fetch): Promise<Issue>`
  → `POST /v1/issues/{id}/detach`
- `patchIssue(id: number, patch, fetch): Promise<IssueWithContext>`
  → `PATCH /v1/issues/{id}`
- `createAttachmentRule(issueId: number, data, fetch): Promise<AttachmentRule>`
  → `POST /v1/issues/{id}/attachment-rules`
- `deleteAttachmentRule(issueId: number, ruleId: number, fetch): Promise<void>`
  → `DELETE /v1/issues/{id}/attachment-rules/{ruleId}`
- `patchAttachmentRule(issueId: number, ruleId: number, patch, fetch): Promise<void>`
  → `PATCH /v1/issues/{id}/attachment-rules/{ruleId}`

### `src/lib/api/environments.ts`
- `searchEnvironments(params, fetch): Promise<string[]>`
  → `GET /v1/environments`
- `getEnvironmentIssues(fetch): Promise<EnvironmentIssue[]>`
  → `GET /v1/environments/reported-issues`
- `createEnvironmentIssue(data, fetch): Promise<EnvironmentIssue>`
  → `POST /v1/environments/reported-issues`
- `updateEnvironmentIssue(id: number, data, fetch): Promise<EnvironmentIssue>`
  → `PUT /v1/environments/reported-issues/{id}`
- `deleteEnvironmentIssue(id: number, fetch): Promise<void>`
  → `DELETE /v1/environments/reported-issues/{id}`

### `src/lib/api/execution-metadata.ts`
- `getExecutionMetadata(fetch): Promise<ExecutionMetadata>`
  → `GET /v1/execution-metadata`

### `src/lib/api/users.ts`
- `getCurrentUser(fetch): Promise<User | null>`
  → `GET /v1/users/me`
- `getUsers(params, fetch): Promise<User[]>`
  → `GET /v1/users`
- `getUser(id: number, fetch): Promise<User>`
  → `GET /v1/users/{id}`

### `src/lib/api/notifications.ts`
- `getNotifications(fetch): Promise<UserNotification[]>`
  → `GET /v1/users/me/notifications`
- `getUnreadNotificationCount(fetch): Promise<number>`
  → `GET /v1/users/me/notifications/count`
- `dismissNotification(id: number, fetch): Promise<UserNotification>`
  → `POST /v1/users/me/notifications/{id}/dismiss`

### `src/lib/api/auth.ts`
- `getVersion(fetch): Promise<{ version: string }>`
  → `GET /v1/version`

### `src/lib/api/artefact-matching-rules.ts`
- `getArtefactMatchingRules(fetch): Promise<ArtefactMatchingRule[]>`
  → `GET /v1/artefact-matching-rules`
- `createArtefactMatchingRule(data, fetch): Promise<ArtefactMatchingRule>`
  → `POST /v1/artefact-matching-rules`
- `patchArtefactMatchingRule(id: number, patch, fetch): Promise<ArtefactMatchingRule>`
  → `PATCH /v1/artefact-matching-rules/{id}`
- `deleteArtefactMatchingRule(id: number, fetch): Promise<void>`
  → `DELETE /v1/artefact-matching-rules/{id}`

### `src/lib/api/teams.ts`
- `getTeams(fetch): Promise<Team[]>`
  → `GET /v1/teams`
- `createTeam(data, fetch): Promise<Team>`
  → `POST /v1/teams`
- `getTeam(id: number, fetch): Promise<Team>`
  → `GET /v1/teams/{id}`
- `patchTeam(id: number, patch, fetch): Promise<Team>`
  → `PATCH /v1/teams/{id}`

### `src/lib/api/permissions.ts`
- `getPermissions(fetch): Promise<string[]>`
  → `GET /v1/permissions`

### `src/lib/api/applications.ts`
- `getApplications(fetch): Promise<unknown[]>`
  → `GET /v1/applications`

### `src/lib/api/reports.ts`
- `downloadReport(params, fetch): Promise<Blob>`
  → `GET /v1/reports` (returns CSV file via FileResponse)

> **Note:** Reports, teams, permissions, applications, and artefact-matching-rules
> are not currently called by the Flutter frontend.  The SvelteKit app should
> implement stubs (typed functions that call the API) in Phase 3 Step 8 (Polish),
> and expose admin UI for them only if explicitly scoped.  The API client
> functions are defined in Phase 3 Step 1 (scaffold) for completeness.

---

## 10. Incremental Migration Path

Both apps share the same backend and SAML IdP.  The SvelteKit app runs on port
30001 during development (Flutter stays on 30000 / 30001 as configured).

| Step | Scope | Deployable? | Parallelisable |
|------|-------|-------------|----------------|
| 1 | Scaffold: package.json, svelte.config.js, +layout.svelte (Pragma styles), Sidebar driven by config.tabs, empty pages, auth flow in hooks.server.ts | Yes (shell with nav) | — |
| 2 | Auth: login page, +layout.server.ts auth gate, redirect to /login, SAML return flow | Yes (auth works end-to-end) | No (needs Step 1) |
| 3 | Dashboard: `/[family]` route, ArtefactList, ArtefactCard, StageGroup (data-driven), filters | Yes (primary use case) | No (needs Step 2) |
| 4 | Artefact detail: `/[family]/[id]`, builds, environment reviews, bulk review dialog, version history | Yes | No (needs Step 3) |
| 5 | Test results: `/test-results`, full filter panel, bulk rerun/attach, issue attach | Yes | Yes (parallel w/ 6, 7) |
| 6 | Issues: `/issues`, `/issues/[id]`, attachment rules CRUD | Yes | Yes (parallel w/ 5, 7) |
| 7 | Notifications: `/notifications`, dismiss, unread count polling | Yes | Yes (parallel w/ 5, 6) |
| 8 | Polish: a11y audit, Biome clean, svelte-check zero errors, Docker build, adapter-node | Yes (final) | No (needs 5–7) |

Steps 5, 6, 7 are **parallelisable** — each adds a self-contained route with
no dependencies on each other.

---

## Appendix: Corrected API Endpoint List

Corrections versus the initial `migration-context.yaml`:

| Endpoint | Correction |
|---|---|
| `PUT /v1/test-executions/start-test` | Was listed as `GET`; is actually `PUT` (confirmed in backend `start_test.py`) |
| `GET /v1/artefacts/{id}` | Missing from initial list; confirmed in `artefacts.py` |
| `GET /v1/artefacts/history` | New endpoint not in Flutter app; confirmed in `artefacts.py` |
| `GET /v1/test-cases` | Missing from initial list; used by `searchTestCases` |
