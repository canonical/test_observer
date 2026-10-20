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

### SvelteKit search filter foundation

The test-results search provides compact chip editors for all 18 typed fields:
Family, Status, Issues, Reviewers, Artefact, Artefact Version, Artefact Stage,
Artefact Track, Archived, Rerun Requested, Execution Version, Environment, Test
Case, Test Plan, Metadata, From, Until, and Template ID. Labels match Flutter;
Template ID is an approved extra whose filter was not originally rendered by
Flutter. Unused fields stay hidden in the searchable Add filter picker. Edits are
confirmed locally; only explicit Search applies the complete draft to the URL and
fetches results. Table view changes remain independent.

`sveltekit/src/lib/testResultsFilters.ts` defines typed backend contracts and
shared empty/active/clone/equality operations. `FilterEditor.svelte` dispatches to
small kind-specific editors rather than a schema engine. Manual-only lists trim
and deduplicate comma-separated values; stages use the configured union across
families, including explicit `(none)` and retained unconfigured selections.
Nullable booleans use a single choice, including active false. Issues and
Reviewers have mutually exclusive specific IDs / has any / has none modes.
Detail labels hydrate through a bounded in-memory session cache (invalidated on
session/profile/permission or API-root changes). Lookup failures stay local and
never drop conditions, block other editors or create global error toasts.

Artefact, Environment, Test Plan and Test Case offer searchable name suggestions
scoped to the **confirmed draft Family chips**, not the applied results query.
Issues and Reviewers offer rich issue/project/title/source and
name/handle/email suggestions, without a family restriction (matching Flutter).
These use the existing `GET /v1/artefacts/search`, `/v1/environments`,
`/v1/test-plans`, `/v1/test-cases`, `/v1/issues` and `/v1/users` contracts.
Remote lookups start after two trimmed characters and a 250 ms debounce, with
limits of 50 names or 10 IDs. Query replies are not cached. Requests are aborted
and late bodies/errors ignored when the query, family, field, editor or session
context changes. Lookup failures, including authentication/permission errors,
remain local with retry and a manual exact-value path.

Typing a lookup query never adds a condition. Choose a result or use **Add exact
value / Add exact IDs**; clear pending text before saving. Selected values remain
visible and individually removable even when absent from suggestions. Tab/Enter
activate ordinary result buttons; Arrow Down/Up moves between the input and
results. Enter in the query input does not submit the editor, and Escape discards
the editor. No separate suggestions overlay is created. The comma-list link
contract cannot represent literal commas or surrounding whitespace in names:
such remote options are visibly unavailable, and exact-name additions reject
commas rather than silently splitting them. Existing comma/repeated links still
restore. Artefact Version, Artefact Track and the extra Template ID retain manual
exact lists: there is no complete lookup endpoint for them (test-case search
matches case names, not template IDs).

Metadata lazily loads `GET /v1/execution-metadata` when its editor opens. Native
category/value datalists filter this known map locally (up to 50 matches), with
values grouped by the exact category. The map is cached only in memory for five
minutes in the current API/session/profile/permission context; reopening can
reuse it, while typing never refetches it. Cancelled replies cannot fill the
cache. Manual literal pairs remain available, including Unicode, punctuation and
spaces; users never need to enter wire encoding. Suggestion selection and chip
confirmation never fetch test results: only explicit Search applies the draft.

Unrelated edits preserve malformed/unknown raw URL constraints, including invalid
pagination; they continue to block requests instead of silently broadening a
search. Known malformed fields have explicit replacement/removal controls. Use
the URL or Clear all for unsupported names. Editor cancellation, Escape and
outside dismissal never save an edit.

Page links accept repeated or comma-separated lists; API requests emit repeated
keys. Boolean filters are `true`/`false` (absence is unrestricted), and an empty
`artefact_stages=` explicitly matches the empty stage, not an unrestricted search.
Issues and reviewers accept positive safe integer IDs, `any`, or `none`, without
mixing modes. Legacy `assignee_ids` is used only when `reviewer_ids` is absent;
explicit canonical presence wins, as in Flutter. Empty/invalid canonical IDs
block instead of falling back to the alias (the backend falls back only for an
empty canonical list). Requests always emit only canonical `reviewer_ids`.

Execution metadata is structured as categories with alternative values: AND
across categories, OR within a category. On the wire each pair is
`Base64(UTF8(category)):Base64(UTF8(value))`, repeated for each value, using standard
padded Base64, not the table view's base64url. Decoded punctuation and Unicode are
preserved. The editor uses separate literal category/value inputs, not wire
encoding or delimiter parsing. Categories and values each require 1–200 Unicode
characters. Invalid encoding, UTF-8 or lengths block the search locally.

Date bounds apply inclusively to `TestResult.created_at`. Timestamps must be valid
Gregorian ISO instants (`YYYY-MM-DDTHH:mm:ss[.fraction]Z` or an explicit `±HH:MM`
offset), with no rollover or assumed local timezone. Bounds may be one-sided;
from must not exceed until, comparing offsets and fractional precision without
JavaScript millisecond truncation. Bounds must be exactly representable at the
backend's microsecond precision: nonzero fractional digits beyond six are
rejected; additional trailing zeros are allowed. Input timestamps are retained,
never rounded or silently normalized. The From/Until editors offer a clearly UTC
date/time picker and an exact timestamp input; changing the picker deliberately
selects second precision, while unchanged saves retain the original instant
text. Dates alone count as meaningful frontend filters, matching Flutter.
`view` remains presentation-only: it is never an API filter and cannot enable an
unfiltered fetch. Unknown filter names and invalid conditions visibly block
requests. Hydrated issue/reviewer labels are not part of filter identity.

For local SvelteKit checks, run `npm run check`, `npm run build`, `npm test` and
`npm run lint` from `frontend/sveltekit` (dependencies: `npm ci`). The search tests
include isolated model/URL/API contracts and the actual mounted 18-field UI,
including actual suggestion request contracts, debounce, keyboard/multi-select,
draft family context, local failures, cancellation, late-body and session races;
they do not stand in for live backend/browser testing.

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
