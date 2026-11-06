<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Test result search

`/test-results` is the canonical read-only Search route for the current
experiment. Five routes compare its presentations: Option 1 is the custom
infinite-scroll search; Options 2, 2.5, 3 and 4 are page-based alternatives. All
support the same server-backed exact filters, Run links and on-demand Details.
Applied filters and, for Options 2, 2.5, 3 and 4, page state live in the URL, so direct links,
reloads and browser back/forward restore the search. Search has no row selection
or mutation actions; reusable issue/rerun/rule components remain available to
other workflows. This is the canonical SvelteKit Search guide.

## Search prototype routes (Options 1–4 and 2.5)

The five prototype routes share the same exact server-side Search filters and
read-only result actions, but intentionally compare different table/filter
presentations. They are not expected to look or behave identically as tables:

| Option | Route                      | Presentation                                                                                                                                                                                                                  |
| ------ | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1      | `/test-results`            | Custom SvGrid with 23 columns, 18 exact-filter editors and infinite server range requests. Created is the third column. The URL's legacy `limit`/`offset` values are stripped; SvGrid requests its own default 50-row blocks. |
| 2      | `/test-results/option-2`   | Pragma wide Table with 23 columns and the existing exact-filter controls in the relevant column headers. Created is third. This header-filter layout is unchanged.                                                            |
| 2.5    | `/test-results/option-2-5` | Pragma wide Table with 23 columns and a dedicated second `<thead>` row of exact-filter controls aligned beneath their field-label columns. Created is third. This is a separate route and presentation from Option 2.         |
| 3      | `/test-results/option-3`   | Pragma compact Table with 10 columns, Created first, and a SidePanel filter surface.                                                                                                                                          |
| 4      | `/test-results/option-4`   | Pragma compact Table with the same 10 columns and Created-first order, plus historical-style editable filter chips.                                                                                                           |

Options 2, 2.5, 3 and 4 share URL presentation state: `page` is 1-based and
defaults to 1; `page_size` defaults to 50 and accepts 25, 50, or 100. A request
maps to API `offset=(page - 1) * page_size`, `limit=page_size`, and
`include_count=true` so the page can show the exact range and pager. Page and
page-size navigation preserve every filter; changing page size resets to page 1,
and applying a filter also resets `page` to 1 while retaining `page_size`.
Option 1 does not use this presentation state: its infinite scroll strips legacy
URL `limit`/`offset` and starts with `offset=0&limit=50`.

Options 2, 2.5, 3 and 4 show the exact result range, Previous/Next controls,
compact numbered page windows, a numeric **Go to page** form, and a 25/50/100
page-size selector. The window shows every page when there are at most seven;
otherwise it keeps the first, current page and its neighbors, and last page with
ellipses for gaps. Numeric jumps clamp to the valid range. Once the exact count
arrives, an out-of-range direct URL is canonicalized to the last valid page (page
1 for an empty result). An empty result shows `0–0 of 0`, keeps the page-size
selector, and has no page-jump target.

Every option carries the same 19 canonical exact filters to
`/v1/test-results/search-page`: `families`, `test_result_statuses`,
`test_execution_statuses`, `artefacts`, `artefact_versions`, `artefact_tracks`,
`environments`, `test_plans`, `test_cases`, `artefact_stages`,
`artefact_is_archived`, `rerun_is_requested`, `execution_is_latest`, `issues`,
`reviewer_ids`, `execution_metadata`, `from_date`, `until_date`, and
`template_ids`. In particular, `test_execution_statuses` is a canonical filter
in every route. Alternatives within a field are exact-match ORs; different
fields are combined server-side. No option filters or sorts only the rows
already loaded in the browser.

All five remain read-only: configured Run links retain the deployment base and
execution/result deep links, and Details is fetched lazily for a selected row.
API authorization remains authoritative for result and Details reads; 401/403
responses are revalidated against the current session and presented as the
appropriate login, forbidden, or session-check state. These shared contracts do
not make the presentations equivalent. Options 1, 2 and 2.5 use the wide
23-column table; Option 2 retains its unchanged column-header filters, while
Option 2.5 puts the same exact-filter triggers in a dedicated second header row.
Options 3 and 4 use a 10-column compact table with Created first and expose
filters in a SidePanel or editable chips, respectively. All 19 filters and all
sorting/filtering remain server-side; there is no client-only filtering or
sorting of loaded rows.
The compact columns are Created, Artefact, Test Case, Test Execution ID, Status,
Track, Version, Environment, Test Plan and Actions. The wide tables keep their
23-column order, including Run, Details and Created as the first three columns.

The opt-in cross-option browser QA uses actual Chromium and mocks every API call
with synthetic loopback fixtures. It does not require or contact a live API,
SSO service, database, or credentials and is not live integration evidence.

## Wide-table column filters (Options 1, 2 and 2.5)

On Option 1, all 18 filter groups start in their own SvGrid column header and open
an anchored menu attached to that header. Option 2 keeps its existing
column-header filters unchanged. Option 2.5 presents the same field-specific
filter triggers in a second `<thead>` row directly beneath the 23 field labels;
nonfilterable action/display columns remain empty in that row. Created is one
group with inclusive From and Until bounds. The Search URL/API contract accepts
all 19 canonical filter keys; every key has an exact editor. Conditions are sent
to the server and are not evaluated against only the loaded blocks. These
wide-table variants do not use an **Add filter** picker, condition-chip row, or
detached filter panel; Options 3 and 4 use the distinct compact filter surfaces
described below.

Column menus update a single shared draft directly. High-cardinality Artefact,
Environment, Test Case and Test Plan values reuse their lookup APIs; a suggestion
or explicit exact value must be selected before it becomes a condition. Other
exact text lists accept comma-separated values. Neither editing nor suggestion
lookup fetches test results or changes the URL.
Selected values can be removed individually or cleared from their column menu.

For header-based filtering (Options 1, 2 and 2.5), only one column menu is open
at a time, without expanding the page layout.
Placement is anchored to its trigger within the visible viewport, independent of
the result grid's document height. It follows scrolling/resizing and scrolls
internally when the available space is short, keeping all actions reachable.
Grid column menus use the same viewport anchoring and internal scrolling; each
menu is rendered from its own column header and closes when focus or pointer
interaction moves outside it.
Focus enters the menu after opening completes, so typing works without an extra
Tab. Escape closes the menu and returns focus to its trigger; outside click
closes it without stealing focus from the clicked control. Search menus write
the shared draft as values are selected; pending suggestion query text is not a
selected value. Tab follows normal browser order; Enter activates a focused
button, and Enter in a suggestion query never selects or saves implicitly.
Backend query URL changes close and reset transient menus; Option 1's
table-view-only URL changes preserve its column drafts, open menu and keyboard
focus.

**Search** applies the entire column-filter draft and updates the URL. On Option
1 it purges the range cache and restarts at row 0; on page-based options it
resets to page 1 while retaining `page_size`. Column-menu edits never fetch.
**Changes not applied** marks a draft that differs from the URL, and existing
results are labelled as belonging to the previous query. Lookup text that has
not been explicitly selected or added is not part of the draft; all column-menu
selections are applied together when Search is selected.

On Option 1, **Clear all** immediately removes the URL query, column filters and
table view, purges all blocks and loads the unfiltered recent range
(`limit=50`, `offset=0`). On Options 2, 2.5, 3 and 4 it clears filters and starts an
unfiltered page-one request while retaining a valid `page_size`. Removing the
last selected value instead remains a draft until Search is selected; Search
then clears the applied query. A URL with no filters, or only presentation
parameters, is a valid unfiltered recent-results request.

## Compact filters (Options 3 and 4)

Option 3's **Filters** button opens a SidePanel with the shared exact editors for
all 18 filter groups; its footer **Search** applies the draft, while **Clear all**
clears the query. Option 4 uses **Add filter** to select a canonical field and
editable chips to review, edit or remove active conditions. A chip's **Save
changes** updates the draft; the page-level **Search** is still required to apply
it. Created From and Until are independently editable bounds. Both compact
surfaces serialize the same 19 canonical exact filters as the wide tables and
never filter or sort only the rows already in memory.

## Option 1 filter and row mapping (wide-table columns shared)

| Column/filter      | URL/API key               | Editor and API mapping                                                                                        |
| ------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Created            | `from_date`, `until_date` | Inclusive bounds on `TestResult.created_at`; either bound may be omitted.                                     |
| Family             | `families`                | Configured labels; requests use the API family name.                                                          |
| Artefact           | `artefacts`               | Lookup suggestions and explicit exact values.                                                                 |
| Stage              | `artefact_stages`         | Configured family stages; `(none)` selects an explicitly empty stage (the row API returns `""`).              |
| Archived           | `artefact_is_archived`    | Nullable boolean equality: Any, No or Yes.                                                                    |
| Test Case          | `test_cases`              | Lookup suggestions and explicit exact values.                                                                 |
| Execution Status   | `test_execution_statuses` | Exact set of existing execution statuses.                                                                     |
| Rerun Requested    | `rerun_is_requested`      | Nullable boolean equality; a rerun exists for the test-plan/build/environment group.                          |
| Latest Execution   | `execution_is_latest`     | Nullable boolean equality; latest means no higher-ID execution in the same test-plan/build/environment group. |
| Result status      | `test_result_statuses`    | Exact set: `PASSED`, `FAILED`, `SKIPPED`.                                                                     |
| Track              | `artefact_tracks`         | Typed exact comma-separated values.                                                                           |
| Version            | `artefact_versions`       | Typed exact comma-separated values.                                                                           |
| Environment        | `environments`            | Lookup suggestions and explicit exact values.                                                                 |
| Test Plan          | `test_plans`              | Lookup suggestions and explicit exact values.                                                                 |
| Template ID        | `template_ids`            | Exact typed value; no complete lookup endpoint.                                                               |
| Issues             | `issues`                  | Specific positive IDs or mutually exclusive `any` / `none`; issue suggestions.                                |
| Reviewers          | `reviewer_ids`            | Specific positive IDs or mutually exclusive `any` / `none`; user suggestions.                                 |
| Execution Metadata | `execution_metadata`      | Literal category/value pairs; known map loads when its editor opens.                                          |

The 23 visible wide-table columns (Options 1, 2 and 2.5) are ordered Run,
Details, Created, Family, Artefact,
Stage, Archived, Test Case, Category, Execution ID, Execution Status, Rerun
Requested, Latest Execution, Result status, Track, Version, Architecture,
Environment, Test Plan, Template ID, Issues, Reviewers and Execution Metadata.
Created displays UTC `YYYY-MM-DD HH:mm:ss`; fractional seconds and the timezone
suffix are omitted. Issues, Reviewers and Execution Metadata are the final
filter-bearing columns. Category, Execution ID and Architecture are separate
display-only columns.

All 18 filter groups have active exact editors in the wide-table header surface
(Option 2.5 places them in its second header row): exact/set lists, inclusive
Created bounds, nullable boolean equality (Any/No/Yes), issue/reviewer ID or
`any`/`none` modes, and literal metadata category/value pairs. The table above
describes the full editor and row-value association; these conditions are not
API-only. Options 3 and 4 expose the same exact filter model in their SidePanel
and chips, respectively. Contains/prefix operators are not offered or
translated. High-cardinality values are not inferred from cached result blocks.
Category, Execution ID and Architecture remain display-only because the endpoint
has no corresponding predicates. Run and Details are nonfilterable actions.
Global text search remains disabled because the endpoint has no global-search
parameter.

Issues, Reviewers and Execution Metadata have active wide-table editors and are
sent with every Search request; they are not locally applied to loaded rows.
Compact issue ID/key/title summaries, reviewer ID/name/Launchpad-handle
summaries, and every literal metadata category/value pair are present in the row
response. Reviewer email and other profile fields are excluded. In Option 1's
wide grid, the Issues, Reviewers and Execution Metadata cells render every item
as a compact preview, but SvGrid keeps row height fixed and clips overflowing
preview content. Each
cell therefore also has a keyboard-accessible **View all …** affordance that
opens one shared, responsive design-system modal with every complete item and
wrapping. Issue key/title entries link to the internal issue-detail route under
the configured deployment base, in a new tab with `noopener noreferrer`. That
route supports issue results and rule/rerun workflows (see [Issues](#issues-workflows)). Execution Metadata uses a semantic
**Category | Value** table, while Issues and Reviewers retain their list layout.
The modal is centered, bounded by viewport margins and scrolls its body
internally while keeping its header and close controls available. Its item
snapshot is independent of virtualized/recycled grid cells; close returns focus
to the trigger when it still represents the same row, or to the grid region when
it does not. Opening that affordance does not fetch Details. Details remain
on-demand and continue to use the separate modal endpoint.

## Shared issue, reviewer and metadata filter behavior

| Filter             | URL/API key          | Editor contract                                                                                                            |
| ------------------ | -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Issues             | `issues`             | Positive safe integer IDs with rich suggestions/manual IDs, **Has any issue** (`any`), or **Has no issues** (`none`).      |
| Reviewers          | `reviewer_ids`       | Positive safe integer IDs with rich suggestions/manual IDs, **Has any reviewer** (`any`), or **Has no reviewer** (`none`). |
| Execution Metadata | `execution_metadata` | Literal category/value pairs, with locally filtered category/value options and individual pair removal.                    |

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

### Suggestions and typed exact values

Issues and Reviewers retain rich issue/project/title/source and
name/handle/email suggestions without a family restriction, matching Flutter.
They use existing `GET /v1/issues` and `/v1/users` contracts, start after two
trimmed characters and a 250 ms debounce, and are capped at 10 IDs. Query replies
are not cached. Requests are aborted and late bodies/errors ignored when query,
field, editor or session context changes. Failures, including
authentication/permission errors, stay local with retry and a manual exact-ID
path, not global error toasts.

Artefact, Environment, Test Case and Test Plan use lookup suggestions and
explicit single-value exact additions, never result-derived facets. Artefact
Version, Artefact Track and Template ID have no complete lookup endpoint.
Family labels and stage choices use configured family data; filter values use
API family names and are not inferred from loaded result blocks. The explicit
empty stage is shown as `(none)`; a missing stage renders as unavailable instead.

Metadata lazily loads `GET /v1/execution-metadata` when its editor opens. Focusing
Category shows known categories; selecting one focuses Value and reveals that
category's known values, including before a query is typed. Both lists filter the
known map locally and scroll internally, showing up to 50 matches. Arrow keys
highlight options and Enter selects; Enter never submits the editor. The map is
cached only in memory for five minutes in the current API/session/profile/permission
context. Reopening can reuse it; typing never refetches it, and cancelled replies
cannot fill the cache. Manual literal pairs remain available, including when the
map is empty or unavailable. **Add pair** adds the pair and clears its inputs;
changing category clears pending value text so it cannot be assigned to the wrong
category. Pending category/value text is not a filter until **Add pair** is
selected.
Suggestion selection never fetches test results.

### Metadata wire format and active date bounds

Metadata predicates are ANDed across categories and ORed across values within a
category. Each wire pair is
`Base64(UTF8(category)):Base64(UTF8(value))`, repeated for each value, using standard
padded Base64, not the table view's base64url. Comma-separated encoded pairs also
restore. Decoded Unicode, punctuation, commas, colons and spaces remain literal.
The editor accepts separate category/value inputs, not wire encoding or delimiter
parsing. Categories and values each require 1–200 Unicode characters. Invalid
encoding, UTF-8 or lengths block the search locally.

The **Created — From/To** bounds apply inclusively to `TestResult.created_at`
in all five variants. Each Search date editor exposes only a native
`datetime-local` picker with whole-second precision. The selected wall-clock
fields are interpreted as UTC (not browser-local time) and serialize as
`YYYY-MM-DDTHH:mm:ssZ`; if the browser supplies minute precision, `:00` is
appended. The picker never converts through the browser timezone.

The existing URL parser and API continue to accept valid offset and fractional
timestamps. Restored query values remain the source of truth and are preserved
byte-for-byte in the URL/API when the editor is merely opened/closed or another
filter is changed. Only an existing canonical UTC whole-second `...Z` value is
shown in the picker. A valid offset or fractional value that cannot be
represented there appears as an empty picker with a note to select a new UTC
time or clear that bound; it is never projected, rounded or silently dropped.
Changing a picker explicitly replaces only its bound with the selected UTC
whole-second instant, and clearing it removes only that bound. Options 1–3 show
the bound headings **Created — From (UTC)** and **Created — To (UTC)**. Option 4
keeps its chip labels without the timezone suffix and shows `(UTC)` in the open
date-editor heading.

Timestamps must be valid
Gregorian ISO instants (`YYYY-MM-DDTHH:mm:ss[.fraction]Z` or an explicit `±HH:MM`
offset), with no rollover or assumed local timezone. Bounds may be one-sided;
From must not exceed Until, comparing offsets and fractional precision without
JavaScript millisecond truncation. Bounds must be exactly representable at backend
microsecond precision: nonzero digits beyond six fractional places are rejected;
additional trailing zeros are allowed. Input timestamps are retained, never
rounded or silently normalized. Either bound can be active by itself; a range
condition is meaningful even when it is the only filter.

Invalid timestamp precision and reversed ranges block the Search request until
the editor is corrected. Corrections send the exact corrected text while keeping
unrelated filters and (for Options 2, 2.5, 3 and 4) `page_size`; a successful filter change
starts at page 1.

## URL and result contract

Lists use backend **exact-match** semantics, not substring search. Alternatives
within one list are ORed; different filters are ANDed. Page URL lists can be
comma-separated, repeated, or both, matching Flutter. Whitespace is trimmed and
values deduplicated; empty entries are removed. Commas delimit list values and
cannot be literal characters in names. API calls use
repeated parameters. For example,
`?artefacts=one,two&test_result_statuses=FAILED` requests
`artefacts=one&artefacts=two&test_result_statuses=FAILED` from `/v1/test-results/search-page`.

All five options use the dedicated `/v1/test-results/search-page` endpoint; the
existing `/v1/test-results` contract remains unchanged for other clients. The
endpoint returns compact row values for Family, Stage, Archived, Execution
Status, Rerun Requested, Latest Execution, Template ID, Issues, Reviewers and
Execution Metadata, in addition to the existing result/execution/artefact
values. Option 1's 23-column grid presents these values alongside its full
filter columns; the paginated wide and compact tables present their documented
column subsets. Stage `""` means explicitly empty, not unavailable. Rerun state is
scoped to the test-plan, artefact-build and environment group. Latest means no
higher-ID execution exists in that same group. Issue summaries contain only ID,
key and title; reviewer summaries contain ID, name and optional Launchpad handle,
never email. Metadata returns literal category/value pairs sorted by category
then value. These lightweight summaries omit full issue/profile/detail records;
the potentially large IO log and expanded issue details are not included in each
row.
For Option 1, the first range request asks for the exact count. Later range
requests set `include_count=false`; the endpoint returns `count: null`, and the
page reuses the exact count cached for the current filter set. Changing filters
starts a new search and obtains a fresh count. Options 2, 2.5, 3 and 4 request
`include_count=true` on each page so their range, page window and pager use the
server's exact total.

Opening Details fetches `/v1/test-results/search-page/{test_result_id}`. That
response contains only modal data, including the I/O log; it is not downloaded
for every table row.

Option 1's additional `view` parameter carries only column visibility (see
below) and is never sent to the API. Unknown URL keys, invalid result statuses and
malformed active conditions block the request with a
visible notice rather than silently broadening the query. Raw malformed/unknown
URL provenance is preserved across unrelated edits and Search. Search does **not**
silently drop unsupported constraints. Malformed active fields with a current
filter editor have explicit replacement/removal controls; hidden malformed fields
must be corrected in the URL or removed with **Clear all**. Invalid result
statuses can be explicitly cleared from the current variant's filter surface.
While a query is blocked, the empty results table remains mounted with its filter
controls, so repairs remain reachable without requesting or locally filtering
results. A repair/removal remains a draft until
Search. Unknown field names must be corrected/removed in the URL, or removed with
**Clear all**. Dismissing a menu does not apply the query; previously selected
values remain in the draft for Search.
All 19 canonical filter keys, including `execution_is_latest`, are supported by
the Search URL parser and repeated API request serializer. Malformed values still
block requests and show an actionable **Search not applied** alert; **Clear all**
removes the constraints and loads recent results.

On Option 1, legacy `limit` and `offset` URL parameters are deliberately ignored
and removed with a replace-only URL update. They are not filters, do not block
malformed condition checks, and never contribute to a grid request. This
preserves all condition and `view` parameters while migrating older page links.
Every Option 1 block request uses SvGrid's exact range: `offset=startRow` and
`limit=endRow-startRow`. Blocks are 50 rows (and cannot exceed the API maximum
of 1000); the initial request is `offset=0&limit=50`.

Option 1's SvGrid requests blocks for the visible range and scrolls through one
result set;
it keeps at most eight blocks cached and runs at most two requests concurrently.
Each variant's filter surface writes the same canonical draft model, and every
page/block request repeats all applied conditions. Option 1's built-in SvGrid
local sorting, generic operator menus and global search remain disabled so
unloaded rows cannot be silently omitted or reordered. Its menus are rendered by
each column's supported header template. The grid uses SvGrid 3.0.20's
`externalFilter`/`onFiltersChange` contract to report draft filter state;
the page adapts that state into the existing API query and never tests only
loaded blocks. Generic operator menus are not exposed because this version has no
public per-column operator allowlist and choices such as contains, prefix, regex
or inequality cannot be represented by this endpoint's exact-match contract.
Across all five options, canonical conditions retain their field types: exact
lists, nullable booleans, ID lists or `any`/`none`, metadata category/value
pairs, and inclusive date bounds. No option evaluates predicates against loaded
rows or locally sorts the API response.
The API's `count` is the server total and defines the end of a page or Option 1's
list; short final pages/blocks are rendered correctly. Results retain backend
newest-first order (created time, then ID). The API does not provide a snapshot
across offset requests, so concurrent ingestion/deletion can shift boundaries;
reapplying Search or Clear all starts a fresh result request.
View Run uses the configured family route and the SvelteKit
`testExecutionId`/`testResultId` deep links (including the deployment base path).
If a result's family has no configured route, the results table shows Run
unavailable.

## Result details and actions (all options)

The wide tables (Options 1, 2 and 2.5) have the 23 columns in the order listed
above: Run, Details, 18 filter-bearing columns (Created is one range group),
Category, Execution ID and Architecture. The filter/display columns keep Category
beside Test Case and place Architecture immediately before Environment. In these
wide tables Run and Details are the leading nonfilterable actions. Options 3 and
4 instead keep the 10 documented compact columns with Created first and Details
and Run in the trailing Actions column. All variants display Created as UTC
`YYYY-MM-DD HH:mm:ss`, without fractional seconds or a timezone suffix. No
variant has row selection, local sorting/filtering or global text search.

Details is a dense, keyboard-accessible Pragma action. It does not change the
search, table view or URL. One reusable native Pragma modal displays the exact
loaded result by test result ID, including after paging or infinite scrolling.
Opening Details fetches that result's detail response on demand; closing it does
not fetch. Active filters are always applied through server queries.

**Test result details** contains Test Case (name, category, template ID, status),
Artefact (configured family display name, name, version, track, build architecture)
and Test Execution (ID, test plan, environment, status, execution creation time).
The Details section's Created value is the **execution's** timestamp, displayed
in the browser's local time with a timezone label and the original timestamp on
hover. It is distinct from the results table's Created column and date filter, which use
`TestResult.created_at`. Scalars use vertically stacked,
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

Issue links target the internal `${base}/issues/${id}` path in a new tab with
`noopener noreferrer`, not an external tracker. The issue-detail page displays
the issue and supports attachment-rule inspection, enable/disable and confirmed
deletion, plus the separate [issue-scoped result and rerun workflows](#issues-workflows).
Footer **View Run** uses the same configured family route,
deployment base and execution/result deep link as the grid. An unconfigured
family has no guessed Run route, but its Details still works.

The responsive modal is at most about 900px wide with viewport margins and an
internally scrolling body; header and footer controls remain reachable in light
and dark themes. Native modal focus containment, Escape, outside click, header X
and footer Close apply. Closing restores the opening Details button, or the
labelled results region if that virtualized row disappeared or was recycled for
another record. Unmount removes the dialog/top-layer backdrop. Background body
scrolling is locked only while the modal is open.

Filter drafts survive opening/closing; Option 1 also retains column visibility.
An open filter editor is hidden before the Details dialog while its input remains
mounted; it is not automatically reopened or focused behind the modal. Option 1's
view-only history and view polling keep the same modal and focus. A meaningful
query change, explicit Search/reapply,
session/loading invalidation or leaving the route closes details safely; obsolete
row callbacks cannot open a different dataset. Modal state is
ephemeral, never a URL parameter or another server query.

## Read-only Search experiment

All five Search variants support reading result data only. They have no row
selection, contextual issue attach/detach or rerun actions, or query-based Create
Attachment Rule action. Run and Details remain available on loaded rows,
including the initial unfiltered results. Conditions, paging/infinite scrolling,
column visibility where available, and Details are read operations and do not
mutate backend records. Sorting and local filtering are disabled; the active
variant's filter surface updates state that is applied only through server
queries.

The existing mutation components and family/review workflows are not removed by
this experiment; they are simply not wired into any Search route.

## Table layout and shareable views

All five Search routes fill the viewport below the app shell's padding. Headings,
actions and notices take their natural height. Option 1's virtualized grid uses
the remaining space and scrolls internally, loading server blocks as needed.
Options 2, 2.5, 3 and 4 keep the table itself as the vertical and horizontal
scroll region and keep the result range, page controls and page-size selector in
a separate visible pager outside that region. Scrolling the table does not
require document or main-content scrolling. Column menus are not clipped by a
page-level overflow container.

### Option 1 column visibility and shareable views

Option 1 column visibility changes automatically replace the current history entry's
`view` parameter, without navigating, fetching, cancelling a pending search,
resetting drafts/editors or moving focus/scroll. The address bar is the shareable
link; reload and browser back/forward restore visibility. The URL uses the same
encoding as the artefact grid, but search only retains visibility overrides
relative to defaults. Legacy sort, global-search, column-filter and facet values
in old `view` links are ignored. All search columns are visible by default.
Column widths, order and pinning remain valid session-local presentation state,
but are deliberately not shared. There are no named views or session autosave on
search. Malformed or oversized values fall back to defaults; unknown/inapplicable
columns are ignored. Removing `view` restores default visibility, not stale
state from the previous URL. Restoring a link does not rewrite it.

**Search** (including reapplying an unchanged query) preserves column visibility
while purging blocks and restarting at row 0. **Reset table view** removes only
the shared visibility customization, retaining the backend query and drafts
without a fetch. Returning to default visibility removes the parameter
automatically. **Clear all** resets the backend query/drafts and table view, then
loads the unfiltered recent range.

The route adapter reads SvelteKit 3's `page.shallow.url` as well as `page.url`.
View writes use the non-navigating `replaceState` API, preserving `page.state`.
The shared shell exempts native history transitions differing only in `view`
from its loading lock/overlay: even a transient `inert` during native Forward
would blur an editor. It captures the visible source URL in `beforeNavigate`
and identifies that particular navigation by its public `complete` promise.
Search-condition changes, other routes and non-history navigation still block;
superseding navigation cannot inherit the exemption. This does not rely on
`navigating.shallow`, which the installed runtime does not expose.
The history adapter
rejects outgoing writes from a different URL or while a route navigation is in
progress. SvGrid provides no column-visibility callback, so visibility is
checked every 250ms while the grid is mounted (with cleanup).

## Deliberately deferred

All 18 filter groups, including Issues, Reviewers, Execution Metadata and Latest
Execution, are active Search editors on each route, backed by all 19 canonical
URL/API keys. Their presentation is route-specific: wide-table headers, Option
3's SidePanel or Option 4's editable chips. The dedicated Search-page backend response includes the compact row values
and association summaries those columns need; this is a Search-specific API
contract and does not change the existing `/v1/test-results` response. Saved
views and export remain deferred. Issue details, attachment-rule management,
issue-scoped results and rerun controls are available on the separate Issues pages.
Search mutation workflows remain deliberately unwired for this read-only
experiment.

## Issues workflows

`/wip/issues` has URL-backed source/status/family/project filters, explicit search
submission, preserved hide/show state and Load more. Open + unknown is the
default status selection; explicit empty status means all. Single-project
selection uses the API, while multi-project OR and multi-source selection operate
over loaded pages. Project options come from a separate bounded stream without a
project restriction but with the other filters. Discovery/search is partial until
the user loads further discovery pages, not an exhaustive server facet. Selected
projects remain available even when absent from those pages.

Add issue uses supported external tracker URLs and the server's get-or-create
contract. It reports already added only when the returned safe ID was known in
the loaded main stream before refresh; unseen/facet-only IDs get neutral success
wording. Both streams refresh independently after confirmed success.

`/wip/issues/{id}` displays identity and complete attachment-rule criteria.
Native disclosures retain inspection and one-shot `?attachmentRule={id}` focus
and attention through loading, direct links and history. View filters navigates
to Search with the issue and complete rule predicate. Enable/disable uses the
confirmed response; deletion requires a Pragma confirmation modal with pending
locks, inline errors and focus return (or the rules heading if the rule disappears).
There is no issue edit/delete, rule-criteria editor or result attach/detach UI.

The issue result grid uses the same compact block-loading infrastructure and
lazy Details modal as Search, with Architecture immediately before Environment,
configured View Run execution/result links and bounded cache. It can browse
beyond 100 matches; the exact server count is retained when later blocks return
`count: null`. This is offset browsing, not a server snapshot. Optional Family,
Artefact, Environment, Test Case and inclusive From/Until bounds use explicit
draft/Apply. Dates count as one optional group; pending suggestion input is not
a selected condition. Clearing drafts needs Apply and never clears the immutable
issue scope. Query/session/issue invalidation closes obsolete Details.

Auto-rerun is independent of result availability. It checks a fresh session and
keeps the last confirmed value while pending or after rejection. A same-session
confirmed update reconciles on return to that issue; stale owners cannot update
another issue/session. Bulk create/delete rerun review freezes the applied query
and covers all effective server matches, including unloaded rows, not draft or
cache-only selection. Creation defaults to latest executions and excluding
archived artefacts; deletion does not silently inherit those defaults. Priority,
preview counts, large-operation acknowledgement and eligibility remain part of
review. View matching results opens the exact effective preview/write predicate
in a protected new Search tab; opening it does not mutate or dismiss review.
Session/scope changes invalidate review and ambiguous writes require refresh,
not an automatic retry.

Read access is server-authoritative: issues require `view_issue`; result reads
require `view_test`. Add requires `change_issue`, rule writes require
`change_attachment_rule`, auto-rerun requires both `change_issue` and
`change_auto_rerun`, and query bulk reruns require both `change_rerun` and
`change_rerun_bulk`. Ordinary grants can suffice, not just administrator status.
401/403 and failed session verification are recoverable local states, never
permission grants. Global Search remains read-only even when opened from review.

The controls use installed Pragma 0.33 components and theme tokens. Badge is a
numeric indicator, so textual issue/rule states use read-only Chip. Native rule
disclosures and the UTC datetime picker are retained where no corresponding
installed editable component exists. Narrow tests establish control/modal
reachability, not full-page mobile support: the pre-existing expanded shell
sidebar clips content at 390px.

## Local checks

From `frontend/sveltekit`, install locked dependencies with `npm ci`, then run
`npm run check`, `npm run build`, `npm test`, and `npm run lint`.
The [test guide](tests/README.md) lists the opt-in mocked Issues and Search
browser runners and their evidence boundaries. No browser dependency belongs
in the project just to run these checks.
`tests/test-results-search.test.js` tests the backend/OpenAPI and URL contracts,
initial unfiltered recent-page defaults, races, auth revalidation, the absence of
Search-page selection/mutation controls, and actual mounted Pragma controls and
the Option 1 SvGrid rendering/interactions in Happy DOM. Mounted regressions cover the absence
of Add filter/condition chips, the active filters opening from their column
headers, all-canonical-filter URL acceptance and block serialization, per-column
anchored menus and their external filter adapter, drafts versus applied queries, strict operator mapping
and visible unsupported-filter alerts, menu dismissal and focus,
URL restoration, long values and clear. Infinite-search regressions cover exact
range-to-API mapping, repeated column filters, count/end-of-data, bounded
cache, cancellation/stale replies, filter/history resets, legacy pagination URL
normalization, and the absence of old page controls plus disabled grid-local
sort/filter/global search. Additional regressions cover shareable column
visibility, replace-only history writes, restoring/removing invalid views,
repeated parameters, drafts/menu/focus and grid identity across view-only
changes, pending result/auth requests, retained visibility through Search, and
resetting the table independently. Shared filter utilities retain metadata and
ID wire-contract tests for other workflows. Mounted issue/reviewer/metadata
regressions cover suggestions, label hydration, lazy metadata loading, exact ID
modes, local suggestion failures/retries and literal metadata pairs. Mounted
read-only regressions verify unfiltered initial/clear behavior, no row selection
or mutation controls, and working Run/Details behavior. Happy DOM lacks native
popover and dialog/Invoker Commands support, so a test-only adapter models native toggle/light-dismiss
events, including ignored focus attempts before native opening completes.
Details regressions additionally cover actual column order, ID mapping for loaded
rows, all/empty sections, multiple internal issue links,
execution timestamps/timezones, Unicode metadata, full malicious/large literal
logs, missing configured families, preserved column-menu drafts, view-only
preservation, invalidation, recycled-cell focus fallback and
unmount. The adapter is test-only, not an application dialog fallback or proof
of real native focus containment.
Mounted tests also verify viewport constraints with supplied geometry; real
scrollbar reachability still needs browser QA. These tests use mocked API
responses, not a live backend integration or
a real-browser visual test; real top-layer layout, keyboard traversal, and
desktop/800px screenshots require separate browser QA.

`tests/search-options-pagination.test.js` covers the actual Options 2, 2.5, 3
and 4 routes and their mounted Pragma tables, including the dedicated Option 2.5
filter row, Created-first compact order, UTC-only date editors with raw legacy-value preservation, page and
page-size URL/API mapping, page-window edges, numeric jumps, and direct
out-of-range canonicalization. The mocked Chromium runner adds native picker,
real table scrolling and visible-pager evidence.

### Native history browser regression

The live history/Details runners below emit post-login screenshots and
record-specific links. Review that behavior against your privacy policy before
running them. Under a no-live-payload/no-live-screenshot policy, do not run them
unchanged: use bounded sanitized SAML + API-read smoke and the separate mocked
current-branch UI regressions instead. See the [test guide](tests/README.md#conditional-real-sso-and-read-only-api-checks).

`tests/search-view-history.browser.js` is an opt-in integration check against a
running Vite frontend and real seeded API/SSO stack, not part of the mocked
`npm test` suite. It uses SvelteKit's actual public `replaceState`/`pushState`
APIs, first verifying Test Case filter URL reload/Back/Forward restoration and
then native view-only Back/Forward twice each. The view-only traversal asserts
focus never leaves the Test Case header-menu input, no transient `inert` or
loading overlay appears, the same grid/menu/input and unapplied exact-value draft
survive, page state survives, the table view restores, and view-only traversal
sends zero API requests. No requests are intercepted or mocked.

Use the native LXD stack for the local API and test IdP (`just lxd-dev-up` from
the repository root); separate LXD containers provide independent development
instances without alternate service-port configuration. Use the container's
reported address rather than `localhost` when accessing it from the host.
The history runner additionally requires a Vite development frontend so the
public SvelteKit modules are available; set `SEARCH_URL` to that frontend's
`/wip/test-results` URL and allow its origin in the local API's CORS settings.
The static frontend built by `lxd-dev-up` alone cannot serve those Vite modules.

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
storage state. Do not enable traces, HARs or login screenshots. Stop only your
own native stack with `just lxd-dev-down`; its database data is retained. Do not
reload a database snapshot or modify a shared database just to run these checks.

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

It checks 1920px, 1440px, 960px and 800px in light/dark: newest-first loaded row
IDs, disabled local sort/filter/search controls, Run targets, native keyboard opening/Tab containment/Escape/backdrop/X/Close and
focus restoration, viewport/body scroll/footer reachability, no row-selection or
mutation controls, one Details API request on open and none on close, no URL
changes on open/close, confirmed and
unconfirmed drafts, and native view-only Back/Forward modal/focus retention.
Shared assertions in `tests/details-layout.browser.js` verify actual scalar row
geometry, a full-width real metadata table with complete sorted literal text,
top-aligned cells, wrapping, no descendant scroll containers, and header/footer
visibility. Available real rows exercise populated/empty logs and issue hrefs
without navigating to the issue destination, which has separate browser coverage. The JSON report
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

### Search-grid mock integration and metadata cost

`tests/search-grid-mocked.browser.js` runs the real SvelteKit route and SvGrid
inside Chromium with intercepted API responses. It is opt-in and separate from
`npm test`; Playwright Core and Chromium are supplied externally, with no project
dependency or lockfile changes. For example:

```sh
PLAYWRIGHT_MODULE=/tmp/opencode/svelte-search-qa-tools/node_modules/playwright-core/index.mjs \
CHROMIUM_EXECUTABLE=/tmp/opencode/playwright-browsers/chromium-1248/chrome-linux64/chrome \
QA_ARTIFACT_DIR=/tmp/opencode/search-grid-mocked \
PW_TEST_SCREENSHOT_NO_FONTS_READY=1 \
node tests/search-grid-mocked.browser.js
```

The synthetic response has 50 newest-first-shaped rows, one issue and one
reviewer summary per row, and 41 metadata categories × 2 values per row (4,100
pairs total). Categories and values contain long Unicode text (maximum 180 and
182 Unicode code points); stage includes an explicit empty value. The test verifies
the final ordered 23 columns and 18
header filter groups; row values and the full-value dialogs for issues, reviewers
and metadata (82 entries in the metadata dialog); keyboard opening, Escape/focus
return, centered/responsive modal bounds, design-system shell, internal scrolling
and a narrow-viewport keyboard-opened far-right menu; horizontal and
vertical grid scrolling at 800 × 600; and Details fetch-on-open/no-fetch-on-close.
The test also covers draft-versus-applied behavior, Back/Forward/reload, Clear
all and the absence of local sorting/filtering controls. It deliberately returns
the same rows for every condition, so the still-visible first row after a
`FAILED` search demonstrates that the browser did not apply a client-only filter.

One final Chromium run in this workspace (report at
`/tmp/opencode/search-grid-mocked-chunk5-final/report.json`) measured:

| Measurement                                           |                                                                                                                                                      Result |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------: |
| Search response body                                  |                                                                                                      4,086,148 UTF-8 JSON bytes, uncompressed identity body |
| Actual `Response.json()` parse/decode                 |                                                                                                                                                     62.8 ms |
| Standalone `JSON.parse`                               |                                                            10 measured runs after 2 warm-ups: 1.45 ms mean, 1.1 ms reported middle sample, 0.9–5.3 ms range |
| First row readiness after `Response.json()` completed |                                                                                                        2,189.6 ms; 37 rows rendered at the initial viewport |
| Sampled row heights                                   |                                                                                                                     20 rows; min/median/max 30/30/30 CSS px |
| Grid at 800 × 600                                     | 496 px client width / 3,386 px scroll width; horizontal scroll reached 2,890 px, vertical client/scroll heights 341/1,529 px and reached scrollTop 1,188 px |

These are synthetic-fixture observations, not production budgets. Response bytes
exclude compression and network transfer; parse timing is one browser run; row
height confirms clipping rather than showing the full metadata at once. The render
interval includes Vite/Svelte/SvGrid update and Playwright observation delay, and
is not a controlled benchmark. Scroll timings are instant programmatic scrolling
plus animation-frame settling, not wheel/trackpad throughput. This mock establishes
component behavior only: it is not evidence of backend query/response integration,
live authentication, seeded data, compressed wire size, or production performance.
The live Details/history scripts above are separate and must be run against a
healthy seeded stack when live-stack evidence is required.
