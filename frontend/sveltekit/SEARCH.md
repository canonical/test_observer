<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Test result search

`/test-results` is a search page with ephemeral result selection and contextual
issue attachment and rerun request actions. Its
applied query lives in the URL, so direct links, reloads, and browser back/forward
restore the search. Selection is not encoded in links; view-only history changes
preserve the current selection. This is the canonical SvelteKit search guide.

## Conditions and applying a search

The compact condition bar starts with **+ Add filter** and **Search**. Add filter
opens an anchored, searchable picker containing the 18 fields below. Unused
fields stay hidden until added. A field already represented by a chip is omitted
from the picker; select its chip to edit it instead. Labels match Flutter's 17
rendered fields, plus the approved extra **Template ID**. Family labels use the
configured route name with only its first character capitalized, matching the
sidebar, dashboard titles and artefact breadcrumbs. API names are submitted
unchanged.

**Add filter** or **Save changes** confirms an editor into the chip draft, but
does not fetch results or change the URL. At least one value is required: empty
editors cannot create or empty a chip. To clear an existing condition, use its
separate, labelled remove button, or **Remove filter** inside its editor. Values
are summarized/truncated in chips; the full values are available in their
accessible names, hover titles, and editors.

Only one Pragma popover is open at a time, without expanding the page layout.
Placement is anchored to its trigger within the visible viewport, independent of
the result grid's document height. It follows scrolling/resizing and scrolls
internally when the available space is short, keeping all actions reachable.
Focus enters the picker/editor after native opening completes, so typing works
without an extra Tab. Cancel or Escape discards unconfirmed
edits and returns focus to the trigger; outside click discards edits without
stealing focus from the clicked control. Confirming focuses the resulting chip,
and removing a condition focuses Add filter. Tab follows normal browser order;
Enter activates a focused button or submits a valid editor, except that Enter
in a suggestion query never saves. Backend query or
pagination URL changes close and reset transient editors; table-view-only URL
changes preserve the confirmed drafts, open editor and keyboard focus.

**Search** applies the entire confirmed chip draft, updates the URL, and resets
valid pagination to the first page. Chip configuration and removal never fetch. **Changes
not applied** marks a draft that differs from the URL, and existing results are
labelled as belonging to the previous query. Pagination is disabled until the
draft is applied or restored to the applied values, so it cannot accidentally
apply or discard edits. Unconfirmed editor contents are never included by Search.

**Clear all** immediately removes the URL query, chips and results, returning to
the initial prompt. Removing the last chip instead remains a draft until Search
is selected; Search then clears the applied query and results. Neither action
requests unfiltered results. Empty and pagination-only URLs never request
unfiltered test results.

## Fields and editors

| Label             | URL/API key            | Editor and contract                                                                                                                                                                    |
| ----------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Family            | `families`             | Multiple configured family checkboxes; API names, not display labels.                                                                                                                  |
| Status            | `test_result_statuses` | Multiple checkboxes: Passed, Failed, Skipped (`PASSED`, `FAILED`, `SKIPPED`).                                                                                                          |
| Issues            | `issues`               | Specific positive safe integer IDs with rich suggestions/manual IDs, **Has any issue** (`any`), or **Has no issues** (`none`).                                                         |
| Reviewers         | `reviewer_ids`         | Specific positive safe integer IDs with rich suggestions/manual IDs, **Has any reviewer** (`any`), or **Has no reviewer** (`none`).                                                    |
| Artefact          | `artefacts`            | Exact names with remote suggestions and manual exact-value entry.                                                                                                                      |
| Artefact Version  | `artefact_versions`    | Manual comma-separated exact values; no remote lookup.                                                                                                                                 |
| Artefact Stage    | `artefact_stages`      | Multiple checkboxes from the union of all configured families' stages, plus **(none)** for an explicitly empty stage. Unconfigured selections are retained until explicitly unchecked. |
| Artefact Track    | `artefact_tracks`      | Manual comma-separated exact values; no remote lookup.                                                                                                                                 |
| Archived          | `artefact_is_archived` | Single choice: **Non archived only** (`false`) or **Archived only** (`true`).                                                                                                          |
| Rerun Requested   | `rerun_is_requested`   | Single choice: **No rerun requested** (`false`) or **Rerun requested** (`true`).                                                                                                       |
| Execution Version | `execution_is_latest`  | Single choice: **Older executions only** (`false`) or **Latest execution only** (`true`).                                                                                              |
| Environment       | `environments`         | Exact names with remote suggestions and manual exact-value entry.                                                                                                                      |
| Test Case         | `test_cases`           | Exact names with remote suggestions and manual exact-value entry.                                                                                                                      |
| Test Plan         | `test_plans`           | Exact names with remote suggestions and manual exact-value entry.                                                                                                                      |
| Template ID       | `template_ids`         | Manual comma-separated exact values; no remote lookup.                                                                                                                                 |
| Metadata          | `execution_metadata`   | Literal category/value pairs, with native datalist suggestions and individual pair removal.                                                                                            |
| From              | `from_date`            | Inclusive lower bound on result creation time; UTC date/time picker and exact timestamp input.                                                                                         |
| Until             | `until_date`           | Inclusive upper bound on result creation time; UTC date/time picker and exact timestamp input.                                                                                         |

Boolean absence is unrestricted; `false` is an active condition, not an empty
filter. Issues and Reviewers have mutually exclusive specific IDs / any / none
modes: IDs cannot be mixed with `any` or `none`. Legacy `assignee_ids` is read only
when `reviewer_ids` is absent. Explicit canonical presence wins, as in Flutter;
an empty/invalid canonical value blocks instead of falling back to the alias
(the backend falls back for an empty canonical list). API requests emit only
canonical `reviewer_ids`. Hydrated issue/reviewer labels are display-only and are
not part of filter identity. Detail labels use a bounded in-memory session cache,
invalidated on session/profile/permission or API-root changes; lookup failures
never drop selected IDs or block other editors.

### Suggestions and manual values

Artefact, Environment, Test Plan and Test Case suggestions use the **confirmed
draft Family chips**, not the applied results query. Issues and Reviewers offer
rich issue/project/title/source and name/handle/email suggestions without a family
restriction, matching Flutter. Lookups use existing `GET /v1/artefacts/search`,
`/v1/environments`, `/v1/test-plans`, `/v1/test-cases`, `/v1/issues` and `/v1/users`
contracts. They start after two trimmed characters and a 250 ms debounce, capped
at 50 names or 10 IDs. Query replies are not cached. Requests are aborted and late
bodies/errors ignored when query, family, field, editor or session context changes.
Failures, including authentication/permission errors, stay local with retry and a
manual exact-value path, not global error toasts.

Typing **Find Artefact** (or another lookup query) never selects a value. Choose a
suggestion or **Add exact value / Add exact IDs** to add to the selected list and
clear the query. Selected values remain visible and individually removable even
when absent from suggestions. Pending text must be selected, explicitly added, or
cleared before saving the chip. Tab/Enter activate ordinary result buttons;
Arrow Down/Up moves between the input and results. Enter in the query input does
not submit the editor; Escape discards it. Suggestions are inline in the same
popover, not a second overlay.

Name options containing literal commas or surrounding whitespace cannot
round-trip through the comma-list link contract and are visibly unavailable.
Manual exact-name entry trims surrounding whitespace and rejects commas instead
of silently splitting them. Existing comma/repeated links still restore.
Artefact Version, Artefact Track and Template ID remain manual exact lists,
trimming and deduplicating comma-separated values: no complete lookup endpoint
exists for them (test-case search matches case names, not template IDs).

Metadata lazily loads `GET /v1/execution-metadata` when its editor opens. Native
category/value datalists filter this known map locally (up to 50 matches), with
values grouped by the exact category. The map is cached only in memory for five
minutes in the current API/session/profile/permission context. Reopening can
reuse it; typing never refetches it, and cancelled replies cannot fill the cache.
Manual literal pairs remain available. **Add pair** adds the pair and clears its
inputs; pending category/value text must be added or cleared before confirming.
Suggestion selection and chip confirmation never fetch test results.

### Metadata and date wire contracts

Metadata is AND across categories and OR within each category. Each wire pair is
`Base64(UTF8(category)):Base64(UTF8(value))`, repeated for each value, using standard
padded Base64, not the table view's base64url. Comma-separated encoded pairs also
restore. Decoded Unicode, punctuation, commas, colons and spaces remain literal.
The editor accepts separate category/value inputs, not wire encoding or delimiter
parsing. Categories and values each require 1–200 Unicode characters. Invalid
encoding, UTF-8 or lengths block the search locally.

From/Until apply inclusively to `TestResult.created_at`. Timestamps must be valid
Gregorian ISO instants (`YYYY-MM-DDTHH:mm:ss[.fraction]Z` or an explicit `±HH:MM`
offset), with no rollover or assumed local timezone. Bounds may be one-sided;
From must not exceed Until, comparing offsets and fractional precision without
JavaScript millisecond truncation. Bounds must be exactly representable at backend
microsecond precision: nonzero digits beyond six fractional places are rejected;
additional trailing zeros are allowed. Input timestamps are retained, never
rounded or silently normalized. Changing the clearly labelled UTC picker
deliberately selects second precision; an unchanged save retains the original
timestamp text. Dates alone count as meaningful frontend filters, matching Flutter.

## URL and result contract

Lists use backend **exact-match** semantics, not substring search. Alternatives
within one list are ORed; different filters are ANDed. Page URL lists can be
comma-separated, repeated, or both, matching Flutter. Whitespace is trimmed and
values deduplicated; empty entries are removed except for `artefact_stages=`,
which explicitly matches an empty stage, not an unrestricted search. Commas
delimit list values and cannot be literal characters in names. API calls use
repeated parameters. For example,
`?artefacts=one,two&test_result_statuses=FAILED` requests
`artefacts=one&artefacts=two&test_result_statuses=FAILED` from `/v1/test-results`.

The additional `view` parameter carries only the local grid presentation (see
below). It is never sent to the API and cannot make an empty/pagination-only
search request unfiltered results. Unknown URL keys, unknown/unavailable families,
invalid result statuses, malformed typed conditions and invalid pagination block
the request with a visible notice rather than silently broadening the query.
Raw malformed/unknown URL provenance is preserved across unrelated edits and
Search, including repeated parameters and invalid pagination. Search does **not**
silently drop unsupported constraints. Known malformed fields have explicit
replacement/removal controls; invalid family/status selections can be explicitly
unchecked or their chip removed. Confirming a repair/removal remains a draft until
Search. Unsupported names and invalid pagination must be corrected/removed in the
URL, or removed with **Clear all**. Cancellation, Escape and outside dismissal
never save a repair.

`limit` defaults to 50 and accepts integers from 1 to the API's default maximum of
1000; `offset` is a nonnegative safe integer. Valid pagination resets on Search;
invalid pagination remains blocking until explicitly repaired. A deployment may
configure a lower API maximum; such a request displays the retryable API error.

Pagination replaces pages; it never appends or mixes datasets. Server order is
newest result first (created time, then ID). The count is the backend's total,
while SvGrid filtering and sorting are **local to the loaded page** and do not
change that count.
The API does not provide snapshot pagination, so concurrent ingestion/deletion
can shift offset boundaries; refreshing or reapplying starts a fresh search.
View Run uses the configured family route and the SvelteKit
`testExecutionId`/`testResultId` deep links (including the deployment base path).
If a result's family has no configured route, the grid shows Run unavailable.

## Loaded result details

The native selection checkbox stays first, followed by **Run**, **Details**, and
the result columns. Details is a dense, keyboard-accessible Pragma action, not a
sortable/filterable data column. It does not select a row or change the search,
table view, URL or selection. One reusable native Pragma modal displays the exact
loaded result by test result ID, including after local sorting, filtering and
virtual scrolling; opening/closing it makes **no API requests**. Raw detail
context does not participate in the grid's global text filter.

**Test result details** contains Test Case (name, category, template ID, status),
Artefact (configured family display name, name, version, track, build architecture)
and Test Execution (ID, test plan, environment, status, execution creation time).
Created is the **execution's** timestamp, displayed in the browser's local time
with a timezone label and the original timestamp on hover; it is not the result
creation time used by the search date filters. Scalars use vertically stacked,
top-aligned label/value rows: a compact label column and the remaining modal width
for naturally wrapping values. Execution Metadata is a separate full-width,
semantic **Category | Values** table, with top-aligned cells and more space for
the stacked values. Categories and values are sorted and shown literally, with
an explicit empty message. Missing
optional values use an em dash. Every attached `test_result.issues` issue is
shown when present, with source, project, key, title and status. Nonempty IO Log
is full, selectable, escaped monospace text, preserving whitespace and soft-wrapping
even unbroken lines; it is never interpreted as HTML or silently truncated.
The log has its natural height in the **single scrolling modal body**, not its
own bounded scrollpane. Wheel/trackpad scrolling over fields, metadata, issues
or the log continues through that body. The labelled body region is the one
keyboard scroll stop (PageDown/End); the log adds no Tab stop.

Issue links intentionally target the **future internal** `${base}/issues/${id}`
path in a new tab with `noopener noreferrer`. The SvelteKit issue detail route is
not implemented yet: its current 404 is a known, accepted destination gap, not a
fallback to an external tracker. No issue detail page or attachment rules are
provided here. Footer **View Run** uses the same configured family route,
deployment base and execution/result deep link as the grid. An unconfigured
family has no guessed Run route, but its Details still works.

The responsive modal is at most about 900px wide with viewport margins and an
internally scrolling body; header and footer controls remain reachable in light
and dark themes. Native modal focus containment, Escape, outside click, header X
and footer Close apply. Closing restores the opening Details button, or the
labelled grid region if that virtualized cell disappeared or was recycled for
another record. Unmount removes the dialog/top-layer backdrop. Background body
scrolling is locked only while the modal is open.

Explicit/all-matches selection and exclusions, confirmed chip drafts and table
sort/filter/visibility survive opening/closing. An open chip editor is suspended
without discarding its unconfirmed input; reopening that same chip resumes it
(ordinary Cancel/Escape/outside dismissal still discards edits). It is not
automatically reopened or focused behind the modal. Pending suggestion/label
responses and grid view polling do not move modal focus. View-only history keeps
the same modal and focus. A meaningful query change, explicit Search/reapply,
pagination, session/loading invalidation or leaving the route closes details
safely; obsolete row callbacks cannot open a different dataset. Modal state is
ephemeral, never a URL parameter or another server query.

## Result selection

Native row checkboxes select by **test result ID**, not row position. The header
checkbox acts on the entire displayed, post-local-filter/sort backend page,
including virtualized rows not currently in the DOM. It does not select locally
hidden rows, other backend pages or all server matches. Explicit selected IDs
survive pagination and local filtering/sorting, so selections on other pages
remain counted even when not visible.

Only after **all IDs on the entire loaded backend page** are selected (not just
locally displayed rows) is the separate checkbox offered, labelled
`Apply bulk options to all ${MATCH_COUNT} matches`. Opting in creates a rule bound
to the normalized applied backend filters, excluding pagination and `view`, not
an enumerated/frozen result set. Unchecking individual rows adds exclusions;
checking them again removes exclusions. The selected count uses the latest
server match count minus exclusions, floored at zero, so concurrent changes can
change the count. Local grid filters and unapplied drafts never narrow this rule.

Turning the header off affects only displayed rows; it does not exit all-matches
mode or clear other pages. **Clear selection** clears everything globally.
Turning the all-matches option off drops the rule, exclusions and off-page
selection, retaining explicit selected IDs from the **entire current loaded
backend page**, including locally hidden rows (but not excluded rows).

Explicit **Search**, including reapplying unchanged filters, a new applied query,
**Clear all**, leaving the route or reloading reset selection. Draft/editor edits,
pagination and table-view changes preserve it. Selection is ephemeral per-route
state: nothing is written to the URL, storage or shared view, and selection sends
no network requests or mutations until a bulk workflow is explicitly opened
and submitted.

## Contextual issue actions

Selecting results reveals **Bulk actions** beside the selection summary and
**Clear selection**. Its Pragma chevron menu contains **Attach Issue…** and
**Detach Issue…**, followed by a separate group for **Create Rerun Requests…** and
**Delete Rerun Requests…**. Opening the menu and review refreshes session permissions;
selection alone never does. Disabled actions have visible explanations, including
unapplied drafts, unavailable results and unsupported scopes. All-matches
exclusions are not supported by the mutation API: remove the exclusions or
choose explicit rows. Date-only queries remain searchable, but all-query
mutations need a non-date condition; explicit selected IDs are still supported.
The client never enumerates all results or combines IDs with filters to work
around these limits.

One Pragma modal reviews the frozen selected IDs (including other pages) or
explicit all-matches query conditions and count. It excludes local grid filters,
sorting and pagination. The count is a preview, not a changed count or server
snapshot; query filters are evaluated against server data at submission time.
More than 50 results requires an acknowledgment in that same modal. Scope,
query/reapply, selection or logout changes require a new review. Details cannot
stack with the review. Existing condition editors are suspended, preserving
their confirmed and unconfirmed inputs; Cancel/Escape restores the bulk trigger.

The single-issue picker reuses the search issue suggestions and session label
cache. Choose a rich suggestion, enter one positive safe internal ID, or use a
same-origin `${base}/issues/123` or legacy `/#/issues/123` link. Supported external
HTTP(S) GitHub, Jira and Launchpad links are canonicalized to the existing server
formats; unsafe, foreign internal and arbitrary tracker URLs are rejected.
Attach can create or find the issue through the existing issue PUT API, requiring
`change_issue` separately. Detach never creates: external URLs must resolve to
one exact canonical existing issue in a bounded lookup; fuzzy/ambiguous or
incomplete matches require an internal ID or explicit suggestion instead.

Session permissions are refreshed again before mutation (and after a creation
request before attaching). Attachment normal/bulk, lookup and creation grants
are checked separately; confirmed global team grants work, while cached admin,
unknown, cancelled and superseded authorization fail closed. Server 401/403 and
validation errors stay inline. Submission disables duplicates, closing and
navigation. Network/5xx failures have an explicitly unknown outcome with no
automatic retry or same-review resubmission. Creating an issue and attaching it
are not atomic: a known issue ID is retained on failure, and an explicit retry
after a definite rejection uses that same ID without another PUT.

Success clears the reviewed selection and refreshes current results, counts and
loaded attachments without reloading the route or applying drafts. Query,
pagination, grid view and suspended condition inputs survive. The API does not
return a changed count, so already-attached/detached results may be unchanged.
Empty or out-of-range pages retain Previous-page navigation. **Close and refresh
results** is also available after partial/unknown outcomes for inspection.

## Rerun request review

The same contextual menu opens one Pragma review for Create or Delete Rerun
Requests. It cannot stack with issue review or Details. Reruns are whole
**build / environment / test plan groups**, not individual test results, and
multiple executions can share one group. No client-side group enumeration is
performed. Selection alone never sends requests.

For **all matches**, the original valid applied query is frozen without page,
view or local grid filters. All-matches exclusions and date-only queries are
unsupported even if adding a rerun guard would make them non-date predicates.
Creation intersects `rerun_is_requested=false`; deletion intersects `true`.
The independent **Only latest test executions** and **Exclude archived artefacts**
options default on for create and off for delete. They add `execution_is_latest=true`
and `artefact_is_archived=false` respectively. Unchecked options preserve existing
applied constraints, including `false`. A contradiction disables submission with
a reason; it never replaces the query to target different rows.

An independent `GET /v1/test-results` preview uses the effective conditions and
`limit=0`, with raw mutation metadata converted to repeated UTF-8 Base64 pairs
for GET. This does not change the search page's `limit>=1` contract. Options,
session changes and closing cancel obsolete previews; stale replies/errors cannot
enable submission. The summary counts **matching test results**, not request
groups or changed requests. A failed, pending or zero preview cannot submit.

For **explicit selected results**, retained result-to-execution context is
deduplicated across pages. Missing context disables the action; result IDs are
never substituted for execution IDs or fetched in bulk to reconstruct context.
The backend ORs IDs and filters, so guarded explicit selection cannot be expressed.
The review requires the distinct **Use these exact execution groups** opt-in.
This sends execution IDs only, with **no latest/archive/existing-request guards**;
it includes older executions and archived artefacts. Use an all-matches query
instead when eligibility guards are needed. The review shows selected result and
unique execution counts; actual request groups may be fewer. Exact creation can
**update existing groups' priorities**, not just create missing requests. Exact
deletion affects the whole group, even when identified by an older execution.

Create priority defaults to 0 and must be a safe integer from -1000000 to 1000000.
Higher-priority requests are listed first, not guaranteed to run first. Delete
has no priority. More than 50 target **results** requires acknowledgment in the
same modal, independently of execution deduplication; scope, options, priority
and preview changes reset it. Effective JSON and scope are frozen before the
fresh presubmit authorization check. Create sends
`POST /v1/test-executions/reruns?silent=true` (a null success body is valid);
delete sends `DELETE /v1/test-executions/reruns` with JSON and no priority.
IDs and filter criteria are never combined.

Normal `change_rerun` permission is always required. `change_rerun_bulk` is also
required for queries or more than one deduplicated execution ID, not merely more
than one result. Confirmed admin and global team grants are supported; cached
admin, unknown/cancelled/superseded authorization and AMR-only grants that `/me`
does not expose cannot authorize. Permissions are revocable and refreshed at
open and immediately before submit. Observed scope/logout changes permanently
invalidate that review even if the same selection or user returns during an await.
The server remains authoritative: 401/403 and other failures stay inline, and
require a new review. Network/5xx outcomes are explicitly unknown, with no
automatic retry or same-review resubmission. Close and refresh results allows
inspection before starting over.

Submission blocks duplicates, closing and navigation. Success clears only the
matching reviewed selection and refreshes the **current applied** results, count
and loaded rerun state without applying drafts or reloading the route. Query,
pagination, grid view and the same suspended condition-editor inputs survive;
an obsolete completion cannot clear a newer selection. The API does not report
a changed count, and concurrent group changes can leave requests unchanged or
update an existing priority. This is not a server snapshot or an atomicity promise.

## Table layout and shareable views

Like the artefact list, the search page fills the viewport below the app shell's
padding. Headings, wrapping chips, actions, notices and server counts take their
natural height; the virtualized grid uses the remaining space and scrolls
internally. Backend pagination stays below the grid. Condition popovers and grid
menus are not clipped by a page-level overflow container.

Grid interactions automatically replace the current history entry's `view`
parameter, without navigating, fetching, cancelling a pending search, resetting
drafts/editors or moving focus/scroll. The address bar is the shareable link;
reload and browser back/forward restore its view. The parameter uses the same
encoding as the artefact grid: sorting, global text, per-column operator filters,
facet selections and column visibility overrides relative to defaults. All
search columns are visible by default. Column widths, order and pinning are
deliberately not shared. There are no named views or session autosave on search.
Malformed or oversized values fall back to defaults; unknown/inapplicable
columns are ignored. Removing `view` restores the shared defaults, not stale
filters from the previous URL. Restoring a link does not rewrite it.

**Search** (including reapplying an unchanged query) and backend pagination
preserve the view on the new loaded page. **Reset table view** removes only the
shared grid customization, retaining the backend query, result count and drafts
without a fetch. Returning to the default table view removes the
parameter automatically. **Clear all** resets both the backend search/drafts and
the table view. Local table filters/sort still apply **only to the loaded page**,
not the server total or other pages.

The route adapter reads SvelteKit 3's `page.shallow.url` as well as `page.url`.
View writes use the non-navigating `replaceState` API, preserving `page.state`.
The shared shell exempts native history transitions differing only in `view`
from its loading lock/overlay: even a transient `inert` during native Forward
would blur an editor. It captures the visible source URL in `beforeNavigate`
and identifies that particular navigation by its public `complete` promise.
Query/pagination changes, other routes and non-history navigation still block;
superseding navigation cannot inherit the exemption. This does not rely on
`navigating.shallow`, which the installed runtime does not expose.
The history adapter
rejects outgoing writes from a different URL or while a route navigation is in
progress. SvGrid provides sorting/filter callbacks but no visibility callback,
so visibility is checked every 250ms while the grid is mounted (with cleanup).

## Deliberately deferred

Execution-status filtering; saved views and export. Attachment rules and other
mutation workflows beyond issue attachment and rerun requests remain excluded.

## Local checks

From `frontend/sveltekit`, install locked dependencies with `npm ci`, then run
`npm run check`, `npm run build`, `npm test`, and `npm run lint`.
`tests/test-results-search.test.js` tests the backend/OpenAPI and URL contracts,
request defaults, races, auth revalidation, and actual mounted Pragma controls
and SvGrid rendering/interactions in Happy DOM. Mounted regressions cover the
searchable 18-field picker, duplicate/empty prevention, all editor types,
confirmed drafts versus applied queries, cancellation/dismissal and focus,
URL restoration, long values, clear and pagination. Additional regressions cover
shareable sort/global/column/facet/visibility state, replace-only history writes,
restoring/removing invalid views, repeated parameters, drafts/editor/focus and
grid identity across view-only changes, pending result/auth requests, retained
views through Search/pagination, and resetting the table independently. Typed
contract and suggestion tests cover metadata/date/ID modes, malformed URL
provenance and explicit repairs, debounce, keyboard/multi-select, draft family
context, local failures, cancellation, late-body and session races. Selection
tests cover ID-native page/header scope, query-bound all-matches/exclusions,
reset/preserve rules and no selection traffic or persistence. Happy DOM lacks native
popover and dialog/Invoker Commands support, so a test-only adapter models native toggle/light-dismiss
events, including ignored focus attempts before native opening completes.
Details regressions additionally cover actual column order, ID mapping after
local sorting/filtering, all/empty sections, multiple internal issue links,
execution timestamps/timezones, Unicode metadata, full malicious/large literal
logs, missing configured families, selections, suspended drafts, pending lookup
focus, view-only preservation, invalidation, recycled-cell focus fallback and
unmount. The adapter is test-only, not an application dialog fallback or proof
of real native focus containment.
Mounted tests also verify viewport constraints with supplied geometry; real
scrollbar reachability still needs browser QA. These tests use mocked API
responses, not a live backend integration or
a real-browser visual test; real top-layer layout, keyboard traversal, and
desktop/800px screenshots require separate browser QA.

### Native history browser regression

`tests/search-view-history.browser.js` is an opt-in integration check against a
running Vite frontend and real seeded API/SSO stack, not part of the mocked
`npm test` suite. It uses SvelteKit's actual public `replaceState`/`pushState`
APIs and native browser Back/Forward, twice each. It asserts focus never leaves
the editor, no transient `inert` or loading overlay appears, the same
grid/editor/popover/input and confirmed
and unconfirmed drafts survive, page state survives, the table view restores,
and traversal sends zero API requests. The real debounced suggestion request
finishes before traversal measurement begins; it is not exempted from the
zero-traffic assertion during traversal. No requests are intercepted or mocked.

Use an externally installed Playwright Core and Chromium (no project dependency
or lockfile changes), supply test SSO credentials privately through
`TEST_OBSERVER_USERNAME` and `TEST_OBSERVER_PASSWORD`, and run, for example:

```sh
PLAYWRIGHT_MODULE=/tmp/opencode/svelte-search-qa-tools/node_modules/playwright-core/index.mjs \
CHROMIUM_EXECUTABLE=/path/to/chromium \
SEARCH_URL=http://localhost:30001/wip/test-results \
QA_ARTIFACT_DIR=/tmp/opencode/search-view-history \
PW_TEST_SCREENSHOT_NO_FONTS_READY=1 \
node tests/search-view-history.browser.js
```

The script expects real loaded rows and a Vite dev server so it can resolve the
public SvelteKit modules. Supplying credentials forces the real public SAML login
flow even if development permits anonymous result reads; the script checks
`GET /v1/users/me` using the browser session and reports only status and an
authenticated boolean, never the personal payload. Without credentials it can
also run against a development stack permitting anonymous reads, but that is not
authenticated SSO evidence. It writes only an assertion report and search-page
screenshot under `/tmp/opencode` by default, never credentials, cookies, tokens or
storage state. Do not enable traces, HARs or login screenshots. Start/stop only
your own stack with `docker compose down` **without `-v`**, preserving volumes and
unrelated projects.

### Native Details browser regression

`tests/search-result-details.browser.js` is another opt-in regression using real
Chromium, Vite, the locally seeded API and **required TEST SSO**. It does not
intercept successful requests or modify seed data. Use the same external
Playwright/Chromium and private credential environment as above, for example:

```sh
PLAYWRIGHT_MODULE=/tmp/opencode/svelte-search-qa-tools/node_modules/playwright-core/index.mjs \
CHROMIUM_EXECUTABLE=/path/to/chromium \
SEARCH_URL=http://localhost:30001/wip/test-results \
QA_ARTIFACT_DIR=/tmp/opencode/search-details \
PW_TEST_SCREENSHOT_NO_FONTS_READY=1 \
node tests/search-result-details.browser.js
```

It checks 1920px, 1440px, 960px and 800px in light/dark: real loaded row IDs after sorting,
Run targets, native keyboard opening/Tab containment/Escape/backdrop/X/Close and
focus restoration, viewport/body scroll/footer reachability, explicit selection
and all-matches exclusions, no API or URL changes on open/close, confirmed and
unconfirmed drafts, and native view-only Back/Forward modal/focus retention.
Shared assertions in `tests/details-layout.browser.js` verify actual scalar row
geometry, a full-width real metadata table with complete sorted literal text,
top-aligned cells, wrapping, no descendant scroll containers, and header/footer
visibility. Available real rows exercise populated/empty logs and issue hrefs
without requiring the future issue destination to succeed. The JSON report
explicitly notes live data gaps; large/complex/malicious examples and zoom use the
separate browser fixture below, not claims about the seed. Reports/screenshots
stay outside the repository under `/tmp/opencode`; no login screenshots, traces,
HAR, credentials, cookies, tokens, personal `/me` payload or storage state.

### Representative Details component browser fixture

The existing small seed is not representative of large production details.
`tests/search-result-details-fixture.browser.js` starts and stops its **own
standalone loopback Vite server** with `tests/fixtures/details` as its root. That
test-only entry mounts the actual `SearchResultDetails.svelte` and imports the
exact application/Pragma/responsive-token styles. It is not a SvelteKit route,
production entry, static HTML mock, alternate modal implementation, or API
response interception. It needs no backend, SSO credentials, seed mutations,
project dependency additions, or production/staging access.

```sh
PLAYWRIGHT_MODULE=/tmp/opencode/svelte-search-qa-tools/node_modules/playwright-core/index.mjs \
CHROMIUM_EXECUTABLE=/path/to/chromium \
QA_ARTIFACT_DIR=/tmp/opencode/details-layout/fixture-browser \
PW_TEST_SCREENSHOT_NO_FONTS_READY=1 \
node tests/search-result-details-fixture.browser.js
```

The reproducible synthetic data includes 41 metadata categories, long repeated
keys (including `pipeline:workflow_hash` and `failure:charm:component:status`),
many alternatives, multiline stack traces/messages/relations, long scalar paths,
Unicode/punctuation/malicious-looking literal text, attached issues, and a large
multiline log with indented table-like output and long unbroken tokens. A second
short record covers empty optional fields/sections and an unconfigured family.
The runner verifies every metadata value and the entire log, not a sample or
truncated preview. It checks scalar/table geometry, natural short-record height,
no nested scrolling/clipping, selectable literal content, PageDown/End, real
wheel events **over the log at start/middle/end** moving the body, background
locking, native modal/Tab order, Escape and internal issue links.

The matrix is 1920/1440/960/800 × 900 plus 800 × 600, light/dark, at native
Chromium **100% and 120% browser zoom**. Zoom is set using Chromium's own Settings
API in a disposable isolated profile, with actual viewport/DPR checked (not CSS
zoom, pinch scaling, or an emulated DPR). Physical content viewport dimensions
are maintained, so 120% zoom reduces the CSS viewport as a user would see. This
also exercises the typography-token breakpoint above 1681px. The runner closes
its browser/server and removes its disposable profile in `finally`; its Vite
cache, screenshots and explicitly labelled JSON fixture report stay under the
artifact directory. Pragma's stylesheet may load its normal external static font;
the fixture makes zero Test Observer API calls. **A fixture pass is not live API,
exact production-record, or production-data evidence.** Use the native live
regression independently, and check actual user data after deployment.
