<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# Basic test result search

`/test-results` is a read-only search page. Its applied query lives in the URL,
so direct links, reloads, and browser back/forward restore the search. Editing a
control does not change the results until **Apply filters** is submitted. Applying
starts again at the first page. **Clear all** returns to the initial prompt;
empty and pagination-only URLs never request unfiltered test results.

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

Unknown URL keys, unknown/unavailable families, invalid result statuses, and
invalid pagination block the request with a visible notice, rather than silently
broadening the applied query. Apply replaces unsupported URL keys with the
supported draft controls; Clear removes everything. `limit` defaults to 50 and
accepts integers from 1 to the API's default maximum of 1000; `offset` is a
nonnegative safe integer. A deployment may configure a lower API maximum; such a
request displays the retryable API error.

Pagination replaces pages; it never appends or mixes datasets. Server order is
newest result first (created time, then ID). The count is the backend's total,
while SvGrid filtering and sorting are **local to the loaded page** and do not
change that count. Grid state is reset on query/page changes and is not persisted.
The API does not provide snapshot pagination, so concurrent ingestion/deletion
can shift offset boundaries; refreshing or reapplying starts a fresh search.
View Run uses the configured family route and the SvelteKit
`testExecutionId`/`testResultId` deep links (including the deployment base path).
If a result's family has no configured route, the grid shows Run unavailable.

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
and SvGrid rendering/interactions in Happy DOM. It uses mocked API responses,
not a live backend integration or a real-browser visual test.
