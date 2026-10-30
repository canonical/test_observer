<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import {
    Button,
    Checkbox,
    Link,
    Modal,
    TextInput,
  } from "@canonical/svelte-ds-app-launchpad";
  import { silentApi } from "$lib/api/client";
  import { userStore } from "$lib/stores/user.svelte";
  import {
    executionIds,
    rerunPlan,
    type BulkTarget,
    type Capability,
  } from "$lib/testResultsBulk";
  import {
    refreshBulkPermissions,
    type BulkPermissions,
  } from "$lib/testResultsBulkPermissions";
  import {
    ambiguousMutationError,
    issueRequestError,
  } from "$lib/testResultsIssues";
  import {
    previewRerunCount,
    rerunIsBulk,
    rerunSearchUrl,
    type RerunOperation,
  } from "$lib/testResultsReruns";

  let {
    scope,
    reviewKey,
    loginUrl,
    searchDestination,
    onbusy,
    onreview,
    oncomplete,
    onrefresh,
    onclose,
  }: {
    scope: (ownSubmission?: boolean) => Capability<BulkTarget>;
    reviewKey: string;
    loginUrl: string;
    /** Explicit opt-in; unrelated consumers must not infer Search from login. */
    searchDestination?: string;
    onbusy: (busy: boolean) => void;
    onreview: (open: boolean) => void;
    oncomplete: (key: string, message: string) => Promise<void>;
    onrefresh: () => Promise<void>;
    onclose: () => void;
  } = $props();
  const id = $props.id();
  let live = true;
  let open = $state(false);
  let busy = $state(false);
  let target = $state.raw<BulkTarget | null>(null);
  let operation = $state<RerunOperation>("create");
  let onlyLatest = $state(true);
  let excludeArchived = $state(true);
  let exact = $state(false);
  let priority = $state("0");
  let acknowledged = $state(false);
  let permissions = $state.raw<BulkPermissions | null>(null);
  let checking = $state(false);
  let authController: AbortController | undefined;
  let countController: AbortController | undefined;
  let countGeneration = 0;
  let lastPreview = "";
  let preview = $state.raw<{
    key: string;
    count: number | null;
    error: string;
  }>({ key: "", count: null, error: "" });
  let message = $state("");
  let terminal = $state(false);
  let invalidated = $state(false);
  let openedKey = $state("");
  let reviewedUser = $state<number | null>(null);
  let reviewedSession = $state(0);
  let reviewGeneration = 0;
  const currentUserId = $derived(userStore.current?.id ?? null);
  const plan = $derived(
    target
      ? rerunPlan(target, operation, {
          onlyLatestExecutions: target.kind === "query" ? onlyLatest : false,
          excludeArchivedArtefacts:
            target.kind === "query" ? excludeArchived : false,
          explicitMode: exact ? "exact" : "guarded",
          ...(operation === "create"
            ? { priority: /^-?\d+$/.test(priority) ? Number(priority) : NaN }
            : {}),
        })
      : null,
  );
  const ids = $derived(
    target?.kind === "explicit" ? executionIds(target) : null,
  );
  const permission = $derived(
    checking
      ? { ok: false as const, reason: "Checking permissions…" }
      : (permissions?.check("rerun", target ? rerunIsBulk(target) : true) ?? {
          ok: false as const,
          reason: "Refresh permissions before submitting.",
        }),
  );
  const previewKey = $derived(
    plan?.ok && "test_results_filters" in plan.value.payload
      ? JSON.stringify(plan.value.payload.test_results_filters)
      : "",
  );
  const count = $derived(
    target?.kind === "explicit"
      ? target.resultIds.length
      : preview.key === previewKey
        ? preview.count
        : null,
  );
  const canSubmit = $derived(
    open &&
      !busy &&
      !checking &&
      !invalidated &&
      !terminal &&
      plan?.ok &&
      permission.ok &&
      count !== null &&
      count > 0 &&
      (count <= 50 || acknowledged),
  );
  const matchingResultsUrl = $derived(
    open &&
      !busy &&
      !checking &&
      !invalidated &&
      !terminal &&
      permission.ok &&
      plan?.ok &&
      target?.kind === "query" &&
      preview.key === previewKey &&
      count !== null &&
      !preview.error &&
      searchDestination &&
      plan.value.payload.test_results_filters
      ? rerunSearchUrl(
          plan.value.payload.test_results_filters,
          searchDestination,
        )
      : null,
  );

  function inspectMatches(event: MouseEvent) {
    // Recheck synchronously too: a previously rendered link cannot outlive its
    // scope/session, even if an external change precedes Svelte's next flush.
    if (!matchingResultsUrl || !currentScope()) event.preventDefault();
  }

  // Revocation is durable: restoring a selection or logging in as the same user
  // cannot revive a review observed to have changed while an await was pending.
  $effect.pre(() => {
    const user = currentUserId;
    const session = userStore.sessionVersion;
    const fresh = scope(true);
    if (
      open &&
      (openedKey !== reviewKey ||
        user !== reviewedUser ||
        session !== reviewedSession ||
        !fresh.ok ||
        JSON.stringify(fresh.value) !== JSON.stringify(target))
    ) {
      invalidated = true;
      acknowledged = false;
    }
  });
  $effect(() => {
    const active = open && !invalidated && !terminal;
    const key = previewKey;
    const user = currentUserId;
    // Priority and independent options are review changes even when their
    // resulting filters happen to stay identical to an applied constraint.
    const signature = JSON.stringify([
      active,
      key,
      user,
      priority,
      onlyLatest,
      excludeArchived,
      exact,
    ]);
    untrack(() => {
      if (signature === lastPreview) return;
      lastPreview = signature;
      countController?.abort();
      const generation = ++countGeneration;
      acknowledged = false;
      preview = { key, count: null, error: "" };
      if (!active || !key || !target || target.kind !== "query" || !plan?.ok)
        return;
      const filters = plan.value.payload.test_results_filters;
      if (!filters) return;
      const controller = new AbortController();
      countController = controller;
      void (async () => {
        try {
          const count = await previewRerunCount(filters, controller.signal);
          if (
            !live ||
            controller.signal.aborted ||
            generation !== countGeneration ||
            !currentScope() ||
            user !== userStore.current?.id
          )
            return;
          preview = { key, count, error: "" };
          acknowledged = false;
        } catch (cause) {
          const error = await issueRequestError(cause);
          if (
            !live ||
            controller.signal.aborted ||
            generation !== countGeneration ||
            !currentScope()
          )
            return;
          preview = {
            key,
            count: null,
            error: `Count preview failed. ${error}`,
          };
        }
      })();
    });
  });

  function currentScope() {
    if (!live || !open || invalidated) return false;
    const fresh = scope(true);
    if (
      openedKey !== reviewKey ||
      reviewedUser !== (userStore.current?.id ?? null) ||
      reviewedSession !== userStore.sessionVersion ||
      !fresh.ok ||
      JSON.stringify(fresh.value) !== JSON.stringify(target)
    ) {
      invalidated = true;
      return false;
    }
    return true;
  }
  async function refreshPermissions() {
    authController?.abort();
    const controller = new AbortController();
    authController = controller;
    checking = true;
    permissions = null;
    const generation = reviewGeneration;
    const result = await refreshBulkPermissions(fetch, controller.signal);
    if (
      !live ||
      controller.signal.aborted ||
      generation !== reviewGeneration ||
      !currentScope()
    )
      return;
    permissions = result;
    checking = false;
  }
  export async function start(action: RerunOperation) {
    if (open || busy) return;
    const fresh = scope();
    if (!fresh.ok) return;
    target = fresh.value;
    operation = action;
    onlyLatest = action === "create";
    excludeArchived = action === "create";
    exact = false;
    lastPreview = "";
    priority = "0";
    acknowledged = false;
    preview = { key: "", count: null, error: "" };
    openedKey = reviewKey;
    reviewedUser = userStore.current?.id ?? null;
    reviewedSession = userStore.sessionVersion;
    ++reviewGeneration;
    invalidated = false;
    terminal = false;
    message = "";
    open = true;
    onreview(true);
    await refreshPermissions();
  }
  function close() {
    if (busy) return;
    open = false;
    ++reviewGeneration;
    authController?.abort();
    countController?.abort();
    ++countGeneration;
    onreview(false);
    onclose();
  }
  async function submit() {
    if (!canSubmit || busy || !target || !plan?.ok || !currentScope()) return;
    // The entire effective plan, scope and acknowledgment are frozen BEFORE
    // reauthorization; no mutable controls are read after awaiting /me.
    const submission = plan.value;
    const action = operation;
    const key = openedKey;
    const bulk = rerunIsBulk(target);
    const generation = reviewGeneration;
    busy = true;
    onbusy(true);
    message = "";
    let sent = false;
    try {
      await refreshPermissions();
      if (!currentScope()) return;
      const gate = permissions?.check("rerun", bulk);
      if (!gate?.ok) {
        message =
          gate && !gate.ok
            ? gate.reason
            : "Authorization is unknown. Start a new review.";
        terminal = true;
        return;
      }
      sent = true;
      await silentApi(
        `test-executions/reruns${action === "create" ? "?silent=true" : ""}`,
        {
          method: action === "create" ? "POST" : "DELETE",
          body: JSON.stringify(submission.payload),
        },
      );
      if (!live) return;
      if (generation !== reviewGeneration || !currentScope()) return;
      open = false;
      onreview(false);
      // Release navigation/busy before the parent's result refresh unmounts us.
      busy = false;
      onbusy(false);
      await oncomplete(
        key,
        `${action === "create" ? "Create" : "Delete"} rerun request completed. Refreshing current results and rerun state. The API does not report a changed count; requests are grouped and may be unchanged.`,
      );
    } catch (cause) {
      const detail = await issueRequestError(cause);
      // Parsing an HTTP error body is asynchronous too. An obsolete issue or
      // session must not receive the old request's message or completion.
      if (generation !== reviewGeneration || !currentScope()) return;
      terminal = true;
      message =
        sent && ambiguousMutationError(cause)
          ? `Outcome unknown. The server may have completed the request. No automatic retry or same-review resubmission will be made. Refresh results and inspect rerun state before opening a new review. ${detail}`
          : `${detail} Refresh results or permissions, then close and open a new review before submitting again.`;
    } finally {
      busy = false;
      if (live) onbusy(false);
    }
  }
  onDestroy(() => {
    live = false;
    authController?.abort();
    countController?.abort();
    ++countGeneration;
    onbusy(false);
    onreview(false);
  });
</script>

{#if open}
  <Modal
    class="bulk-rerun-review"
    bind:open
    closeOnOutsideClick={false}
    aria-labelledby={`${id}-title`}
    oncancel={(event) => {
      if (busy) event.preventDefault();
    }}
    onkeydown={(event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        close();
      }
    }}
    onclose={(event) => {
      if (!event.currentTarget.open) close();
    }}
  >
    <Modal.Content class="bulk-rerun-content">
      <Modal.Content.Header>
        <h2 id={`${id}-title`}>
          {operation === "create" ? "Create" : "Delete"} Rerun Requests
        </h2>
        <Button
          type="button"
          density="dense"
          aria-label="Close rerun review"
          disabled={busy}
          onclick={close}>Close</Button
        >
      </Modal.Content.Header>
      <Modal.Content.Body class="bulk-rerun-body">
        <p>
          Rerun requests operate on whole build / environment / test plan
          groups, not individual test results. Multiple executions can belong to
          the same group, so the number of requests may be smaller.
        </p>
        {#if target?.kind === "explicit"}
          <p>
            <strong
              >{target.resultIds.length} selected test results → {ids?.ok
                ? ids.value.length
                : "unknown"} unique executions</strong
            >, including selections on other pages. Actual request groups may be
            fewer.
          </p>
          <p>Result IDs: {target.resultIds.join(", ")}</p>
          {#if ids?.ok}<p>
              Execution IDs: {ids.value.join(", ")}
            </p>{:else if ids}<p role="alert">{ids.reason}</p>{/if}
          <p>
            The server cannot combine exact execution IDs with latest, archive
            or existing-request eligibility guards. To apply those guards, use
            an all-matches query instead.
          </p>
          <label class="option"
            ><Checkbox
              bind:checked={exact}
              onchange={() => (acknowledged = false)}
              disabled={busy || invalidated || terminal || !ids?.ok}
            />Use these exact execution groups</label
          >
          <p>
            This opt-in sends execution IDs only, with no filters or eligibility
            guards. It includes older executions and archived artefacts. {operation ===
            "create"
              ? "Creation may update the priority of existing requests in these groups, not just create missing requests."
              : "Deletion removes requests for these whole groups, including groups identified by older executions."}
          </p>
        {:else if target?.kind === "query"}
          <h3>Frozen applied query</h3>
          <dl>
            {#each Object.entries(target.filters) as [name, value] (name)}<dt>
                {name}
              </dt>
              <dd>{JSON.stringify(value)}</dd>{/each}
          </dl>
          <label class="option"
            ><Checkbox
              bind:checked={onlyLatest}
              onchange={() => (acknowledged = false)}
              disabled={busy || invalidated || terminal}
            />Only latest test executions</label
          >
          <label class="option"
            ><Checkbox
              bind:checked={excludeArchived}
              onchange={() => (acknowledged = false)}
              disabled={busy || invalidated || terminal}
            />Exclude archived artefacts</label
          >
          <p>
            These options intersect the applied query; unchecking them preserves
            its constraints. {operation === "create"
              ? "Only results without a requested rerun are eligible."
              : "Only results with a requested rerun are eligible."} Contradictory
            conditions never override the applied query.
          </p>
          {#if plan?.ok}<h3>Effective result conditions</h3>
            <dl>
              {#each Object.entries(plan.value.payload.test_results_filters ?? {}) as [name, value] (name)}<dt
                >
                  {name}
                </dt>
                <dd>{JSON.stringify(value)}</dd>{/each}
            </dl>{/if}
          {#if preview.error}<p role="alert">
              {preview.error}
            </p>{:else if plan?.ok && count === null && !terminal && !invalidated}<p
              role="status"
            >
              Counting matching test results…
            </p>{:else if count !== null}<p role="status">
              Matches {count} test results; rerun requests are grouped, so the count
              may differ.
              {#if matchingResultsUrl}
                <Link
                  href={matchingResultsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onclick={inspectMatches}
                  onauxclick={inspectMatches}
                  >View matching results (opens in a new tab)</Link
                >
              {/if}
            </p>{/if}
        {/if}
        <p>
          This review excludes local grid filters, view and pagination. Counts
          are previews, not snapshots or changed counts; the server evaluates
          query conditions when submitted.
        </p>
        {#if operation === "create"}
          <label class="priority"
            >Priority<TextInput
              type="text"
              inputmode="numeric"
              value={priority}
              oninput={(event) => {
                priority = event.currentTarget.value;
                acknowledged = false;
              }}
              disabled={busy || invalidated || terminal}
            /></label
          >
          <p>
            Higher priority requests are listed first; this is not a scheduling
            guarantee. Use an integer from -1000000 to 1000000.
          </p>
        {/if}
        {#if plan && !plan.ok}<p role="alert">{plan.reason}</p>{/if}
        {#if !permission.ok}<p role={checking ? "status" : "alert"}>
            {permission.reason}
          </p>{/if}
        {#if !userStore.current && !checking}<Link href={loginUrl}>Log in</Link
          >{/if}
        {#if !busy && !invalidated && !terminal}<Button
            type="button"
            density="dense"
            disabled={checking}
            onclick={refreshPermissions}>Refresh permissions</Button
          >{/if}
        {#if count !== null && count > 50}<label class="option acknowledgment"
            ><Checkbox
              bind:checked={acknowledged}
              disabled={busy || invalidated || terminal}
            />I have reviewed the scope of {count} test results and want to {operation}
            rerun requests for their groups.</label
          >{/if}
        {#if invalidated}<p role="alert">
            The selection, applied query or session changed. Close this review
            and open rerun actions again. Nothing further will be submitted from
            this review. If a request was already sent, it may still complete;
            refresh results to inspect its outcome.
          </p>{/if}
        {#if message}<p role="alert">{message}</p>{/if}
        {#if busy}<p role="status">
            Submitting… Closing is disabled while the request is in flight.
            Leaving the page cannot undo a dispatched request.
          </p>{/if}
      </Modal.Content.Body>
      <Modal.Content.Footer>
        <Button
          type="button"
          severity="brand"
          disabled={!canSubmit}
          onclick={submit}
          >{busy
            ? "Submitting…"
            : operation === "create"
              ? "Create rerun requests"
              : "Delete rerun requests"}</Button
        >
        {#if terminal || invalidated || preview.error}<Button
            type="button"
            disabled={busy}
            onclick={async () => {
              close();
              await onrefresh();
            }}>Close and refresh results</Button
          >{/if}
        <Button type="button" disabled={busy} onclick={close}>Cancel</Button>
      </Modal.Content.Footer>
    </Modal.Content>
  </Modal>
{/if}

<style>
  :global(html:has(dialog.bulk-rerun-review[open])) {
    overflow: hidden;
  }
  :global(dialog.ds.modal.bulk-rerun-review) {
    width: min(48rem, calc(100vw - 2rem));
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }
  :global(.bulk-rerun-content) {
    display: flex;
    flex-direction: column;
    max-height: calc(100dvh - 2rem);
    min-height: 0;
    box-sizing: border-box;
  }
  :global(.bulk-rerun-body) {
    min-height: 0;
    overflow: auto;
    overflow-wrap: anywhere;
    overscroll-behavior: contain;
  }
  :global(.bulk-rerun-content .dialog-content-header),
  :global(.bulk-rerun-content .dialog-content-footer) {
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  :global(.bulk-rerun-content .dialog-content-header) {
    justify-content: space-between;
    gap: var(--lp-dimension-spacing-inline-s);
  }
  h2 {
    font-size: 1.25rem;
    margin: 0;
  }
  h3 {
    font-size: 1rem;
  }
  dt {
    font-weight: 550;
  }
  dd {
    margin: 0 0 var(--lp-dimension-spacing-block-xs);
  }
  .option {
    display: flex;
    align-items: start;
    gap: var(--lp-dimension-spacing-inline-s);
    margin-block: var(--lp-dimension-spacing-block-m);
  }
  .priority {
    display: flex;
    flex-direction: column;
    gap: var(--lp-dimension-spacing-block-xs);
    max-width: 15rem;
  }
</style>
