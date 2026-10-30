<!--
Copyright 2023 Canonical Ltd.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3, as
published by the Free Software Foundation.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
SPDX-License-Identifier: GPL-3.0-only
-->

# Test Observer Frontend

The frontend of Test Observer is a web application developed in Flutter.

## SvelteKit UI rewrite (development)

For development of the SvelteKit UI rewrite, run the commands below from the repository root (where the `justfile` is located):

```bash
export TEST_OBSERVER_API_URL=https://test-observer-api-staging.canonical.com
export TEST_OBSERVER_API_KEY=<read-only-key>

just          # list available recipes
just up       # start the frontend container
just down     # stop the frontend container
```

### SvelteKit test result search

The read-only `/test-results` page uses per-column filters in the result headers,
with explicit Search to apply drafts, remote suggestions where supported, and a
shareable local table view. Results have no row selection, bulk actions, or
mutation workflows.
The grid loads compact result rows; the Details action fetches the selected
result on demand and opens one reusable Pragma modal with execution metadata,
attached issues and literal IO logs. Closing the modal does not fetch again.
Issue links open the internal SvelteKit issue-detail route described below.

See the canonical [SvelteKit search guide](sveltekit/SEARCH.md) for all field
labels, editors, URL contracts and repair rules, query and table-view resets,
layout/native-history guarantees, and the optional real API/SSO browser check.

For local SvelteKit checks, run `npm run check`, `npm run build`, `npm test` and
`npm run lint` from `frontend/sveltekit` (dependencies: `npm ci`). Automated
model/URL/API and mounted UI tests do not stand in for live backend/browser QA.

### SvelteKit issues

`/wip/issues` lists linked external issues with search, source/status/family/project
filters, fifty-row pages, and a Pragma Add issue dialog. Status defaults to open
and unknown; clearing the status selection explicitly includes all statuses.
Search is submitted explicitly. Hiding filters preserves their values and URL
state. The searchable project picker supports keyboard selection and removal.
One selected project is sent to the API; multiple projects use local OR over
loaded pages (as does multi-source selection). Use Load more to continue browsing.
Project-option discovery is a separate, bounded, project-unrestricted stream
matching the other filters. It remains partial until explicitly paged further;
searching options does not search the whole server. Selected values stay visible.

`/wip/issues/[issueId]` displays the issue and its attachment rules, including
complete criteria, View filters links back to Search, enable/disable, and
confirmed deletion. `?attachmentRule=<positive ID>` expands and focuses a rule
after loading, including on history navigation. Issue-scoped compact results
support server-backed browsing beyond 100 matches, on-demand literal Details,
and View Run links to the configured family/execution/result. Architecture stays
immediately before Environment. Optional Family, Artefact, Environment, Test Case
and inclusive date filters have separate drafts and Apply; the issue is always
pinned. Counts describe server matches, not cached rows; offset pages are not a
server snapshot.

Auto-rerun keeps the last confirmed setting while saving or after failure. Bulk
create/delete rerun review freezes the applied issue query, not draft filters or
cached IDs, and previews all effective server matches. Creation defaults to
latest executions and excluding archived artefacts; deletion has its own scope.
View matching results opens the effective predicate in read-only Search in a
new tab. Pending/ambiguous writes are not silently replayed. Add issue reports
already added only for IDs known in the loaded main list; otherwise success uses
neutral wording, not a global duplicate/newness claim.

The API is authoritative for access. Reading issues requires `view_issue` and
result access requires `view_test`. Add issue requires `change_issue`; rule
enable/disable/delete requires `change_attachment_rule`; auto-rerun requires
`change_issue` and `change_auto_rerun` after a fresh session check. Query-based
bulk reruns require `change_rerun` and `change_rerun_bulk`. Ordinary team grants
can suffice; these are not administrator-only features. Denials are reported
without inventing grants. There is no issue title/status editing, issue deletion,
rule-criteria editing, result attach/detach or global Search mutation UI.

The opt-in `npm run test:issues-browser` and `npm run test:issues-detail-browser`
checks run Chromium against temporary local Vite servers with mocked API
responses; they do not mutate a live database. Supply externally installed
Playwright Core via `PLAYWRIGHT_MODULE` and Chromium via `CHROMIUM_EXECUTABLE`,
as for the [Search browser checks](sveltekit/SEARCH.md#local-checks). No Playwright
project dependency is required. See the [SvelteKit test guide](sveltekit/tests/README.md)
for the results, auto-rerun, bulk/inspection, rule-target, filter and Add runners,
their boundaries, and the full check commands. Mocked UI tests are not live API
or SSO evidence. Read-only live checks use an existing local stack and the root
[README](../README.md)'s Local authentication instructions; never duplicate
credentials in guides or artifacts or write shared records for QA. The existing
expanded sidebar clips whole-page content at 390px; narrow modal/control coverage
does not establish full mobile support.

## Setup

Install flutter snap:

```bash
$ sudo snap install flutter --classic
```

Check the version of flutter installed:

```bash
$ flutter --version
```

Change flutter to the version used in production (note that the below directory doesn't get created until you run some flutter command like `flutter --version`):

```bash
$ cd ~/snap/flutter/common/flutter
$ git checkout 3.29.3
```

Then install dependencies via:

```bash
$ flutter pub get
```

And finally, make sure to install chrome.

## Run

This project uses code generation, so you must first generate the required code:

```bash
$ dart run build_runner build
```

Then you can launch the fontend on chrome:

```bash
# You can use --experimental-hot-reload with Flutter versions >= 3.32.0
$ flutter run -d chrome # --experimental-hot-reload
```

## Test

### Static analysis

```bash
$ flutter analyze
```

### Unit tests

```bash
$ flutter test --platform chrome # requires chrome
```

### Integration tests

To run integration tests you first need to install chromedriver.

Then you can run it via:

```bash
$ chromedriver --port=4444
```

While it's running you can launch a single integration test via:

```bash
$ flutter drive --driver=test_driver/integration_test.dart --target=integration_test/<integration-test-file> -d chrome
```

You can even run it in headless mode via:

```bash
$ flutter drive --driver=test_driver/integration_test.dart --target=integration_test/<integration-test-file> -d web-server
```

And you can run all integration tests via the bash script:

```bash
$ ./run_integration_tests.sh
```

## Benchmark

There are some benchmarks written under the `/benchmarks` directory. You can run these using:

```bash
$ dart run_benchmark_tests.dart
```

This will open up chrome and run the benchmarks infront of you.

You can also pass `--headless` to run the above command in headless mode.

Either way the command will produce json files with results under the `/benchmarks` directory.

## Connect to backend

By default the Test Observer frontend will use `http://localhost:30000/` to communicate with the backend. To use a different address you can modify `window.testObserverAPIBaseURI` attribute in `web/index.html`.
