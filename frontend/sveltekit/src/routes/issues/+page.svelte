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
  import { page } from "$app/state";
  import { beforeNavigate, goto } from "$app/navigation";
  import { onDestroy, untrack } from "svelte";
  import { Button } from "@canonical/svelte-ds-app-launchpad";
  import { resolve } from "$app/paths";
  import { getApiRoot } from "$lib/config";
  import { userStore } from "$lib/stores/user.svelte";
  import { IssueListPages } from "$lib/issueListPages.svelte";
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
  beforeNavigate(() => {
    ++addNavigation;
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
    results.dispose();
    projects.dispose();
  });

  // Compose rapid changes against the most recent intended URL, not a stale
  // page snapshot while goto is pending. Only the latest navigation can clear it.
  let pendingUrl: URL | null = null;
  let navigationRevision = 0;
  function navigate(next: URL) {
    pendingUrl = next;
    const revision = ++navigationRevision;
    return goto(next, { reset: false }).finally(() => {
      if (revision === navigationRevision) pendingUrl = null;
    });
  }

  function updateFilter(
    name: "source" | "status" | "family" | "project",
    values: string[],
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
    return navigate(next);
  }

  function toggleValue(
    value: string,
    checked: boolean,
    name: "source" | "status" | "family" | "project",
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
    return updateFilter(name, next);
  }

  function submitSearch(event: SubmitEvent) {
    event.preventDefault();
    const next = new URL((pendingUrl ?? pageUrl).href);
    const query = searchText.trim();
    if (query) next.searchParams.set("q", query);
    else next.searchParams.delete("q");
    navigate(next);
  }

  function issueAdded(id: number) {
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

<div class="issues-page">
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
      onclick={() => (filtersVisible = !filtersVisible)}
      >{filtersVisible ? "Hide filters" : "Show filters"}</Button
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
          <input
            id="issue-search"
            name="q"
            type="search"
            bind:value={searchText}
            placeholder="Source, project, key, title…"
          />
          <button type="submit">Search</button>
        </div>
      </form>

      <fieldset>
        <legend>Source</legend>
        {#each ISSUE_SOURCES as source (source)}
          <label class="filter-option">
            <input
              type="checkbox"
              value={source}
              checked={filters.sources.includes(source)}
              onchange={(event) =>
                toggleValue(source, event.currentTarget.checked, "source")}
            />
            <span>{source.toUpperCase()}</span>
          </label>
        {/each}
      </fieldset>

      <fieldset>
        <legend>Status</legend>
        {#each ISSUE_STATUSES as status (status)}
          <label class="filter-option">
            <input
              type="checkbox"
              value={status}
              checked={filters.statuses.includes(status)}
              onchange={(event) =>
                toggleValue(status, event.currentTarget.checked, "status")}
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
            <input
              type="checkbox"
              value={family.api_name}
              checked={filters.families.includes(family.api_name)}
              onchange={(event) =>
                toggleValue(
                  family.api_name,
                  event.currentTarget.checked,
                  "family",
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
          <small role="status">Loading project options…</small>
        {:else if projects.error}
          <div role="alert">
            <p>Unable to load project options: {projects.error}</p>
            <Button density="dense" onclick={() => void projects.retry()}
              >Retry project options</Button
            >
          </div>
        {:else if projects.hasMore}
          <Button
            density="dense"
            disabled={projects.loadingMore}
            onclick={() => void projects.more()}
          >
            {projects.loadingMore
              ? "Loading project options…"
              : "Load more project options"}
          </Button>
        {/if}
      </IssueProjectPicker>
    </aside>

    <section class="issue-results" aria-label="Issues">
      {#if results.initialLoading}
        <p class="state" role="status">Loading issues…</p>
      {:else if results.error && results.rows.length === 0}
        <div class="error-state" role="alert">
          <p>Unable to load issues: {results.error}</p>
          <button type="button" onclick={() => void results.retry()}
            >Try again</button
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
          <button type="button" onclick={() => void results.retry()}
            >Try again</button
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
                  <a
                    class="external-link"
                    href={issue.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Open external issue ${issueLinkLabel(issue)} in a new tab`}
                  >
                    {issueLinkLabel(issue)}
                  </a>
                  <span class={`status status-${issue.status}`}
                    >{statusLabel(issue.status)}</span
                  >
                  <span
                    class="execution-count"
                    aria-label={`${issue.test_executions_count ?? 0} test executions`}
                  >
                    <span aria-hidden="true">▶</span>
                    {issue.test_executions_count ?? 0} test {issue.test_executions_count ===
                    1
                      ? "execution"
                      : "executions"}
                  </span>
                </div>
                <a
                  class="issue-title"
                  href={`${resolve("/issues")}/${issue.id}`}
                  >{issue.title || "[No title]"}</a
                >
              </li>
            {/each}
          </ul>
        </section>
      {/each}

      {#if !results.initialLoading && results.hasMore && !results.error}
        <div class="pagination">
          <button
            type="button"
            onclick={() => void results.more()}
            disabled={results.loadingMore}
          >
            {results.loadingMore
              ? "Loading more…"
              : `Load more issues (${ISSUE_PAGE_SIZE} at a time)`}
          </button>
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
    color: var(--lp-color-text-muted, #666);
  }
  button {
    border: 1px solid var(--lp-color-border-default, #b8b8b8);
    border-radius: 0.25rem;
    padding: 0.55rem 0.85rem;
    color: var(--lp-color-text-default, #222);
    background: var(--lp-color-background-default, #fff);
    font: inherit;
    cursor: pointer;
  }
  button:hover:not(:disabled) {
    background: var(--lp-color-background-hover, #f5f5f5);
  }
  button:disabled {
    cursor: wait;
    opacity: 0.7;
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
    gap: 0.4rem;
  }
  .search-control input {
    min-width: 0;
    flex: 1;
  }
  input[type="search"] {
    box-sizing: border-box;
    width: 100%;
    border: 1px solid var(--lp-color-border-default, #b8b8b8);
    border-radius: 0.25rem;
    padding: 0.55rem;
    color: inherit;
    background: var(--lp-color-background-default, #fff);
    font: inherit;
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
  .filter-option input {
    accent-color: #77216f;
  }
  small {
    display: block;
    margin-top: 0.45rem;
    color: var(--lp-color-text-muted, #666);
  }
  .issue-results {
    min-width: 0;
  }
  .state {
    padding: 1.5rem;
    color: var(--lp-color-text-muted, #666);
  }
  .error-state {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 0.8rem 1rem;
    color: #a40000;
    background: #f8eeee;
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
    border-bottom: 1px solid var(--lp-color-border-default, #d9d9d9);
    font-size: 1rem;
    font-weight: 400;
  }
  .issue-group h2 span:first-child {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
  }
  .issue-group h2 span:last-child {
    color: var(--lp-color-text-muted, #666);
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
    border-bottom: 1px solid var(--lp-color-border-default, #e5e5e5);
  }
  .issue-summary {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
    font-size: 0.875rem;
  }
  .external-link {
    color: #06c;
    text-decoration: underline;
  }
  .status {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  .status::before {
    content: "";
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
    background: #666;
  }
  .status-open::before {
    background: #0e8420;
  }
  .status-closed::before {
    background: #77216f;
  }
  .execution-count {
    color: var(--lp-color-text-muted, #666);
  }
  .issue-title {
    width: fit-content;
    max-width: 100%;
    overflow: hidden;
    color: var(--lp-color-text-link, #06c);
    text-decoration: none;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .issue-title:hover {
    text-decoration: underline;
  }
  .pagination {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
  }
  .pagination span {
    color: var(--lp-color-text-muted, #666);
    font-size: 0.875rem;
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
