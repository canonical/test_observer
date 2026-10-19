<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Basic test result search

`/test-results` is a read-only search page. Its applied query lives in the URL,
so direct links, reloads, and browser back/forward restore the search.

## Conditions and applying a search

The compact condition bar starts with **+ Add filter** and **Search**. Add filter
opens an anchored, searchable picker containing only the eight supported fields
below. A field already represented by a chip is omitted from the picker; select
its chip to edit it instead. Families and result statuses use multi-checkbox
editors; the other six fields accept comma-separated exact values. Configured
family friendly names are displayed, while their API names are submitted.

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
Enter submits an editor's values or activates a focused button. Backend query or
pagination URL changes close and reset transient editors; table-view-only URL
changes preserve the confirmed drafts, open editor and keyboard focus.

**Search** applies the entire confirmed chip draft, updates the URL, and starts
again at the first page. Chip configuration and removal never fetch. **Changes
not applied** marks a draft that differs from the URL, and existing results are
labelled as belonging to the previous query. Pagination is disabled until the
draft is applied or restored to the applied values, so it cannot accidentally
apply or discard edits. Unconfirmed editor contents are never included by Search.

**Clear all** immediately removes the URL query, chips and results, returning to
the initial prompt. Removing the last chip instead remains a draft until Search
is selected; Search then clears the applied query and results. Neither action
requests unfiltered results. Empty and pagination-only URLs never request
unfiltered test results.

## URL and result contract

Supported query keys:

- `families` (API names from the layout's configured families)
- `test_result_statuses` (`PASSED`, `FAILED`, `SKIPPED`)
- `artefacts` (artefact names)
- `artefact_versions`
- `artefact_tracks`
- `environments` (environment names)
- `test_plans` (test plan names)
- `test_cases` (test case names)

All eight use the backend's **exact-match** semantics, not substring search.
Values are ORed within one key, and keys are ANDed together. URL values can be
comma-separated, repeated, or both, matching Flutter's list parsing. Whitespace
is trimmed and empty entries removed. Commas delimit values and cannot be used
as literal characters within a value in this basic UI. API calls use repeated
parameters. For example, `?artefacts=one,two&test_result_statuses=FAILED` requests
`artefacts=one&artefacts=two&test_result_statuses=FAILED` from `/v1/test-results`.

The additional `view` parameter carries only the local grid presentation (see
below). It is never sent to the API and cannot make an empty/pagination-only
search request unfiltered results. Other unknown URL keys, unknown/unavailable families, invalid result statuses, and
invalid pagination block the request with a visible notice, rather than silently
broadening the applied query. Search replaces unsupported URL keys with the
supported confirmed draft; Clear all removes everything. `limit` defaults to 50 and
accepts integers from 1 to the API's default maximum of 1000; `offset` is a
nonnegative safe integer. A deployment may configure a lower API maximum; such a
request displays the retryable API error.

Pagination replaces pages; it never appends or mixes datasets. Server order is
newest result first (created time, then ID). The count is the backend's total,
while SvGrid filtering and sorting are **local to the loaded page** and do not
change that count.
The API does not provide snapshot pagination, so concurrent ingestion/deletion
can shift offset boundaries; refreshing or reapplying starts a fresh search.
View Run uses the configured family route and the SvelteKit
`testExecutionId`/`testResultId` deep links (including the deployment base path).
If a result's family has no configured route, the grid shows Run unavailable.

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

Archived/latest/rerun boolean selectors; date bounds; `artefact_stages`;
`template_ids`; execution statuses and metadata; issues and reviewers; a result
details modal; saved views and export. All bulk operations, attachment rules,
issue attach/detach, rerun creation/deletion, and other mutation workflows are
excluded.

## Local checks

From `frontend/sveltekit`, install locked dependencies with `npm ci`, then run
`npm run check`, `npm run build`, `npm test`, and `npm run lint`.
`tests/test-results-search.test.js` tests the backend/OpenAPI and URL contracts,
request defaults, races, auth revalidation, and actual mounted Pragma controls
and SvGrid rendering/interactions in Happy DOM. Mounted regressions cover the
searchable eight-field picker, duplicate/empty prevention, all editor types,
confirmed drafts versus applied queries, cancellation/dismissal and focus,
URL restoration, long values, clear and pagination. Additional regressions cover
shareable sort/global/column/facet/visibility state, replace-only history writes,
restoring/removing invalid views, repeated parameters, drafts/editor/focus and
grid identity across view-only changes, pending result/auth requests, retained
views through Search/pagination, and resetting the table independently. Happy DOM lacks native
popover support, so a test-only adapter models native toggle/light-dismiss
events, including ignored focus attempts before native opening completes.
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
the editor, no transient `inert` appears, the grid/editor/popover and confirmed
and unconfirmed drafts survive, page state survives, the table view restores,
and traversal sends zero API requests. No requests are intercepted or mocked.

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
public SvelteKit modules. It writes only an assertion report and search-page
screenshot under `/tmp/opencode` by default, never credentials, cookies or
storage state. Start/stop only your own stack and preserve Docker volumes.
