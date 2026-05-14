# Design Specification — test-observer SvelteKit Redesign

> **Phase 2 deliverable.** This document specifies the complete UI design for
> the SvelteKit frontend. It is the authoritative reference for the Builder
> agent (Phase 3). Every component, layout, interaction, and page is described
> here.

---

## 1. Information Architecture

### Site Map

```
/                         → Redirect to first configured family tab
/login                    → SAML authentication
/[family]                 → Family dashboard (artefacts grouped by stage)
/[family]/[id]            → Artefact detail (builds, environments, reviews)
/test-results             → Cross-family test results search
/issues                   → Linked external issues list
/issues/[id]              → Issue detail (attachment rules, associated results)
/notifications            → User notifications
```

### IA Decisions vs. Flutter

| Aspect | Flutter | SvelteKit (proposed) | Rationale |
|--------|---------|---------------------|-----------|
| Navigation model | Top horizontal navbar | Left sidebar (`SideNavigation`) | Pragma convention; better scalability as tabs grow; consistent with Launchpad DS apps |
| Family navigation | Hardcoded tabs with display names (`_tabDisplayName`) | Config-driven sidebar items; label = `capitalize(family)` + "s" | Eliminates artefact-specific logic; new family = config edit only |
| Dashboard layout | Columns view (default) OR per-family list view with family-specific column sets | Single unified view mode toggle: **board** (stage columns) or **table** (generic columns). Table columns are the same for every family. | Removes the per-family list view branching (`ArtefactsListView.snaps()`, `.debs()`, etc.) which is artefact-specific tech debt |
| Artefact detail sidebar | Left panel with info + filters, toggled by filter button | Persistent `SidePanel` with metadata on top + collapsible filters below | Clearer separation of metadata from filtering; SidePanel is a Pragma component |
| Help links | Navbar dropdown (Docs, Feedback, Source Code) | Footer links inside sidebar bottom | Declutters nav; help is secondary information |
| User menu | Navbar dropdown (Log out) | `UserAvatar` in header bar with `Popover` dropdown | Standard Pragma pattern |

### Content Hierarchy

1. **Shell** — sidebar + header + content area (all routes except `/login`)
2. **Dashboard** — primary workspace; users spend most time here
3. **Artefact Detail** — deep-dive into a specific artefact's test state
4. **Test Results** — cross-cutting search across all families
5. **Issues** — external issue tracking integration
6. **Notifications** — transient alerts

---

## 2. Pragma Component Selection

### Component Mapping

| UI Element | Pragma Component | Custom Component | Notes |
|------------|-----------------|-----------------|-------|
| App shell sidebar | `SideNavigation` | — | Items from `config.tabs` |
| Header bar | — | `Header.svelte` | Custom: logo, breadcrumbs area, user avatar, notification badge |
| Artefact status badge | `Badge` | `StatusBadge.svelte` | Wraps Badge with status→severity mapping |
| Test execution status | `Chip` | `TestStatusChip.svelte` | Wraps Chip with execution status→severity mapping |
| Test result status | `Chip` | `TestResultStatusChip.svelte` | PASSED→positive, FAILED→negative, SKIPPED→neutral |
| Search inputs | `SearchBox` | — | Dashboard filter, test results filter, issues filter |
| Data tables | `Table` | — | Test results, issues list, artefact list view |
| Dialogs/modals | `Modal` | — | Bulk review, attachment rule create/edit, confirmations |
| Dropdowns | `Select` | — | Status change, version selector, review decision |
| User avatars | `UserAvatar` | — | Header, reviewer display |
| Notification count | `Badge` | `NotificationBadge.svelte` | Wraps Badge with polling logic |
| Timestamps | `RelativeDateTime` | — | "3 hours ago" style display |
| Absolute dates | `DateTime` | — | Due dates, created dates |
| Loading states | `Spinner` | — | All async data fetches |
| Tooltips | `Tooltip` | — | Status explanations, truncated text |
| Popovers | `Popover` | — | User menu, environment review form |
| Checkboxes | `Checkbox` | — | Bulk selection, review decisions |
| Radio buttons | `Radio` | — | View mode toggle (board/table) |
| Toggle switches | `Switch` | — | Attachment rule enable/disable, auto-rerun toggle |
| Text inputs | `TextInput` | — | Comment fields, issue URL input |
| Multiline text | `Textarea` | — | Review comments |
| Number inputs | `NumberInput` | — | Pagination offset (if needed) |
| Breadcrumbs | `Breadcrumbs` | — | Artefact detail, issue detail |
| Links | `Link` | — | External URLs (CI links, bug links, issue URLs) |
| Filter chips | `Chip` | — | Active filter display with remove action |
| Timeline | `Timeline` | — | Test execution event log |
| Buttons | `Button` | — | All actions |

### Custom Components (no Pragma equivalent)

| Component | Purpose |
|-----------|---------|
| `AppShell.svelte` | Root layout: sidebar + header + content slot |
| `Sidebar.svelte` | Wraps `SideNavigation`; injects config-driven items |
| `Header.svelte` | Top bar with logo, breadcrumbs, user avatar, notifications |
| `StatusBadge.svelte` | Maps `ArtefactStatus` → Badge severity |
| `TestStatusChip.svelte` | Maps `TestExecutionStatus` → Chip severity |
| `TestResultStatusChip.svelte` | Maps `TestResultStatus` → Chip severity |
| `NotificationBadge.svelte` | Badge with polled unread count |
| `StageGroup.svelte` | Board column: stage header + artefact card list |
| `ArtefactCard.svelte` | Card for dashboard board view |
| `ExpandableSection.svelte` | Collapsible section with header + content slot |
| `BulkActionsBar.svelte` | Sticky bar for bulk operations on test results |
| `EnvironmentRow.svelte` | Expandable environment with review controls |
| `TestPlanSection.svelte` | Groups test executions by plan within environment |
| `TestExecutionRow.svelte` | Single test execution with status + actions |
| `VersionSelector.svelte` | Dropdown to switch artefact versions |
| `ReviewForm.svelte` | Checkbox list of review decisions + comment textarea |
| `AttachmentRuleCard.svelte` | Expandable card for an attachment rule |
| `IssueCard.svelte` | Card/row for issue in list view |
| `EmptyState.svelte` | Consistent empty state with icon + message |
| `ErrorState.svelte` | Consistent error state with retry action |
| `ViewModeToggle.svelte` | Board/Table toggle using Radio or Button group |
| `FilterPanel.svelte` | Reusable collapsible filter panel with apply/reset |

---

## 3. Layout System

### Layout Hierarchy

```
<html>
  <body>
    <!-- /login route: no shell -->
    <LoginPage />

    <!-- All other routes: Shell layout -->
    <AppShell>
      <Sidebar slot="sidebar" />
      <Header slot="header" />
      <main slot="content">
        <slot />  <!-- page content -->
      </main>
    </AppShell>
  </body>
</html>
```

### AppShell Grid

```css
.ds.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width, 240px) 1fr;
  grid-template-rows: var(--header-height, 56px) 1fr;
  grid-template-areas:
    "sidebar header"
    "sidebar content";
  height: 100vh;
  overflow: hidden;
}

.ds.app-shell__sidebar {
  grid-area: sidebar;
  overflow-y: auto;
  border-right: 1px solid var(--color-border);
  background-color: var(--color-background-alt);
}

.ds.app-shell__header {
  grid-area: header;
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-background);
}

.ds.app-shell__content {
  grid-area: content;
  overflow-y: auto;
  padding: var(--spacing-4);
}

/* Collapsed sidebar */
.ds.app-shell.sidebar-collapsed {
  grid-template-columns: var(--sidebar-collapsed-width, 48px) 1fr;
}
```

### Content Area Patterns

**Dashboard (board view):**
```css
.ds.dashboard-board {
  display: flex;
  gap: var(--spacing-4);
  overflow-x: auto;
  height: 100%;
}

.ds.stage-group {
  min-width: var(--stage-column-min-width, 320px);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}
```

**Dashboard (table view):**
```css
.ds.dashboard-table {
  width: 100%;
}
```

**Detail page with sidebar:**
```css
.ds.detail-layout {
  display: grid;
  grid-template-columns: var(--detail-sidebar-width, 300px) 1fr;
  gap: var(--spacing-4);
  height: 100%;
}

.ds.detail-layout__sidebar {
  overflow-y: auto;
  border-right: 1px solid var(--color-border);
  padding-right: var(--spacing-4);
}

.ds.detail-layout__main {
  overflow-y: auto;
}
```

### Density Modes

The UI supports two density modes stored in `ui.svelte.ts`:

| Mode | CSS class on `<body>` | Effect |
|------|----------------------|--------|
| Comfortable | `density-comfortable` | Default spacing; `--spacing-*` at standard values |
| Compact | `density-compact` | Reduced padding in cards, table rows, expandable headers |

Density is toggled via a `Switch` in the sidebar footer. Custom components read density via a CSS class on a parent element:

```css
.density-compact .ds.artefact-card {
  padding: var(--spacing-1);
}

.density-compact .ds.environment-row__header {
  padding: var(--spacing-1) var(--spacing-2);
}
```

---

## 4. Navigation Design

### Sidebar Structure

```
┌──────────────────────────┐
│  [Logo] Test Observer     │
├──────────────────────────┤
│  ── Family Dashboards ── │
│  📦 Snaps                │  ← from config.tabs[0]
│  📦 Debs                 │  ← from config.tabs[1]
│  📦 Charms               │  ← from config.tabs[2]
│  📦 Images               │  ← from config.tabs[3]
│  ── Tools ──────────── ──│
│  🔍 Test Results          │
│  🐛 Issues                │
│  🔔 Notifications [3]    │  ← badge with unread count
├──────────────────────────┤
│  [Density toggle]         │
│  [Help links]             │
│  [Version: x.y.z]        │
└──────────────────────────┘
```

**Important:** The icon shown above (📦) is illustrative only. All family nav items use the **same** generic icon (or no icon). No family-specific icons.

### Sidebar Implementation

```svelte
<!-- Sidebar.svelte -->
<script lang="ts">
  import { base } from "$app/paths";
  import { page } from "$app/stores";
  import { SideNavigation } from "@canonical/svelte-ds-app-launchpad";

  const { tabs, unreadCount }: { tabs: string[]; unreadCount: number } = $props();

  function capitalize(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  const currentPath = $derived($page.url.pathname);

  const familyItems = $derived(
    tabs.map(family => ({
      href: `${base}/${family}`,
      label: capitalize(family),
      active: currentPath.startsWith(`${base}/${family}`),
    }))
  );

  const toolItems = $derived([
    {
      href: `${base}/test-results`,
      label: "Test Results",
      active: currentPath === `${base}/test-results`,
    },
    {
      href: `${base}/issues`,
      label: "Issues",
      active: currentPath.startsWith(`${base}/issues`),
    },
    {
      href: `${base}/notifications`,
      label: `Notifications`,
      active: currentPath === `${base}/notifications`,
      badge: unreadCount > 0 ? unreadCount : undefined,
    },
  ]);
</script>
```

### Navigation Rules

1. **Family items** are derived exclusively from `config.tabs`. The label is `capitalize(family)` — no plural "s" suffix (deviation from blueprint; config tab values are already plural (e.g. "snaps"), so `capitalize()` alone produces the correct label; the blueprint's `+ 's'` suffix would double the plural).
2. **Tool items** (Test Results, Issues, Notifications) are fixed — they exist regardless of config.
3. **Active state** is determined by path prefix matching.
4. **No family-specific icons or colours.** All family items share one visual treatment.
5. **Notification badge** shows unread count from the `notifications` store.

### Header Bar

The header contains:
- **Breadcrumbs** — contextual path (e.g. `Snaps > firefox > v130`)
- **Spacer**
- **UserAvatar** — current user with popover (Log out)
- **NotificationBadge** — links to `/notifications`

Breadcrumbs are generated from the current route:
- `/[family]` → `[Family]`
- `/[family]/[id]` → `[Family] / [artefact.name]`
- `/issues/[id]` → `Issues / [issue.key]`
- `/test-results` → `Test Results`

---

## 5. Interaction Patterns

### 5.1 Filtering & Searching

**Dashboard filters:**
- A `SearchBox` in the toolbar filters artefacts by name (client-side).
- A collapsible `FilterPanel` (toggle button with active-filter indicator `Badge`) provides:
  - Status filter (checkboxes: Approved, Marked as Failed, Undecided)
  - Assignee filter (multi-select)
  - Architecture filter (derived from artefact data)
- Filters are applied client-side to the already-fetched artefact list.
- Active filters are shown as `Chip` components above the artefact display, each with a dismiss (×) action.

**Test Results filters:**
- All filters are **URL-persisted** (query params). Changing filters updates the URL; the page re-fetches on navigation.
- Filter panel contains multi-select dropdowns (`Select` or custom combobox) for:
  - Families, Statuses, Artefacts, Environments, Test Cases, Template IDs, Execution Metadata, Issues, Assignees
- Boolean toggles (`Switch`): Archived, Rerun Requested, Latest Execution
- Date range pickers (native `<input type="date">` styled to match)
- **Apply Filters** button triggers URL update → server reload.
- **Reset Filters** clears all params.
- Active filters displayed as dismissible `Chip` components.

**Issues filters:**
- Sidebar filter panel with:
  - `SearchBox` for text search
  - Source filter (GitHub, Jira, Launchpad)
  - Project filter
  - Status filter (Open, Closed, Unknown)
  - Family filter
- Filters applied client-side to fetched issues list.

### 5.2 Status Changes

**Artefact status change:**
- In the artefact detail header, the current status is displayed as a `StatusBadge`.
- Clicking it opens a `Select` dropdown with the three status options.
- Selecting a new status triggers `PATCH /v1/artefacts/{id}` and optimistically updates the badge.
- On error, revert and show an error `Badge` / toast.

**Environment review:**
- Each `EnvironmentRow` has a "Review" `Button` on the right.
- Clicking it opens a `Popover` containing `ReviewForm`:
  - Checkbox list of `EnvironmentReviewDecision` values (mutually exclusive: reject vs. approve variants)
  - `Textarea` for review comment
  - Submit `Button`
- Submitting calls `PATCH /v1/artefacts/{id}/environment-reviews/{reviewId}`.
- Review state updates optimistically; reviewers avatars update.

### 5.3 Bulk Operations

**Bulk environment review (artefact detail):**
- Each environment row has a `Checkbox` for selection.
- Select-all / deselect-all controls appear above the environment list.
- When ≥1 environment is selected, a "Bulk Review" `Button` appears.
- Clicking opens a `Modal` (`BulkReviewDialog`) listing selected environments, with the same `ReviewForm` controls.
- Submit calls `PATCH /v1/artefacts/{id}/environment-reviews` (bulk endpoint).

**Bulk operations (test results page):**
- A `BulkActionsBar` appears below the filter panel with buttons:
  - **Create Attachment Rule** → opens `Modal` with rule configuration form
  - **Attach Issue** → opens `Modal` with issue URL input
  - **Detach Issue** → opens `Modal` with issue URL input
  - **Create Rerun Requests** → confirmation `Modal`
  - **Delete Rerun Requests** → confirmation `Modal`
- All bulk operations use the current `TestResultsFilters` as their scope.
- Buttons are disabled when filters have been modified but not yet applied.

### 5.4 Detail Views

**Artefact detail:**
- Left panel: metadata (`DescriptionList`), version selector, comment field
- Main area: Environments list, each an `ExpandableSection`:
  - Header: checkbox, status chip, architecture, name, reviewer avatars, review button
  - Body: Environment issues section, then test plans grouped by plan name
    - Each test plan: `ExpandableSection` with test executions
      - Each execution: status chip, CI link, C3 link, rerun button, created date
        - Expandable: test results list, event log (`Timeline`)

**Issue detail:**
- Header: issue source badge, project, key (linked), title, status badge, auto-rerun toggle
- Attachment Rules section: list of `AttachmentRuleCard` components, each expandable:
  - Shows filter summary
  - Actions: View Filters (navigates to test results with pre-applied filters), Enable/Disable (`Switch`), Delete (confirmation `Modal`)
  - "Add Attachment Rule" button at bottom
- Test Results section: embedded `Table` showing results linked to this issue, with filter controls (subset of test results filters)

### 5.5 Notifications

- List of notification cards, each showing:
  - Notification type (human-readable label)
  - Target link (navigates to relevant artefact/environment)
  - Relative timestamp (`RelativeDateTime`)
  - Dismiss `Button`
- Empty state: `EmptyState` component with message
- Notifications store polls `/v1/users/me/notifications/count` every 60 seconds for the sidebar badge.

### 5.6 Rerun & Manual Testing

**Rerun button** on each test execution row:
- If `isRerunRequested` is false: "Request Rerun" button → `POST /v1/test-executions/reruns`
- If `isRerunRequested` is true: "Rerun Requested" label (disabled state)

**Rerun filtered plans** button in artefact detail toolbar:
- Reruns all test executions matching current filters → `POST /v1/test-executions/reruns` with execution IDs

**Add Manual Testing** button in artefact detail toolbar:
- Opens `Modal` with fields: Environment (select), Test Plan (text input), CI Link (text input)
- Submits via `PUT /v1/test-executions/start-test`

---

## 6. Modifier Family Usage

### Severity Modifiers

| Context | Value | Modifier | Pragma Rendering |
|---------|-------|----------|-----------------|
| Artefact status: APPROVED | `positive` | Green badge | `<Badge severity="positive">` |
| Artefact status: MARKED_AS_FAILED | `negative` | Red badge | `<Badge severity="negative">` |
| Artefact status: UNDECIDED | `neutral` | Grey badge | `<Badge severity="neutral">` |
| Test execution: PASSED | `positive` | Green chip | `<Chip severity="positive">` |
| Test execution: FAILED | `negative` | Red chip | `<Chip severity="negative">` |
| Test execution: IN_PROGRESS | `caution` | Yellow chip | `<Chip severity="caution">` |
| Test execution: NOT_STARTED | `neutral` | Grey chip | `<Chip severity="neutral">` |
| Test execution: NOT_TESTED | `neutral` | Grey chip | `<Chip severity="neutral">` |
| Test execution: ENDED_PREMATURELY | `negative` | Red chip | `<Chip severity="negative">` |
| Test result: PASSED | `positive` | Green chip | `<Chip severity="positive">` |
| Test result: FAILED | `negative` | Red chip | `<Chip severity="negative">` |
| Test result: SKIPPED | `neutral` | Grey chip | `<Chip severity="neutral">` |
| Issue status: open | `negative` | Red badge | `<Badge severity="negative">` |
| Issue status: closed | `positive` | Green badge | `<Badge severity="positive">` |
| Issue status: unknown | `neutral` | Grey badge | `<Badge severity="neutral">` |
| Notification (unread) | `information` | Blue badge | `<Badge severity="information">` |
| Environment review: has decisions | `positive` | Green indicator | Rendered as positive chip |
| Environment review: no decisions | `neutral` | Grey indicator | Rendered as neutral chip |

### Density Modifiers

| Context | Default | Compact |
|---------|---------|---------|
| Artefact card | `comfortable` | `compact` — tighter padding, smaller font |
| Table rows | `comfortable` | `compact` — reduced row height |
| Environment expandable headers | `comfortable` | `compact` — reduced padding |
| Sidebar items | Always comfortable (sidebar density is fixed) | — |

---

## 7. Color and Theming

### Token Usage

All colours reference launchpad design tokens. No hardcoded hex/rgb values.

```css
/* Background hierarchy */
--color-background          /* main content area */
--color-background-alt      /* sidebar, filter panels */
--color-background-hover    /* interactive element hover */

/* Text */
--color-text                /* primary text */
--color-text-muted          /* secondary/metadata text */

/* Borders */
--color-border              /* default borders */
--color-border-hover        /* interactive border hover */

/* Severity colours (used via modifier classes, not directly) */
--color-positive            /* APPROVED, PASSED */
--color-positive-background
--color-negative            /* FAILED, MARKED_AS_FAILED */
--color-negative-background
--color-negative-border
--color-caution             /* IN_PROGRESS, warnings */
--color-caution-background

/* Interactive */
--color-link                /* clickable links */
--color-focus               /* focus ring */
```

### Status → Colour Mapping

Status colours are expressed exclusively through Pragma severity modifiers, not through direct token references:

```svelte
<!-- StatusBadge.svelte -->
<script lang="ts">
  import { Badge } from "@canonical/svelte-ds-app-launchpad";
  import type { ArtefactStatus } from "$lib/types/artefact.js";

  const { status }: { status: ArtefactStatus } = $props();

  const severityMap: Record<ArtefactStatus, string> = {
    APPROVED: "positive",
    MARKED_AS_FAILED: "negative",
    UNDECIDED: "neutral",
  };
</script>

<Badge severity={severityMap[status]}>{status.replace(/_/g, " ")}</Badge>
```

### Theme Support

The app imports `color/light.css` by default. Dark mode is **out of scope** for initial release but can be added by swapping to `color/dark.css` or `color/system.css`.

---

## 8. Responsive Design Strategy

### Target: Desktop Internal Tool

The primary (and initially only) target is desktop browsers at ≥1280px viewport width. This is an internal engineering tool, not a public-facing website.

### Breakpoints

| Viewport | Behaviour |
|----------|-----------|
| ≥1280px | Full layout: expanded sidebar (240px) + content |
| 1024–1279px | Collapsible sidebar: default collapsed (48px icon rail), expand on hover/click |
| <1024px | Not officially supported; sidebar collapses to icon rail; horizontal scroll on tables |

### Navigation Adaptation

- **≥1280px:** Sidebar always visible, expanded with labels
- **1024–1279px:** Sidebar collapsed to icon rail; click hamburger or hover to expand as overlay
- **<1024px:** Same as 1024–1279px; content scrolls horizontally if needed

### Data Table Adaptation

- Tables use `min-width` to prevent column collapse
- Horizontal scroll container wraps tables when viewport is narrow
- Column priority: status and name columns are always visible; metadata columns hide first

### Dashboard Board View Adaptation

- Stage columns have `min-width: 320px` and `flex-shrink: 0`
- Horizontal scroll when columns exceed viewport width
- This is identical to the Flutter behaviour

---

## 9. Accessibility Requirements

### Keyboard Navigation

- **Tab order** follows visual order: sidebar → header → content
- **Sidebar navigation:** Arrow keys move between items; Enter activates
- **Expandable sections:** Enter/Space toggles; focus moves to first child on expand
- **Modals:** Focus trapped inside; Escape closes; focus returns to trigger element
- **Tables:** Arrow keys for cell navigation (rely on native Pragma Table behaviour)
- **Popovers:** Escape closes; focus returns to trigger

### Semantic HTML

- `<nav>` for sidebar navigation
- `<header>` for header bar
- `<main>` for content area
- `<section>` for page regions with `aria-labelledby`
- `<table>` for data tables (Pragma Table handles this)
- `<dialog>` for modals (Pragma Modal handles this)
- `<details>/<summary>` semantics for expandable sections
- Proper heading hierarchy: `<h1>` for page title, `<h2>` for sections, `<h3>` for subsections

### ARIA Labels

- Status badges: `aria-label="Artefact status: APPROVED"` (not just colour)
- Notification badge: `aria-label="3 unread notifications"`
- Filter toggle: `aria-expanded` + `aria-controls`
- Expandable sections: `aria-expanded` on trigger
- Bulk select: `aria-label="Select environment {name} for bulk review"`
- Loading states: `aria-busy="true"` on container; `aria-live="polite"` for result count updates

### Status Not Conveyed by Colour Alone

Every status indicator includes **text or icon** alongside colour:
- `StatusBadge` shows text label ("APPROVED", "MARKED AS FAILED", "UNDECIDED")
- `TestStatusChip` shows text label ("PASSED", "FAILED", "IN PROGRESS", etc.)
- `TestResultStatusChip` shows text label
- Dashboard artefact cards show status as text chip, not just a coloured dot

### Focus Management

- On page navigation: focus moves to `<h1>` of new page (via `afterNavigate` hook)
- On modal open: focus moves to first interactive element inside modal
- On modal close: focus returns to the trigger button
- On expandable toggle: focus remains on the toggle button
- Error states: focus moves to error message container

---

## 10. Page Specifications

### 10.1 Root Page (`/`)

**Purpose:** Redirect to the first configured family dashboard.

**Component tree:**
```
+page.server.ts → redirect(302, `${base}/${config.tabs[0]}`)
```

**No rendered UI.** Pure server-side redirect.

**Data requirements:** `config.tabs` from layout data.

---

### 10.2 Login Page (`/login`)

**Purpose:** Present SAML login prompt for authenticated deployments.

**Component tree:**
```
LoginPage
├── <div class="ds login-page">            (centered card)
│   ├── <h1> "Sign in to Test Observer"
│   ├── <p> "Authentication is required to access this application."
│   └── Button (appearance="positive")     "Sign in"
│       → navigates to /v1/auth/saml/login?return_to={returnTo}
└── (no AppShell, no sidebar, no header)
```

**Layout:** Blank — no shell. Centered card, max-width 420px.

**Key interactions:**
- On mount: if user is already authenticated (from page data), redirect to `returnTo` param or first family tab.
- "Sign in" button links to SAML IdP login endpoint.

**Data requirements:**
- `user` from layout data (to detect already-authenticated state)
- `returnTo` from URL query param

---

### 10.3 Family Dashboard (`/[family]`)

**Purpose:** View all artefacts for a family, grouped by stage, with filtering and search.

**Component tree:**
```
DashboardPage
├── Breadcrumbs                           ["Snaps"]
├── DashboardToolbar
│   ├── <h1> "{Family} Update Verification"
│   ├── <span> artefact count ("24 of 30 artefacts")
│   ├── SearchBox                          (name filter)
│   ├── Button (filter toggle)
│   │   └── Badge (active filter indicator)
│   └── ViewModeToggle                    (board / table)
├── FilterPanel (collapsible)
│   ├── Checkbox group: Status (Approved, Marked as Failed, Undecided)
│   ├── Select: Assignee (multi-select)
│   └── Active filters: Chip[] (dismissible)
├── [if board mode] DashboardBoard
│   ├── StageGroup (for each distinct stage in data)
│   │   ├── <h2> stage name
│   │   ├── <span> artefact count in stage
│   │   └── ArtefactCard[] (scrollable list)
│   │       ├── <h3> artefact.name
│   │       ├── <span> "version: {version}"
│   │       ├── <span> metadata (track, store, series, etc. — only non-empty)
│   │       ├── StatusBadge
│   │       ├── DateTime (due date, if present)
│   │       └── UserAvatar[] (reviewers) + progress "{completed}/{total}"
│   └── (horizontal scroll if stages overflow)
├── [if table mode] DashboardTable
│   └── Table
│       headers: [Name, Version, Stage, Status, Track, Series, Reviewers, Due Date]
│       rows: artefact data
│       each row clickable → navigates to /[family]/[id]
└── [if loading] Spinner
    [if empty] EmptyState "No artefacts found"
    [if error] ErrorState with retry
```

**Key interactions:**
- **Search:** `SearchBox` filters artefacts by name (client-side, debounced 300ms)
- **Filter toggle:** Shows/hides `FilterPanel`; `Badge` on button indicates active filters
- **View mode:** Toggle between board (stage columns) and table (flat list)
- **ArtefactCard click:** Navigate to `/[family]/[id]`
- **Stage groups:** Derived dynamically: `[...new Set(artefacts.map(a => a.stage))]`

**State transitions:**
- Loading → artefacts fetched → display
- Filter change → re-derive filtered list (client-side)
- View mode change → swap board/table (persisted in `ui.svelte.ts`)

**Data requirements:**
- `GET /v1/artefacts?family={family}` → `Artefact[]`
- Family validation: `config.tabs.includes(params.family)` → 404 if not

---

### 10.4 Artefact Detail (`/[family]/[id]`)

**Purpose:** Deep-dive into a specific artefact — metadata, builds, environment reviews, test executions.

**Component tree:**
```
ArtefactDetailPage
├── Breadcrumbs                           ["Snaps", "firefox"]
├── ArtefactHeader
│   ├── <h1> artefact.name
│   ├── StatusBadge (clickable → Select dropdown for status change)
│   ├── UserAvatar[] (reviewers) + progress "{completed}/{total}"
│   ├── DateTime (due date, if present)
│   └── Button "Sign Off" (quick approve-all action)
├── detail-layout (CSS Grid: sidebar + main)
│   ├── ArtefactSidebar (left)
│   │   ├── VersionSelector (Select dropdown → navigate to different version)
│   │   ├── DescriptionList (metadata)
│   │   │   ├── Stage (as breadcrumb-style indicator)
│   │   │   ├── Track, Store, Branch, Series, Repo, Source, OS, Release, Owner
│   │   │   ├── SHA256 (truncated with Tooltip)
│   │   │   ├── Link: Image URL (if present)
│   │   │   ├── Link: Bug Link (if present)
│   │   │   └── TextInput: Comment (editable, submit on Enter)
│   │   └── FilterPanel (collapsible)
│   │       ├── Checkbox group: Execution Status
│   │       ├── Select: Architecture
│   │       ├── Select: Environment
│   │       └── Active filters: Chip[]
│   └── ArtefactMain (right)
│       ├── EnvironmentToolbar
│       │   ├── <h2> "Environments"
│       │   ├── StatusSummary (count of each execution status)
│       │   ├── Button "Add Manual Testing"
│       │   ├── Button "Rerun Filtered Plans"
│       │   └── BulkEnvironmentControls
│       │       ├── Checkbox "Select All" / "Deselect All"
│       │       └── Button "Bulk Review" (visible when ≥1 selected)
│       ├── [Warning banner if fewer environments than previous version]
│       └── EnvironmentList
│           └── EnvironmentRow[] (ExpandableSection for each environment)
│               ├── Header:
│               │   ├── Checkbox (bulk select)
│               │   ├── TestStatusChip (latest execution status)
│               │   ├── <span> architecture
│               │   ├── <span> environment name
│               │   ├── Spacer
│               │   ├── UserAvatar[] (environment reviewers)
│               │   └── Button "Review" → Popover with ReviewForm
│               └── Body (expanded):
│                   ├── EnvironmentIssuesSection
│                   │   └── ExpandableSection "Environment Issues ({count})"
│                   │       ├── Header: Button "Add" (authenticated users) → opens EnvironmentIssueModal
│                   │       └── EnvironmentIssue[]
│                   │           ├── <span> name, description, confirmed status
│                   │           ├── Button "Edit" → opens EnvironmentIssueModal (pre-filled)
│                   │           └── Button "Delete" → confirmation Modal
│                   │       EnvironmentIssueModal (shared for Add/Edit):
│                   │           ├── TextInput: Environment Name (pre-filled from environment)
│                   │           ├── TextInput: Description
│                   │           ├── TextInput: URL
│                   │           ├── Checkbox: Is Confirmed
│                   │           └── Button "Submit" → POST or PUT
│                   └── TestPlanSection[] (grouped by testPlan)
│                       ├── <h3> plan name
│                       └── TestExecutionRow[] (sorted newest first)
│                           ├── TestStatusChip
│                           ├── Link: CI Link
│                           ├── Link: C3 Link
│                           ├── RelativeDateTime: created
│                           ├── Chip: "Rerun Requested" (if applicable)
│                           ├── Button: "Request Rerun" / "Rerun Requested"
│                           ├── Button: "Add Test Result" (visible when testPlan === "Manual Testing" AND user is authenticated)
│                           │   └── Opens AddTestResultModal:
│                           │       ├── TextInput: Test Name (prefixed with user handle)
│                           │       ├── Select: Status (PASSED / FAILED / SKIPPED)
│                           │       ├── Textarea: Comment
│                           │       ├── Textarea: IO Log
│                           │       └── Button "Submit" → POST /v1/test-executions/{id}/test-results
│                           ├── Chip[]: Relevant Links
│                           └── ExpandableSection (test results + event log)
│                               ├── TestResultsList
│                               │   └── TestResultRow[]
│                               │       ├── TestResultStatusChip
│                               │       ├── <span> name
│                               │       ├── <span> category
│                               │       ├── Chip[]: issue attachments
│                               │       ├── Previous results indicator
│                               │       ├── Button: "View Details" → SidePanel with full result
│                               │       └── TestIssuesExpandable
│                               │           ├── Header: "Reported Test Issues ({count})" + Button "Add" (authenticated)
│                               │           └── TestIssue[]
│                               │               ├── <span> template ID, case name, description
│                               │               ├── Link: URL
│                               │               ├── Button "Edit" → opens TestIssueModal (pre-filled)
│                               │               └── Button "Delete" → confirmation Modal
│                               │           TestIssueModal (shared for Add/Edit):
│                               │               ├── TextInput: Case Name (pre-filled from test case)
│                               │               ├── TextInput: Template ID (pre-filled from test case)
│                               │               ├── TextInput: Description
│                               │               ├── TextInput: URL
│                               │               └── Button "Submit" → POST or PUT
│                               └── Timeline: TestEvent[] (event log)
```

**Key interactions:**
- **Status change:** Click StatusBadge → dropdown → PATCH artefact
- **Version switch:** Select dropdown → navigate to `/[family]/[newArtefactId]`
- **Comment edit:** TextInput → submit on Enter → PATCH artefact
- **Environment expand:** Click row → toggle body visibility; auto-expand if `?testExecutionId` matches
- **Review:** Click "Review" button → Popover → submit → PATCH review
- **Bulk review:** Select environments → "Bulk Review" → Modal → submit
- **Rerun:** Click per-execution → POST reruns
- **Add manual testing:** Button → Modal → PUT start-test
- **Test result detail:** Click "View Details" → SidePanel slides in with full IO log, template ID, previous results

**Data requirements:**
- `GET /v1/artefacts/{id}` → `Artefact`
- `GET /v1/artefacts/{id}/builds` → `ArtefactBuild[]`
- `GET /v1/artefacts/{id}/environment-reviews` → `EnvironmentReview[]`
- `GET /v1/artefacts/{id}/versions` → `ArtefactVersion[]`
- `GET /v1/test-executions/{id}/test-results` → `TestResult[]` (on expand)
- `GET /v1/test-executions/{id}/status_update` → `TestEvent[]` (on expand)
- `GET /v1/environments/reported-issues` → `EnvironmentIssue[]`
- `POST /v1/environments/reported-issues` → create new environment issue
- `PUT /v1/environments/reported-issues/{id}` → update environment issue
- `DELETE /v1/environments/reported-issues/{id}` → delete environment issue
- `GET /v1/test-cases/reported-issues` → `TestIssue[]`
- `POST /v1/test-cases/reported-issues` → create new test case issue
- `PUT /v1/test-cases/reported-issues/{id}` → update test case issue
- `DELETE /v1/test-cases/reported-issues/{id}` → delete test case issue
- `POST /v1/test-executions/{id}/test-results` → add manual test result
- URL query params: `testExecutionId`, `testResultId` (for deep linking)

---

### 10.5 Test Results (`/test-results`)

**Purpose:** Cross-family search and bulk operations on test results.

**Component tree:**
```
TestResultsPage
├── Breadcrumbs                           ["Test Results"]
├── <h1> "Search Test Results"
├── FilterPanel (always visible by default)
│   ├── Row 1: Select: Families | Select: Statuses | Select: Artefacts
│   ├── Row 2: Select: Environments | Select: Test Cases | Select: Template IDs
│   ├── Row 3: Select: Issues (with Any/None meta-options) | Select: Assignees (with Any/None)
│   ├── Row 4: Execution Metadata key-value pairs (dynamic)
│   ├── Row 5: Switch: Archived | Switch: Rerun Requested | Switch: Latest Execution
│   ├── Row 6: Date range: From | Until
│   ├── Button "Apply Filters" (positive) | Button "Reset" (neutral)
│   └── Active filters: Chip[] (dismissible; removing a chip re-applies)
├── BulkActionsBar
│   ├── <h3> "Bulk Operations"
│   ├── Button "Create Attachment Rule"
│   ├── Button "Attach Issue"
│   ├── Button "Detach Issue"
│   ├── Button "Create Rerun Requests"
│   └── Button "Delete Rerun Requests"
├── ResultsSummary
│   └── <span> "Found {count} results (showing {displayed})"
├── Table (test results)
│   headers: [Artefact, Test Case, Execution ID, Status, Track, Version, Environment, Test Plan, Actions]
│   rows: TestResultWithContext[]
│   ├── Artefact cell: Link to artefact detail
│   ├── Test Case cell: name + category
│   ├── Status cell: TestResultStatusChip
│   ├── Environment cell: "{architecture} / {name}"
│   ├── Actions cell: Button "View" → navigates to artefact detail with testExecutionId + testResultId
│   └── Infinite scroll (load more on scroll near bottom)
├── [if loading] Spinner
├── [if no filters] EmptyState "Use filters above to search"
└── [if error] ErrorState with retry
```

**Key interactions:**
- **Filter editing:** Change filter values → "Apply Filters" button becomes enabled
- **Apply Filters:** Updates URL query params → triggers server-side re-fetch
- **Reset:** Clears all filters → navigates to `/test-results` (no params)
- **Active filter chips:** Clicking × removes that filter and immediately re-applies
- **Bulk operations:** Each opens a `Modal`; operations scope to current filter set
- **Infinite scroll:** As user scrolls near bottom, load next page (offset/limit)
- **Row click / View button:** Navigate to `/[family]/[artefactId]?testExecutionId=X&testResultId=Y`

**Data requirements:**
- `GET /v1/test-results` with filter query params → `TestResultsSearchResult`
- Autocomplete data for filter dropdowns:
  - `GET /v1/artefacts/search` (artefact names)
  - `GET /v1/environments` (environment names)
  - `GET /v1/test-cases` (test case names)
  - `GET /v1/execution-metadata` (metadata keys)
  - `GET /v1/issues` (for issue filter)
  - `GET /v1/users` (for assignee filter)

---

### 10.6 Issues List (`/issues`)

**Purpose:** View and manage linked external issues (GitHub, Jira, Launchpad).

**Component tree:**
```
IssuesPage
├── Breadcrumbs                           ["Issues"]
├── IssuesToolbar
│   ├── <h1> "Linked External Issues"
│   ├── Button (filter toggle) + Badge (active filter indicator)
│   └── Button "Add Issue" → Modal with URL input
├── FilterPanel (collapsible, sidebar-style)
│   ├── SearchBox (text search across title, key, project)
│   ├── Checkbox group: Source (GitHub, Jira, Launchpad)
│   ├── Checkbox group: Status (Open, Closed, Unknown)
│   ├── Select: Project (multi-select, derived from data)
│   └── Select: Family (multi-select)
├── IssuesList
│   └── IssueGroup[] (grouped by source + project)
│       ├── <h2> "{source icon} {project}"
│       └── IssueCard[]
│           ├── Badge: source (GitHub/Jira/Launchpad)
│           ├── Link: issue key → external URL
│           ├── <span> title
│           ├── Badge: status (severity mapped)
│           ├── <span> "{testExecutionsCount} test executions"
│           ├── Switch: auto-rerun (inline toggle)
│           └── Clickable → navigates to /issues/[id]
├── [if loading] Spinner
├── [if empty] EmptyState "No issues found"
└── [if error] ErrorState with retry
```

**Key interactions:**
- **Add Issue:** Button → Modal with `TextInput` for issue URL → `PUT /v1/issues`
- **Filter toggle:** Show/hide filter panel
- **Issue click:** Navigate to `/issues/[id]`
- **Auto-rerun toggle:** Inline `Switch` → `PATCH /v1/issues/{id}` with `{ autoRerunEnabled }`
- **Infinite scroll:** Load more issues as user scrolls

**Data requirements:**
- `GET /v1/issues` → `Issue[]`

---

### 10.7 Issue Detail (`/issues/[id]`)

**Purpose:** View issue details, manage attachment rules, see associated test results.

**Component tree:**
```
IssueDetailPage
├── Breadcrumbs                           ["Issues", "LP#12345"]
├── IssueHeader
│   ├── Badge: source
│   ├── <span> project
│   ├── Link: key → external URL
│   ├── <h1> title
│   ├── Badge: status (severity mapped)
│   └── Switch: auto-rerun + label
├── AttachmentRulesSection
│   ├── <h2> "Attachment Rules"
│   ├── AttachmentRuleCard[] (ExpandableSection for each rule)
│   │   ├── Header: "Rule #{id}" + actions
│   │   │   ├── Button "View Filters" → navigates to /test-results with rule filters pre-applied
│   │   │   ├── Switch: enabled/disabled → PATCH attachment rule
│   │   │   └── Button "Delete" → confirmation Modal → DELETE attachment rule
│   │   └── Body (expanded):
│   │       └── DescriptionList: filter summary (families, environments, test cases, statuses, metadata)
│   └── Button "Add Attachment Rule" → Modal (AttachmentRuleDialog)
│       ├── Select: Families (multi)
│       ├── Select: Environments (multi)
│       ├── Select: Test Cases (multi)
│       ├── Select: Template IDs (multi)
│       ├── Select: Statuses (multi)
│       ├── Execution Metadata key-value editor
│       └── Button "Create" → POST /v1/issues/{id}/attachment-rules
├── TestResultsSection
│   ├── <h2> "Test Results"
│   ├── Button (filter toggle) + Badge
│   ├── FilterPanel (subset: families, artefacts, environments, test cases, date range)
│   ├── BulkActionsBar (subset: attach/detach issue, create/delete reruns)
│   └── Table: test results linked to this issue
│       (same columns as /test-results page, with infinite scroll)
├── [if loading] Spinner
└── [if error] ErrorState with retry
```

**Key interactions:**
- **Attachment rule expand:** Click to toggle; auto-expand if `?attachmentRule=X` matches
- **View Filters:** Navigate to `/test-results` with the rule's filters pre-applied + issue ID filter
- **Enable/Disable rule:** Inline `Switch` → PATCH
- **Delete rule:** Confirmation Modal → DELETE
- **Add rule:** Button → Modal with filter configuration → POST
- **Auto-rerun toggle:** `Switch` in header → PATCH issue

**Data requirements:**
- `GET /v1/issues/{id}` → `IssueWithContext` (includes attachment rules)
- `GET /v1/test-results` with `issues=[id]` filter → embedded test results
- URL query param: `attachmentRule` (for deep linking to a specific rule)

---

### 10.8 Notifications (`/notifications`)

**Purpose:** View and dismiss user notifications.

**Component tree:**
```
NotificationsPage
├── Breadcrumbs                           ["Notifications"]
├── <h1> "Notifications"
├── NotificationList
│   └── NotificationCard[]
│       ├── <div class="ds notification-card">
│       ├── Badge: notification type (severity="information")
│       ├── <span> human-readable type label
│       │   "USER_ASSIGNED_ARTEFACT_REVIEW" → "Assigned to review artefact"
│       │   "USER_ASSIGNED_ENVIRONMENT_REVIEW" → "Assigned to review environment"
│       ├── Link: target URL (if present) → "View"
│       ├── RelativeDateTime: created
│       ├── [if dismissed] <span class="muted"> "Dismissed"
│       └── Button "Dismiss" (if not dismissed) → POST dismiss
├── [if loading] Spinner
├── [if empty] EmptyState "No notifications" (icon + message)
└── [if error] ErrorState with retry
```

**Key interactions:**
- **Dismiss:** Click button → `POST /v1/users/me/notifications/{id}/dismiss` → optimistic update
- **Navigate:** Click target link → navigates to artefact/environment
- **Auto-refresh:** Notifications store polls count every 60s; full list re-fetches on page visit

**Data requirements:**
- `GET /v1/users/me/notifications` → `UserNotification[]`

---

## 11. Design Decisions Log

| # | Decision | Current (Flutter) | Proposed (SvelteKit) | Rationale |
|---|----------|-------------------|---------------------|-----------|
| 1 | Navigation model | Top horizontal navbar with family tabs | Left sidebar with `SideNavigation` | Pragma/Launchpad DS convention; better scalability; consistent with Canonical internal tools |
| 2 | Family display names | Hardcoded map: `'snaps' → 'Snap Testing'`, etc. | Computed: `capitalize(family)` | Eliminates artefact-specific logic; any new family works automatically |
| 3 | Dashboard view modes | Board (all families) + family-specific list views (`ArtefactsListView.snaps()`, `.debs()`, etc.) | Board + generic table view (same columns for all families) | The per-family list views are artefact-specific tech debt; a generic table with common columns is family-agnostic |
| 4 | Stage columns | Derived from `familyStages()` (hardcoded per-family stage lists) | Derived from data: `[...new Set(artefacts.map(a => a.stage))]` | Data-driven; no code change when stages change or new families are added |
| 5 | Artefact detail layout | Left toggleable filter panel + main body | Persistent side panel (metadata + filters) + main body using CSS Grid | Clearer IA; metadata is always visible; filters are secondary |
| 6 | Help links | Navbar dropdown (Docs, Feedback, Source Code) | Sidebar footer (static links) | Declutters header; help is low-frequency |
| 7 | User authentication UI | Navbar "Log in" / user dropdown | Header `UserAvatar` with `Popover` dropdown | Pragma UserAvatar pattern; cleaner header |
| 8 | Test results page filter UX | Collapsible filter panel + apply button | Always-visible filter panel + apply/reset + active filter chips | Filters are the primary interaction on this page; hiding them adds friction |
| 9 | Bulk operations | Buttons below filters; separate forms per operation | `BulkActionsBar` with consistent button row; each opens a Modal | Consistent pattern; clearer separation of trigger (bar) and form (modal) |
| 10 | Environment review | `Popover` with checkboxes + comment | Same: `Popover` with `ReviewForm` (checkboxes + textarea) | Good pattern; kept as-is |
| 11 | Test execution event log | Custom expandable with text list | Pragma `Timeline` component | Purpose-built component; better visual treatment |
| 12 | Notification display | Card list with inline dismiss | Card list with `RelativeDateTime` + dismiss button | Similar pattern; improved with Pragma components |
| 13 | Issues grouping | Grouped by (source, project) tuples | Same grouping, rendered as sections with headers | Good IA; kept as-is |
| 14 | CSS strategy | Flutter Material/Yaru theming | Pure CSS with launchpad design tokens; `ds` namespace for custom components | Pragma convention; no preprocessors; design token consistency |
| 15 | State management | Riverpod providers (client-side) | SvelteKit server load + Svelte 5 runes ($state, $derived) | SSR-first; lighter client-side state; URL as source of truth for filters |
| 16 | Version selector | DropdownMenu widget | Pragma `Select` component | Consistency with DS |
| 17 | Loading states | `YaruCircularProgressIndicator` | Pragma `Spinner` | DS consistency |
| 18 | Empty states | Ad-hoc per page | Reusable `EmptyState` component with icon + message + optional action | Consistency; reduces duplication |
| 19 | Error states | Ad-hoc per page | Reusable `ErrorState` component with message + retry button | Consistency; reduces duplication |
| 20 | Density toggle | Not present | Sidebar footer `Switch` for compact/comfortable density | Power-user feature for data-dense views; low-cost to implement |
