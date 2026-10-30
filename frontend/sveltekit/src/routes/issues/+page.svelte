<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { page, navigating } from "$app/state";
  import { beforeNavigate, goto } from "$app/navigation";
  import { onDestroy, tick, untrack } from "svelte";
  import {
    Button,
    Checkbox,
    Chip,
    Link,
    Spinner,
    TextInput,
  } from "@canonical/svelte-ds-app-launchpad";
  import {
    ExternalLinkIcon,
    PlayIcon,
    SearchIcon,
  } from "@canonical/svelte-icons";
  import { resolve } from "$app/paths";
  import { getApiRoot } from "$lib/config";
  import { userStore } from "$lib/stores/user.svelte";
  import { IssueListPages } from "$lib/issueListPages.svelte";
  import { FocusIntent } from "$lib/focusIntent";
  import IssueProjectPicker from "$lib/components/issues/IssueProjectPicker.svelte";
  import AddIssue from "$lib/components/issues/AddIssue.svelte";
  import {
    addedIssueFeedback,
    filterIssueRows,
    issueActiveGroupCount,
    issueFilterKey,
    issueProjectFilters,
    ISSUE_PAGE_SIZE,
    parseIssueFilters,
  } from "$lib/issuePageModel";
  import { familyDisplayName, type Family } from "$lib/types";
  import {
    DEFAULT_ISSUE_STATUSES,
    ISSUE_SOURCES,
    ISSUE_STATUSES,
    type Issue,
    type IssueSource,
    type IssueStatus,
  } from "$lib/types/issues";

  let { data } = $props();
  const pageUrl = $derived(page.shallow?.url ?? page.url);
  const families = $derived(
    (data.artefactFamilies as Family[]).filter((family) => family.api_name),
  );
  const familyOptions = $derived(families.map((family) => family.api_name));
  const filters = $derived(
    parseIssueFilters(
      new URLSearchParams(pageUrl.searchParams.toString()),
      familyOptions,
    ),
  );
  let searchText = $state("");
  let syncedQuery = "";

  let filtersVisible = $state(true);
  const activeGroups = $derived(issueActiveGroupCount(filters));
  // Session context invalidates both read streams; it does not grant access.
  const sessionScope = $derived(
    `${getApiRoot()}:${userStore.sessionVersion}:${JSON.stringify(userStore.current)}`,
  );
  const resultScope = $derived(`${sessionScope}:${issueFilterKey(filters)}`);
  const facetFilters = $derived(issueProjectFilters(filters));
  const facetScope = $derived(
    `${sessionScope}:${issueFilterKey(facetFilters)}`,
  );
  const results = new IssueListPages(() => resultScope);
  const projects = new IssueListPages(() => facetScope);
  const focusIntent = new FocusIntent();
  let issuesPage = $state<HTMLDivElement>();
  let resultsRegion = $state<HTMLElement>();
  let focusOwner: {
    session: string;
    from: string;
    to: string;
    navigation: boolean;
    started: boolean;
    arrived: boolean;
  } | null = null;
  function cancelFocus() {
    focusIntent.cancel();
    focusOwner = null;
  }
  const visibleIssues = $derived(filterIssueRows(results.rows, filters));
  const projectOptions = $derived(
    [
      ...new Set([
        ...filterIssueRows(projects.rows, facetFilters).map(
          (issue) => issue.project,
        ),
        ...filters.projects,
      ]),
    ].sort((a, b) => a.localeCompare(b)),
  );
  const groups = $derived.by(() => {
    const grouped: {
      key: string;
      source: IssueSource;
      project: string;
      issues: Issue[];
    }[] = [];
    for (const issue of visibleIssues) {
      const key = JSON.stringify([issue.source, issue.project]);
      let group = grouped.find((candidate) => candidate.key === key);
      if (!group) {
        group = {
          key,
          source: issue.source,
          project: issue.project,
          issues: [],
        };
        grouped.push(group);
      }
      group.issues.push(issue);
    }
    return grouped;
  });

  // Fence writes as soon as navigation starts, not only after page.url updates.
  // Keying the dialog also keeps queued native events on their original owner.
  let addNavigation = $state(0);
  const addContext = $derived(`${resultScope}:${addNavigation}`);
  let addFeedback = $state<{ context: string; message: string } | null>(null);
  beforeNavigate((navigation) => {
    ++addNavigation;
    // Exactly the initiating goto may cross the owner boundary. Any further
    // navigation (including A/B/A or history) cancels that operation's return.
    if (
      focusOwner?.navigation &&
      !focusOwner.started &&
      navigation.to?.url.href === focusOwner.to
    )
      focusOwner.started = true;
    else cancelFocus();
  });

  $effect.pre(() => {
    const session = sessionScope;
    const href = pageUrl.href;
    const visible = filtersVisible;
    untrack(() => {
      const owner = focusOwner;
      if (!owner) return;
      if (
        owner.session !== session ||
        !visible ||
        (href !== owner.to && (owner.arrived || href !== owner.from))
      )
        cancelFocus();
      else if (href === owner.to) owner.arrived = true;
    });
  });

  $effect(() => {
    const query = filters.query;
    untrack(() => {
      if (query !== syncedQuery) {
        syncedQuery = query;
        searchText = query;
      }
    });
  });

  $effect.pre(() => {
    const scope = resultScope;
    untrack(() => void results.reset(filters, scope));
  });

  $effect.pre(() => {
    const scope = facetScope;
    untrack(() => void projects.reset(facetFilters, scope));
  });

  onDestroy(() => {
    cancelFocus();
    results.dispose();
    projects.dispose();
  });

  // Compose rapid changes against the most recent intended URL, not a stale
  // page snapshot while goto is pending. Only the latest navigation can clear it.
  let pendingUrl: URL | null = null;
  let navigationRevision = 0;
  function navigate(next: URL, source: HTMLElement | null = null) {
    pendingUrl = next;
    const revision = ++navigationRevision;
    const owner = {
      session: sessionScope,
      from: pageUrl.href,
      to: next.href,
      navigation: true,
      started: false,
      arrived: false,
    };
    focusOwner = owner;
    const intent = focusIntent.begin(
      source,
      () =>
        focusOwner === owner &&
        owner.session === sessionScope &&
        pageUrl.href === owner.to &&
        !navigating.to &&
        filtersVisible,
    );
    return goto(next, { reset: false })
      .then(async () => {
        await tick();
        intent.restore();
      })
      .finally(() => {
        intent.cancel();
        if (focusOwner === owner) focusOwner = null;
        if (revision === navigationRevision) pendingUrl = null;
      });
  }

  async function readPage(
    stream: IssueListPages,
    action: "more" | "retry",
    source: HTMLButtonElement,
    facet = false,
  ) {
    if (stream.initialLoading || stream.loadingMore) return;
    const owner = {
      session: sessionScope,
      from: pageUrl.href,
      to: pageUrl.href,
      navigation: false,
      started: false,
      arrived: true,
    };
    focusOwner = owner;
    const intent = focusIntent.begin(
      source,
      () =>
        focusOwner === owner &&
        owner.session === sessionScope &&
        pageUrl.href === owner.to &&
        !!issuesPage?.isConnected &&
        !navigating.to &&
        (!facet || filtersVisible),
    );
    try {
      await stream[action]();
      await tick();
      intent.restore(() =>
        facet
          ? issuesPage?.querySelector<HTMLInputElement>("#project-search")
          : resultsRegion,
      );
    } finally {
      intent.cancel();
      if (focusOwner === owner) focusOwner = null;
    }
  }

  function updateFilter(
    name: "source" | "status" | "family" | "project",
    values: string[],
    source: HTMLElement | null = null,
  ) {
    const next = new URL((pendingUrl ?? pageUrl).href);
    next.searchParams.delete(name);
    if (name === "status" && values.length === 0) {
      // An explicit empty value means all statuses; absence means the default
      // open + unknown selection.
      next.searchParams.append(name, "");
    } else {
      for (const value of values) next.searchParams.append(name, value);
    }
    return navigate(next, source);
  }

  function toggleValue(
    value: string,
    checked: boolean,
    name: "source" | "status" | "family" | "project",
    source: HTMLElement | null = null,
  ) {
    const current = parseIssueFilters(
      new URLSearchParams((pendingUrl ?? pageUrl).searchParams.toString()),
      familyOptions,
    );
    const selected =
      name === "source"
        ? current.sources
        : name === "status"
          ? current.statuses
          : name === "family"
            ? current.families
            : current.projects;
    const next = checked
      ? [...selected, value].filter(
          (item, index, all) => all.indexOf(item) === index,
        )
      : selected.filter((item) => item !== value);
    return updateFilter(name, next, source);
  }

  function submitSearch(event: SubmitEvent) {
    event.preventDefault();
    const next = new URL((pendingUrl ?? pageUrl).href);
    const query = searchText.trim();
    if (query) next.searchParams.set("q", query);
    else next.searchParams.delete("q");
    const form = event.currentTarget as HTMLFormElement;
    const active = form.ownerDocument.activeElement;
    void navigate(
      next,
      active instanceof HTMLElement && form.contains(active) ? active : null,
    );
  }

  function issueAdded(id: number) {
    // Same-scope stream resets also supersede an older paging/retry intent.
    cancelFocus();
    // Capture duplicate knowledge before either reset clears its loaded rows.
    // Only the main stream counts, including rows hidden by local OR filters.
    addFeedback = {
      context: addContext,
      message: addedIssueFeedback(id, results.rows),
    };
    // Both independent reads refresh, neither owns the mutation/dialog lock.
    void projects.reset(facetFilters, facetScope);
    void results.reset(filters, resultScope);
  }

  function statusLabel(status: IssueStatus) {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  function issueLinkLabel(issue: Issue) {
    return issue.source === "jira"
      ? `${issue.project}-${issue.key}`
      : `#${issue.key}`;
  }
</script>

<svelte:head>
  <title>Issues — Test Observer</title>
</svelte:head>

<div class="issues-page" bind:this={issuesPage}>
  <header class="page-header">
    <div>
      <h1>Issues</h1>
      <p>Browse external issues linked to test executions.</p>
    </div>
    {#key addContext}
      <AddIssue getContext={() => addContext} onadded={issueAdded} />
    {/key}
  </header>

  <div role="status" aria-live="polite" aria-atomic="true" class="add-feedback">
    {#if addFeedback?.context === addContext}{addFeedback.message}{/if}
  </div>

  <div class="filter-disclosure">
    <Button
      aria-expanded={filtersVisible}
      aria-controls="issue-filters"
      onclick={() => {
        cancelFocus();
        filtersVisible = !filtersVisible;
      }}>{filtersVisible ? "Hide filters" : "Show filters"}</Button
    >
    <span role="status"
      >{activeGroups} active filter {activeGroups === 1
        ? "group"
        : "groups"}</span
    >
  </div>
  <div class="issues-layout" class:filters-hidden={!filtersVisible}>
    <aside
      id="issue-filters"
      class="filters"
      aria-label="Issue filters"
      hidden={!filtersVisible}
    >
      <form class="search" role="search" onsubmit={submitSearch}>
        <label for="issue-search">Search issues</label>
        <div class="search-control">
          <TextInput
            id="issue-search"
            name="q"
            type="search"
            bind:value={searchText}
            placeholder="Source, project, key, title…"
          />
          <Button type="submit"
            >{#snippet iconLeft()}<SearchIcon />{/snippet}Search</Button
          >
        </div>
      </form>

      <fieldset>
        <legend>Source</legend>
        {#each ISSUE_SOURCES as source (source)}
          <label class="filter-option">
            <Checkbox
              value={source}
              checked={filters.sources.includes(source)}
              onchange={(event) =>
                toggleValue(
                  source,
                  event.currentTarget.checked,
                  "source",
                  event.currentTarget,
                )}
            />
            <span>{source.toUpperCase()}</span>
          </label>
        {/each}
      </fieldset>

      <fieldset>
        <legend>Status</legend>
        {#each ISSUE_STATUSES as status (status)}
          <label class="filter-option">
            <Checkbox
              value={status}
              checked={filters.statuses.includes(status)}
              onchange={(event) =>
                toggleValue(
                  status,
                  event.currentTarget.checked,
                  "status",
                  event.currentTarget,
                )}
            />
            <span>{statusLabel(status)}</span>
          </label>
        {/each}
        {#if filters.statuses.length === 0}
          <small>All statuses</small>
        {:else if filters.statuses.length === DEFAULT_ISSUE_STATUSES.length && DEFAULT_ISSUE_STATUSES.every( (status) => filters.statuses.includes(status) ) && !pageUrl.searchParams.has("status")}
          <small>Default: open and unknown</small>
        {/if}
      </fieldset>

      <fieldset>
        <legend>Family</legend>
        {#each families as family (family.api_name)}
          <label class="filter-option">
            <Checkbox
              value={family.api_name}
              checked={filters.families.includes(family.api_name)}
              onchange={(event) =>
                toggleValue(
                  family.api_name,
                  event.currentTarget.checked,
                  "family",
                  event.currentTarget,
                )}
            />
            <span>{familyDisplayName(family)}</span>
          </label>
        {/each}
      </fieldset>

      <IssueProjectPicker
        options={projectOptions}
        selected={filters.projects}
        ontoggle={(project, checked) =>
          toggleValue(project, checked, "project")}
      >
        <small id="project-discovery-help">
          Options come from separately loaded issue pages matching the other
          filters, without a project restriction. Selected projects are always
          retained.
          {#if projects.hasMore || projects.initialLoading || projects.error}
            Discovery is incomplete; searching only checks loaded options.
          {:else}
            All {projects.nextOffset} issue rows in this discovery have been checked.
          {/if}
        </small>
        {#if projects.initialLoading}
          <small class="loading" role="status"
            ><Spinner /> Loading project options…</small
          >
        {:else if projects.error}
          <div role="alert">
            <p>Unable to load project options: {projects.error}</p>
            <Button
              density="dense"
              onclick={(
                event: MouseEvent & { currentTarget: HTMLButtonElement },
              ) => void readPage(projects, "retry", event.currentTarget, true)}
              >Retry project options</Button
            >
          </div>
        {:else if projects.hasMore}
          <Button
            density="dense"
            disabled={projects.loadingMore}
            loading={projects.loadingMore}
            aria-busy={projects.loadingMore}
            aria-label={projects.loadingMore
              ? "Loading project options…"
              : "Load more project options"}
            onclick={(
              event: MouseEvent & { currentTarget: HTMLButtonElement },
            ) => void readPage(projects, "more", event.currentTarget, true)}
          >
            {projects.loadingMore
              ? "Loading project options…"
              : "Load more project options"}
          </Button>
        {/if}
      </IssueProjectPicker>
    </aside>

    <section
      class="issue-results"
      aria-label="Issues"
      tabindex="-1"
      bind:this={resultsRegion}
    >
      {#if results.initialLoading}
        <p class="state loading" role="status"><Spinner /> Loading issues…</p>
      {:else if results.error && results.rows.length === 0}
        <div class="error-state" role="alert">
          <p>Unable to load issues: {results.error}</p>
          <Button
            type="button"
            onclick={(event) =>
              void readPage(results, "retry", event.currentTarget)}
            >Try again</Button
          >
        </div>
      {:else if visibleIssues.length === 0 && !results.hasMore}
        <p class="state">No issues found.</p>
      {:else if visibleIssues.length === 0}
        <p class="state">No matching issues on the loaded pages yet.</p>
      {/if}

      {#if results.error && results.rows.length > 0}
        <div class="error-state" role="alert">
          <p>Unable to load more issues: {results.error}</p>
          <Button
            type="button"
            onclick={(event) =>
              void readPage(results, "retry", event.currentTarget)}
            >Try again</Button
          >
        </div>
      {/if}

      {#each groups as group (group.key)}
        <section
          class="issue-group"
          aria-label={`${group.source.toUpperCase()} ${group.project}`}
        >
          <h2>
            <span>{group.source.toUpperCase()}</span><span>{group.project}</span
            >
          </h2>
          <ul>
            {#each group.issues as issue (issue.id)}
              <li>
                <div class="issue-summary">
                  <Link
                    class="external-link"
                    href={issue.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Open external issue ${issueLinkLabel(issue)} in a new tab`}
                  >
                    {issueLinkLabel(issue)}<ExternalLinkIcon />
                  </Link>
                  <Chip
                    class="status"
                    readonly
                    density="dense"
                    severity={issue.status === "open"
                      ? "positive"
                      : issue.status === "unknown"
                        ? "caution"
                        : "neutral"}
                    value={statusLabel(issue.status)}
                  />
                  <span
                    class="execution-count"
                    aria-label={`${issue.test_executions_count ?? 0} test executions`}
                  >
                    <PlayIcon aria-hidden="true" />
                    {issue.test_executions_count ?? 0} test {issue.test_executions_count ===
                    1
                      ? "execution"
                      : "executions"}
                  </span>
                </div>
                <Link
                  class="issue-title"
                  href={`${resolve("/issues")}/${issue.id}`}
                  >{issue.title || "[No title]"}</Link
                >
              </li>
            {/each}
          </ul>
        </section>
      {/each}

      {#if !results.initialLoading && results.hasMore && !results.error}
        <div class="pagination">
          <Button
            type="button"
            onclick={(event) =>
              void readPage(results, "more", event.currentTarget)}
            disabled={results.loadingMore}
            loading={results.loadingMore}
            aria-busy={results.loadingMore}
            aria-label={results.loadingMore
              ? "Loading more…"
              : `Load more issues (${ISSUE_PAGE_SIZE} at a time)`}
          >
            {results.loadingMore
              ? "Loading more…"
              : `Load more issues (${ISSUE_PAGE_SIZE} at a time)`}
          </Button>
          <span>{visibleIssues.length} matching issues shown</span>
        </div>
      {/if}
    </section>
  </div>
</div>

<style>
  .issues-page {
    max-width: 90rem;
    margin: 0 auto;
  }
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }
  h1 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 500;
  }
  .page-header p {
    margin: 0.35rem 0 0;
    color: var(--lp-color-text-muted);
  }
  .add-feedback:not(:empty) {
    margin-bottom: var(--lp-dimension-spacing-block-m);
  }
  .issues-layout {
    display: grid;
    grid-template-columns: minmax(13rem, 17rem) minmax(0, 1fr);
    gap: 1.5rem;
    align-items: start;
  }
  .filter-disclosure {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--lp-dimension-spacing-inline-s);
    margin-bottom: var(--lp-dimension-spacing-inline-m);
  }
  .issues-layout.filters-hidden {
    grid-template-columns: minmax(0, 1fr);
  }
  .filters[hidden] {
    display: none;
  }
  .filters {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }
  .search label,
  fieldset legend {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }
  .search-control {
    display: flex;
    flex-wrap: wrap;
    gap: var(--lp-dimension-spacing-inline-xs);
  }
  .search-control :global(input) {
    min-width: 0;
    flex: 1;
  }
  fieldset {
    min-width: 0;
    margin: 0;
    padding: 0;
    border: 0;
  }
  fieldset legend {
    padding: 0;
  }
  .filter-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.45rem 0;
    cursor: pointer;
  }
  small {
    display: block;
    margin-top: 0.45rem;
    color: var(--lp-color-text-muted);
  }
  .issue-results {
    min-width: 0;
  }
  .state {
    padding: 1.5rem;
    color: var(--lp-color-text-muted);
  }
  .error-state {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 0.8rem 1rem;
    color: var(--lp-color-negative);
    background: var(--lp-color-background-negative-default);
    border-radius: 0.25rem;
  }
  .error-state p {
    margin: 0;
  }
  .issue-group {
    margin-bottom: 1.25rem;
  }
  .issue-group h2 {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin: 0;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--lp-color-border-default);
    font-size: 1rem;
    font-weight: 400;
  }
  .issue-group h2 span:first-child {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
  }
  .issue-group h2 span:last-child {
    color: var(--lp-color-text-muted);
  }
  .issue-group ul {
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .issue-group li {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    padding: 0.85rem 1rem;
    border-bottom: 1px solid var(--lp-color-border-default);
  }
  .issue-summary {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
    font-size: 0.875rem;
  }
  :global(.issues-page .external-link),
  .execution-count {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  .execution-count {
    color: var(--lp-color-text-muted);
  }
  :global(.issues-page .issue-title) {
    width: fit-content;
    max-width: 100%;
    overflow: hidden;
    text-decoration: none;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .pagination {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
  }
  .pagination span {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
  }
  .loading {
    display: flex;
    align-items: center;
    gap: var(--lp-dimension-spacing-inline-s);
  }
  @media (max-width: 760px) {
    .issues-layout {
      grid-template-columns: 1fr;
    }
    .filters {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
      align-items: start;
    }
    .page-header {
      align-items: flex-start;
    }
    .issue-group li {
      padding-inline: 0.5rem;
    }
  }
</style>
