---
description: Implement the "Export" button on the test-results view, producing a portable single-file HTML report generated entirely client-side.
mode: agent
---

<!--
SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
SPDX-License-Identifier: Apache-2.0
-->

# TODO: Portable test report export

> **Status: not started. Blocked on prerequisites below.**
> This is a design spec, not a description of existing code. Nothing here is implemented yet.

## Prerequisite

[frontend/sveltekit/src/routes/test-results/+page.svelte](../../frontend/sveltekit/src/routes/test-results/+page.svelte)
is currently a "Coming soon" stub. Do not start this work until that view exists and owns a
real filter state, because the export is defined as "serialise what the user is currently
looking at". If the view is still a stub when this prompt is invoked, stop and say so.

## Goal

An **Export** button on the test-results view that downloads a single self-contained `.html`
file. It must open offline from the filesystem with no server, no network, and no CLI tooling
— suitable for attaching to a PR, an email, or a Jira ticket.

## Non-goals

- **Not Allure.** Allure 3's generator (`@allurereport/core`, `@allurereport/plugin-awesome`)
  is Node-only: it globs a results directory off disk via `node:fs` and writes a site to an
  output directory. Shimming that over `memfs` in the browser was evaluated and rejected as a
  maintenance liability against a non-public API surface. We produce our own HTML.
- **No backend endpoint and no Celery task.** The whole pipeline runs in the browser. The
  frontend is a static SPA (`@sveltejs/adapter-static`, `ssr = false`), and it stays that way.
- **No new query parameters on `/v1/test-results`.** The existing filter set is sufficient.
  Adding filters to this endpoint needs separate justification — see the API design rules in
  [copilot-instructions.md](../copilot-instructions.md).

## Design constraint: stay generic

Per the Core Design Principle in [CLAUDE.md](../../CLAUDE.md), the exporter must not branch on
artefact family. `family` is carried through as an opaque string field and grouped on like any
other. There must be no `if family === "snap"` anywhere in this feature, and no reachback into
Snapcraft, Launchpad, or any other family-specific external API.

## Pipeline

Three stages, all client-side:

1. **Collect** — page through `GET /v1/test-results` using the active filters from the view.
2. **Transform** — reduce the response into a compact report payload (see below).
3. **Emit** — interpolate the payload into an HTML template, `Blob` → `createObjectURL` →
   synthetic `<a download>` click → `revokeObjectURL`.

### Stage 1: collect

Use the existing `api<T>()` wrapper in
[frontend/sveltekit/src/lib/api/client.ts](../../frontend/sveltekit/src/lib/api/client.ts).
It already sets `credentials: "include"` and `X-CSRF-Token`, so auth needs no new work. Note
its failure contract: it returns `T | null` and pushes the message to `errorStore` rather than
throwing. A partial export is worse than a failed one, so **a `null` on any page must abort
the whole export** and surface a distinct error — do not emit a file built from partial pages.

`limit` is capped at 1000 by the backend (default 50), so a broad filter means many sequential
requests. Requirements:

- Request `limit=1000` per page.
- Drive a determinate progress indicator from the `count` field in the first response.
- Provide a cancel control that aborts in-flight work (`AbortSignal`).
- Refuse to start, or require explicit confirmation, when the unfiltered result count is
  above the threshold settled in Q2.

### Stage 2: transform

Response shape is `TestResultSearchResponseWithContext`: `{ count, limit, offset, test_results[] }`,
where each element carries `test_result`, `test_execution` (with nested `environment`),
`artefact`, and `artefact_build`. Field-level detail lives in
[backend/schemata/openapi.json](../../backend/schemata/openapi.json) — read it rather than
trusting this summary, and consider generating types from it instead of hand-writing them
(there are currently no `TestResult` / `TestExecution` / `Environment` types in
[frontend/sveltekit/src/lib/types/index.ts](../../frontend/sveltekit/src/lib/types/index.ts),
only `Artefact`).

Deduplicate aggressively. Artefact and environment records repeat across every row; the
payload should intern them into lookup tables keyed by id and have rows reference them. This
is the single largest lever on output file size.

**There is no duration field on `test_result`.** Do not build timing, trend, or timeline
views — there is no data behind them. This is what forced `start == stop` in the earlier
standalone Allure script and made its duration charts meaningless.

### Stage 3: emit

Two viable template strategies. Pick per Q1.

- **Vanilla v1** — hand-written HTML template with inline vanilla JS for sort and filter.
  A summary panel plus a sortable table is roughly 300 lines. Ships soonest, no build changes.
- **Single-file Svelte bundle** — a second Vite entry built with `vite-plugin-singlefile` so
  CSS and JS inline into one `.html`, imported into the app via Vite's `?raw` suffix and used
  as a template string. Real components, compiled once, carried as a string. More build
  machinery; worth it only once there are test-results components worth reusing.

## Security requirements

These are hard requirements, not style preferences. `io_log` and `comment` contain arbitrary
test output, which means **the exported file renders attacker-influenced content**. A test that
prints `</script><script>…` compromises every machine the report is opened on, and the file is
designed to be emailed around.

- Embed the payload as `<script type="application/json">`, with `<` escaped as `\u003c` so the
  tag cannot be broken out of. Parse it at load.
- Render every value through `textContent` or equivalent. **Never `innerHTML`**, never
  string-concatenate log or comment text into markup.
- Do not auto-linkify `ci_link` / `c3_link` into `href` without scheme validation — allow
  `http:` and `https:` only, reject `javascript:` and `data:`.
- Add a restrictive `<meta http-equiv="Content-Security-Policy">` to the exported document.
  `default-src 'none'` with whatever minimum the inline script needs; no remote origins, since
  the file must work offline anyway.

## Open questions

Settle these before writing code. Each one changes the shape of the implementation.

**Q1 — Template strategy.** Vanilla v1 now, or go straight to the single-file Svelte bundle?
Depends on how much component reuse the finished test-results view actually offers. Default to
vanilla v1 unless reuse is clearly substantial.

**Q2 — Size budget and log policy.** `io_log` is effectively the entire weight of the output.
Inlining every log across a few thousand results produces a file in the tens of megabytes that
will stall the browser during generation and may not open comfortably afterwards. Options, not
mutually exclusive: inline logs for failed results only; truncate to a head/tail window with a
stated cap; let the user choose; show a size estimate before committing. **What is the hard
ceiling, and what happens on breach — refuse, warn, or silently degrade?**

**Q3 — Export scope.** Current filters only, or an explicit scope picker in the dialog? Current
filters is the stated intent and the simpler contract, but it makes the artifact's contents
non-obvious from the file alone. Mitigation either way: render the active filter set into the
report header so the file is self-describing. Decide whether that is sufficient.

**Q4 — Provenance.** What identifies the export? Proposal: generation timestamp, the API origin
it was pulled from, serialised filter set, total result count, and a schema version for the
embedded payload. The schema version matters if we ever want older exports to stay readable.

**Q5 — Attachment handling.** Logs inline as text today. If per-result attachments ever grow
beyond text, a single HTML file stops being the right container and this needs revisiting —
possibly a `.zip` alternative alongside the HTML. Confirm text-only is a safe assumption.

**Q6 — Overlap with existing tooling.** There is a
[backend/scripts/fetch_test_results_report.py](../../backend/scripts/fetch_test_results_report.py)
in-tree, plus a standalone (not in-tree) Allure exporter script. Check whether either is
superseded by this feature and should be retired rather than left to rot alongside it.

**Q7 — Memory ceiling.** Collect-then-transform holds the entire result set in memory before
emitting. At the Q2 ceiling, confirm this is acceptable on a normal laptop, or restructure to
stream page-by-page into the payload.

## Acceptance criteria

- [ ] Export button on the test-results view, disabled while a run is in flight.
- [ ] Determinate progress indicator and a working cancel.
- [ ] Any failed page aborts the export; no partial files are ever emitted.
- [ ] Output is a single `.html` that opens offline from `file://` with no network requests.
- [ ] Report is self-describing: filters, timestamp, source origin, result count.
- [ ] XSS test: a result whose `io_log` contains `</script><script>alert(1)</script>` and whose
      `ci_link` is `javascript:alert(1)` is rendered inert in the exported file. **This is a
      required test, not a manual check.**
- [ ] No branching on artefact family anywhere in the feature.
- [ ] `npm run check` and `npm run lint` clean in `frontend/sveltekit`.
- [ ] Copyright headers on new files (enforced by `check_copyright_notices.yml`); frontend
      sources are `GPL-3.0-only` — match the header style in `src/lib/api/client.ts`.
