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

The test-results search currently provides compact editors for eight fields:
families, result statuses, artefact names, versions, tracks, environments, test
plans and test cases. `sveltekit/src/lib/testResultsFilters.ts` defines the typed
backend contracts and shared empty/active/clone/equality operations independently
of that editor list. Other supported URL filters are stages, archived artefacts,
rerun requested, latest execution, issues, reviewers, execution metadata,
from/until timestamps and template IDs. Their editors are not implemented yet.
The page identifies active URL-only filters and preserves all URL-only conditions
when editing the eight current fields, including malformed/unknown conditions
that must continue to block requests. Correct the URL or use Clear all to remove
these conditions; an unrelated edit never silently removes them.

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
preserved. Invalid encoding or UTF-8 blocks the search locally.

Date bounds apply inclusively to `TestResult.created_at`. Timestamps must be valid
Gregorian ISO instants (`YYYY-MM-DDTHH:mm:ss[.fraction]Z` or an explicit `±HH:MM`
offset), with no rollover or assumed local timezone. Bounds may be one-sided;
from must not exceed until, comparing offsets and fractional precision without
JavaScript millisecond truncation. Bounds must be exactly representable at the
backend's microsecond precision: nonzero fractional digits beyond six are
rejected; additional trailing zeros are allowed. Input timestamps are retained,
never rounded or silently normalized. Dates alone count as meaningful frontend
filters, matching Flutter.
`view` remains presentation-only: it is never an API filter and cannot enable an
unfiltered fetch. Unknown filter names and invalid conditions visibly block
requests. Hydrated issue/reviewer labels are not part of filter identity.

For local SvelteKit checks, run `npm run check`, `npm run build`, `npm test` and
`npm run lint` from `frontend/sveltekit` (dependencies: `npm ci`). The search tests
include isolated model/URL/API contracts and the actual mounted eight-field UI;
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
