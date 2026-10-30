<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->

# SvelteKit checks and browser regressions

Run from `frontend/sveltekit`, after the documented locked `npm ci` setup:

```sh
npm run check
npm test
npm run lint
npm run build
```

`npm test` selects `tests/*.test.js` using Node's test runner. It includes model,
URL/API-contract, store and Happy DOM mounted-component tests. The repository
does not assign finer machine-readable per-case type labels. Six existing
intentionally skipped tests must be reported as skips, not passes. Happy DOM's
test-only native dialog/popover adapter is not proof of browser top-layer focus
or layout. For focused iteration, select the relevant files or Node name pattern;
the full suite remains the integrated acceptance check. JUnit output needs
reporter flags **before** file paths, for example:

```sh
node --test --test-reporter=junit \
  --test-reporter-destination=/tmp/opencode/frontend-tests.xml tests/*.test.js
```

Keep command wall time distinct from summed case execution time (files may run
in parallel). Procedural browser scripts have no internal timed case report;
do not inflate assertion/matrix counts into test-case totals.

## Opt-in mocked Chromium checks

These runners start and close their own temporary Vite server and actual
Chromium. API calls, including mutation QA, are intercepted; no live account,
database or tracker writes are needed. Supply externally installed tooling, not
a new project dependency or lockfile change:

```sh
export PLAYWRIGHT_MODULE=/path/to/playwright-core/index.mjs
export CHROMIUM_EXECUTABLE=/path/to/chromium
export QA_ARTIFACT_DIR=/tmp/opencode/issues-qa
# Alternatively use PLAYWRIGHT_BROWSERS_PATH with an existing browser install.
npm run test:issues-browser
npm run test:issues-detail-browser
```

| Command                                               | Coverage boundary                                                                                                                                                                                                                     |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm run test:issues-browser`                         | Issues list/search/status/paging/Add smoke                                                                                                                                                                                            |
| `npm run test:issues-detail-browser`                  | Rule criteria/View filters, confirmed enable/disable, held responses, permission failures, native delete Modal light/dark/desktop/narrow keyboard, pending locks and focus fallback                                                   |
| `node --test tests/issues-filters.browser.js`         | List URL/history/disclosure, searchable project selection, partial discovery, independent streams, focus-intent races                                                                                                                 |
| `node --test tests/issues-focus.browser.js`           | Actual Tab/Space/Enter continuity for source/status/family/Search; held result/discovery paging and retry, surviving invokers/current-region fallbacks, no-steal and superseding/query/session/lifetime ownership                     |
| `node --test tests/add-issue.browser.js`              | Add validation, confirmed IDs/loaded-only feedback, pending/cancel/session/navigation, native modal geometry                                                                                                                          |
| `node tests/issue-results.browser.js`                 | 625 server-shaped matches, bounded paging/cache, pinned draft/Apply/date filters, lazy literal Details, stale bodies/A/B/history, access failures and actual configured artefact execution/result navigation from both View Run links |
| `node --test tests/issue-auto-rerun.browser.js`       | Fresh permissions, confirmed state, pending/failure/session and GET/PATCH races                                                                                                                                                       |
| `node --test tests/issue-reruns.browser.js`           | Frozen all-match create/delete scope, effective preview/write/inspection predicates, protected real Search popup, options, permissions, held/ambiguous writes and focus                                                               |
| `node --test tests/attachment-rule-target.browser.js` | One-shot rule attention through delayed loading, history, issue switching and rule actions                                                                                                                                            |
| `node tests/search-grid-mocked.browser.js`            | Read-only global Search, all columns/editors, Architecture/Environment order, drafts/history, full-value dialogs, Details and scrolling                                                                                               |
| `node tests/search-result-details-fixture.browser.js` | Actual Details component with long literal logs/metadata, light/dark viewport/zoom matrix and single-body scrolling; no API/SSO                                                                                                       |

For Node-based browser runners, the same JUnit flags may precede the file path.
Reports/screenshots go outside the repository. Use a distinct artifact directory
per invocation to retain failed attempts and reruns. Never weaken prior checks to
make an integrated run pass. Family-loading and artefact deep-link behavior also
has model/mounted coverage in the normal Node suite; real navigation is exercised
by the issue-results runner rather than asserting href strings alone.

The integrated evidence uses synthetic data and mocked permissions/writes, not
live backend integration. Desktop and narrow modal/control checks do not imply
full 390px mobile support: the pre-existing expanded sidebar clips the page.
Chromium is not a cross-browser or assistive-technology certification.

## Conditional real SSO and read-only API checks

See [SEARCH.md](../SEARCH.md#native-history-browser-regression) for the existing
live history and Details runners. `node tests/search-read-only.browser.js` is
also **live-only**, requires privately supplied test SSO credentials and an
existing `SEARCH_URL`, and does not start a mocked Vite/API fixture. It checks
Search selection/mutation absence, Details and a narrow header pointer target.
Do not count running it without those prerequisites as a mocked regression pass.
These live runners require the appropriate existing Vite/API
origins and data; mock passes do not satisfy those prerequisites. An existing
published frontend may be an older build. Real SAML followed by cookie-context
GETs can establish authenticated API-read smoke without proving current-branch
UI integration. Record missing permissions/data/SSO separately as live gaps.

Existing live history/Details runners can save post-login search/result
screenshots and record-specific links. If your QA privacy policy forbids live
payloads, screenshots or identifiers, **do not run those unchanged runners**;
use a bounded sanitized API-read smoke instead. They are not a substitute for
the current-branch mocked UI checks and their artifact behavior must be reviewed
before use.

Use the root [README](../../../README.md)'s Local authentication instructions or
privately supplied credential environment. Never copy credentials into docs,
commands, saved scripts or artifacts. Use an ephemeral browser context; do not
save storage state, cookies, tokens, personal payloads, live/login screenshots,
traces, HARs or raw authentication errors. Report only sanitized stages, HTTP
statuses, authenticated/schema booleans and counts. Permit only actual auth
endpoint POSTs and abort live API data writes. Issue/rule/result/rerun mutation
QA must remain mocked. Do not repair access by granting permissions, reseeding,
restoring shared data, changing services/configuration or creating tracker records.
