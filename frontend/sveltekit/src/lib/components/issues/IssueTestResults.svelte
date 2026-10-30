<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, tick, untrack } from "svelte";
  import { Button, Link, Spinner } from "@canonical/svelte-ds-app-launchpad";
  import { RestartIcon, DeleteIcon } from "@canonical/svelte-icons";
  import { FetchError, silentApi } from "$lib/api/client";
  import { getApiRoot } from "$lib/config";
  import {
    issueResultsQuery,
    issueResultGroupCount,
    issueRerunTarget,
    type IssueResultFilters,
  } from "$lib/issueTestResults";
  import { TestResultsSearchStore } from "$lib/stores/test-results-search.svelte";
  import { userStore } from "$lib/stores/user.svelte";
  import type { Family } from "$lib/types";
  import type { SearchResultDetails as DetailsData } from "$lib/testResultsSearch";
  import SearchResultDetails from "$lib/components/search/SearchResultDetails.svelte";
  import IssueResultsGrid from "./IssueResultsGrid.svelte";
  import IssueResultFiltersEditor from "./IssueResultFilters.svelte";
  import BulkRerunReview from "$lib/components/search/BulkRerunReview.svelte";

  let {
    issueId,
    families,
    base,
    onbusy,
  }: {
    issueId: number;
    families: Family[];
    base: string;
    onbusy?: (busy: boolean) => void;
  } = $props();
  const store = new TestResultsSearchStore();
  let applied = $state.raw<{
    issueId: number;
    filters: IssueResultFilters;
  } | null>(null);
  // Even an unkeyed caller changing issue IDs cannot carry A's filters into B.
  const query = $derived(
    issueResultsQuery(
      issueId,
      applied?.issueId === issueId ? applied.filters : undefined,
    ),
  );
  $effect.pre(() => {
    if (applied && applied.issueId !== issueId) applied = null;
  });

  function applyFilters(filters: IssueResultFilters) {
    const candidate = issueResultsQuery(issueId, filters);
    if (!candidate.problems.length) applied = { issueId, filters };
  }
  // Same display/session context convention as the shared lookup caches. This
  // is invalidation, not a permission grant; the backend remains authoritative.
  const sessionScope = $derived(
    `${getApiRoot()}:${JSON.stringify(userStore.current)}`,
  );
  const dataset = $derived({ query, sessionScope, families, base });
  let reviewRevision = $state(0);
  let review: BulkRerunReview;
  let rerunBusy = $state(false);
  let reviewing = $state(false);
  let completion = $state("");
  let reviewInvoker: {
    dataset: typeof dataset;
    trigger: HTMLButtonElement;
  } | null = null;
  function startRerun(
    operation: "create" | "delete",
    trigger: HTMLButtonElement,
  ) {
    reviewInvoker = { dataset, trigger };
    void review.start(operation);
  }
  async function restoreRerunFocus() {
    const previous = reviewInvoker;
    // The trigger is disabled while reviewing/loading. Restore only after the
    // dialog has gone and the current dataset's controls are enabled again.
    await tick();
    if (
      live &&
      !reviewing &&
      previous?.dataset === dataset &&
      previous.trigger.isConnected &&
      !previous.trigger.disabled
    )
      previous.trigger.focus({ preventScroll: true });
  }
  // An observed A/B/A query or session transition cannot revive an old review.
  $effect.pre(() => {
    void dataset;
    void userStore.sessionVersion;
    untrack(() => {
      ++reviewRevision;
      completion = "";
    });
  });
  const reviewKey = $derived(`${reviewRevision}:${userStore.sessionVersion}`);
  function rerunScope(ownSubmission = false) {
    return issueRerunTarget(issueId, query, store.state?.rowCount ?? null, {
      available: ready,
      loading: !ready,
      moving: false,
      accessError: !!store.accessError || !!store.error,
      // Draft editing is deliberately independent of the frozen applied query.
      unapplied: false,
      mutating: rerunBusy && !ownSubmission,
    });
  }
  const rerunCapability = $derived(rerunScope());
  async function refreshResults() {
    if (!live) return;
    discardDetails();
    await store.search(query, families, base);
  }
  let modelDataset = $state.raw<typeof dataset | null>(null);
  const ready = $derived(
    modelDataset === dataset &&
      store.modelQuery === query &&
      store.responseQuery === query &&
      !!store.controller &&
      !store.error &&
      !store.accessError,
  );
  let section: HTMLElement;
  let live = true;
  let generation = 0;
  let request: AbortController | null = null;
  let selection = $state.raw<{
    id: number;
    dataset: typeof dataset;
    authorizationVersion: number;
    trigger: HTMLButtonElement;
  } | null>(null);
  let result = $state<DetailsData | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  function discardDetails() {
    ++generation;
    request?.abort();
    request = null;
    selection = null;
    result = null;
    loading = false;
    error = null;
  }

  $effect.pre(() => {
    const current = dataset;
    const version = userStore.authorizationVersion;
    if (
      selection &&
      (selection.dataset !== current ||
        selection.authorizationVersion !== version ||
        !store.controller ||
        store.error ||
        store.accessError)
    )
      untrack(discardDetails);
  });

  $effect(() => {
    const current = dataset;
    untrack(() => {
      modelDataset = current;
      void store.search(current.query, current.families, current.base);
    });
    return () => {
      discardDetails();
      store.cancel();
    };
  });

  onDestroy(() => {
    live = false;
    discardDetails();
  });

  async function loadDetails(id: number, trigger: HTMLButtonElement) {
    request?.abort();
    const token = ++generation;
    const owner = dataset;
    const version = userStore.authorizationVersion;
    const controller = new AbortController();
    request = controller;
    selection = { id, dataset: owner, authorizationVersion: version, trigger };
    result = null;
    loading = true;
    error = null;
    const current = () =>
      live &&
      !controller.signal.aborted &&
      generation === token &&
      dataset === owner &&
      userStore.authorizationVersion === version &&
      selection?.id === id &&
      ready;
    try {
      const details = await silentApi<DetailsData>(
        `test-results/search-page/${id}`,
        { signal: controller.signal },
      );
      if (!current()) return;
      if (!details || details.test_result.id !== id)
        throw new Error("The details endpoint returned a different result.");
      // The selected row may since have been evicted from the bounded cache.
      // Its ID/owner snapshot, not cache occupancy, owns this on-demand dialog.
      result = details;
    } catch (failure) {
      if (!current()) return;
      error =
        failure instanceof FetchError && failure.status === 401
          ? "Your session could not access these details. Log in and try again."
          : failure instanceof FetchError && failure.status === 403
            ? "You don't have permission to view these result details."
            : "Could not load result details. Check your connection and try again.";
    } finally {
      if (current()) {
        loading = false;
        request = null;
      }
    }
  }

  function showDetails(id: number, trigger: HTMLButtonElement) {
    if (
      !live ||
      !ready ||
      !store.controller?.getRows().some((r) => r.id === id)
    )
      return;
    trigger.focus({ preventScroll: true });
    void loadDetails(id, trigger);
  }

  function closeDetails() {
    const previous = selection;
    discardDetails();
    if (!previous || !live || previous.dataset !== dataset || !ready) return;
    const target =
      previous.trigger.isConnected &&
      previous.trigger.dataset.testResultId === String(previous.id)
        ? previous.trigger
        : section.querySelector<HTMLElement>(".issue-results-grid");
    target?.focus({ preventScroll: true });
  }

  function retryDetails() {
    if (selection && ready && selection.dataset === dataset)
      void loadDetails(selection.id, selection.trigger);
  }

  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(typeof location === "undefined" ? `${base}/issues/${issueId}` : location.href)}`,
  );
</script>

<section
  class="issue-test-results"
  aria-labelledby="issue-results-heading"
  aria-busy={store.loading}
  bind:this={section}
>
  <h2 id="issue-results-heading">Test Results</h2>
  <div class="rerun-actions" aria-label="Issue result rerun actions">
    <Button
      type="button"
      aria-haspopup="dialog"
      disabled={!rerunCapability.ok || reviewing}
      onclick={(event) => startRerun("create", event.currentTarget)}
      >{#snippet iconLeft()}<RestartIcon />{/snippet}Create rerun requests</Button
    >
    <Button
      type="button"
      aria-haspopup="dialog"
      disabled={!rerunCapability.ok || reviewing}
      onclick={(event) => startRerun("delete", event.currentTarget)}
      >{#snippet iconLeft()}<DeleteIcon />{/snippet}Delete rerun requests</Button
    >
  </div>
  <p>
    Rerun actions review all server matches for this issue's applied filters,
    including results not loaded in the table. Unapplied drafts are not
    included.
  </p>
  {#if completion}<p role="status">{completion}</p>{/if}
  {#key issueId}
    {@const owner = issueId}
    <IssueResultFiltersEditor
      {issueId}
      {families}
      applied={query.filters}
      onapply={(filters) => {
        if (issueId === owner) applyFilters(filters);
      }}
    />
  {/key}
  {#if query.problems.length}
    <p role="alert">{query.problems.join(" ")}</p>
  {:else if modelDataset !== dataset}
    <div class="loading" role="status"><Spinner /> Loading test results…</div>
  {:else if store.accessError === "requiresLogin"}
    <p role="status">You need to be logged in to view these test results.</p>
    <Link href={loginUrl}>Log in</Link>
    <Button onclick={() => store.retry()}>Retry results</Button>
  {:else if store.accessError || store.error}
    <p role="alert">
      {store.accessError === "forbidden"
        ? "You don't have permission to view these test results. Contact an administrator if this is a mistake."
        : store.accessError === "sessionCheckFailed"
          ? "We couldn't verify your session. Check your connection and try again."
          : store.error}
    </p>
    <Button onclick={() => store.retry()}>Retry results</Button>
  {:else if store.modelQuery === query && store.controller && store.rowModel}
    {#if store.responseQuery === query && store.state?.rowCount !== null && store.state?.rowCount !== undefined}
      <p role="status">
        {store.state.rowCount} matching test results on the server. Scroll to load
        more; newest first. Results may change while browsing.
      </p>
    {/if}
    {#if store.loading}
      <div class="loading" role="status"><Spinner /> Loading test results…</div>
    {/if}
    {#if store.state?.rowCount === 0}
      <p>
        {issueResultGroupCount(query.filters)
          ? "No test results match the applied filters for this issue."
          : "No test results are attached to this issue."}
      </p>
    {:else}
      {#key store.controller}
        <IssueResultsGrid rowModel={store.rowModel} onDetails={showDetails} />
      {/key}
    {/if}
  {:else}
    <div class="loading" role="status"><Spinner /> Loading test results…</div>
  {/if}
</section>

<BulkRerunReview
  bind:this={review}
  scope={rerunScope}
  {reviewKey}
  {loginUrl}
  searchDestination={`${base}/test-results`}
  onbusy={(busy) => {
    rerunBusy = busy;
    onbusy?.(busy);
  }}
  onreview={(open) => (reviewing = open)}
  oncomplete={async (key, message) => {
    if (!live || key !== reviewKey) return;
    completion = message;
    await refreshResults();
    await restoreRerunFocus();
  }}
  onrefresh={async () => {
    await refreshResults();
    await restoreRerunFocus();
  }}
  onclose={() => {
    reviewing = false;
    void restoreRerunFocus();
  }}
/>

<SearchResultDetails
  {result}
  active={selection !== null}
  {loading}
  {error}
  {families}
  {base}
  onclose={closeDetails}
  onretry={retryDetails}
/>

<style>
  .issue-test-results {
    margin-top: var(--lp-dimension-spacing-block-xxl);
    min-width: 0;
    color: var(--lp-color-text-default);
  }
  .loading {
    display: flex;
    gap: var(--lp-dimension-spacing-inline-s);
    align-items: center;
  }
  .rerun-actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--lp-dimension-spacing-inline-s);
  }
</style>
