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

The read-only `/test-results` page has compact chip editors for 18 typed fields,
explicit Search to apply confirmed drafts, remote suggestions where supported,
and a shareable local table view. It also supports ephemeral, ID-based result
selection across backend pages and an explicit query-bound all-matches option
with exclusions; no bulk actions or mutation workflows are enabled.
The Details action opens one reusable Pragma modal from the already-loaded raw
result (no new query), with execution metadata, attached issues and literal IO
logs. Issue links intentionally use the future internal issue-detail route;
that SvelteKit destination currently returns 404 and is not implemented here.

See the canonical [SvelteKit search guide](sveltekit/SEARCH.md) for all field
labels, editors, URL contracts and repair rules, selection scope/reset behavior,
layout/native-history guarantees, and the optional real API/SSO browser check.

For local SvelteKit checks, run `npm run check`, `npm run build`, `npm test` and
`npm run lint` from `frontend/sveltekit` (dependencies: `npm ci`). Automated
model/URL/API and mounted UI tests do not stand in for live backend/browser QA.

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
