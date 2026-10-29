<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import { Button } from "@canonical/svelte-ds-app-launchpad";
  import { ChevronDownIcon, ChevronUpIcon } from "@canonical/svelte-icons";
  import {
    ISSUE_RESULT_LISTS,
    emptyIssueResultFilters,
    issueResultsQuery,
    issueResultGroupCount,
    type IssueResultFilters,
  } from "$lib/issueTestResults";
  import {
    FILTER_DEFINITIONS,
    filtersEqual,
    type SearchFilters,
  } from "$lib/testResultsFilters";
  import type { Family } from "$lib/types";
  import ListFilterEditor from "$lib/components/search/ListFilterEditor.svelte";
  import InstantFilterEditor from "$lib/components/search/InstantFilterEditor.svelte";

  let {
    issueId,
    families,
    applied,
    onapply,
  }: {
    issueId: number;
    families: Family[];
    applied: SearchFilters;
    onapply: (filters: IssueResultFilters) => void;
  } = $props();
  const id = $props.id();
  let live = true;
  onDestroy(() => (live = false));
  const dateBounds = ["from_date", "until_date"] as const;
  let expanded = $state(false);
  let draft = $state(emptyIssueResultFilters());
  let revision = $state(0);
  let pending = $state({
    families: false,
    artefacts: false,
    environments: false,
    test_cases: false,
  });
  const candidate = $derived(issueResultsQuery(issueId, draft));
  const dirty = $derived(
    candidate.problems.length > 0 || !filtersEqual(candidate.filters, applied),
  );
  const hasPending = $derived(Object.values(pending).some(Boolean));
  const activeCount = $derived(issueResultGroupCount(applied));

  function clearDrafts() {
    draft = emptyIssueResultFilters();
    pending = {
      families: false,
      artefacts: false,
      environments: false,
      test_cases: false,
    };
    revision++;
  }
  function apply() {
    if (!live || candidate.problems.length || hasPending) return;
    // Snapshot plain selected values, never lookup text or editor-bound values.
    onapply(
      untrack(() => ({
        ...draft,
        families: [...draft.families],
        artefacts: [...draft.artefacts],
        environments: [...draft.environments],
        test_cases: [...draft.test_cases],
      })),
    );
  }
</script>

<div class="issue-result-filters">
  <!-- Pragma 0.33 has no Accordion export. A Pragma Button exposes the native
       disclosure semantics, with editors kept mounted while collapsed. -->
  <Button
    type="button"
    aria-expanded={expanded}
    aria-controls={`${id}-filters`}
    onclick={() => (expanded = !expanded)}
  >
    Optional filters ({activeCount} applied groups)
    {#snippet iconRight()}{#if expanded}<ChevronUpIcon />{:else}<ChevronDownIcon
        />{/if}{/snippet}
  </Button>
  {#if dirty || hasPending}<p role="status">
      Changes not applied. Results and counts use the applied filters.
    </p>{/if}
  <div id={`${id}-filters`} hidden={!expanded}>
    <p>
      All results stay pinned to issue #{issueId}. Dates count as one optional
      group.
    </p>
    {#key revision}
      <div class="groups">
        {#each ISSUE_RESULT_LISTS as field (field)}
          <section aria-label={`${FILTER_DEFINITIONS[field].label} filter`}>
            <h3>{FILTER_DEFINITIONS[field].label}</h3>
            <ListFilterEditor
              {field}
              bind:value={draft[field]}
              bind:pending={pending[field]}
              {families}
              draftFamilies={draft.families}
            />
          </section>
        {/each}
        <section class="dates" aria-label="Created date filter">
          <h3>Created (inclusive)</h3>
          <div class="groups">
            {#each dateBounds as field (field)}
              <div>
                <h4>{field === "from_date" ? "From" : "Until"} (optional)</h4>
                <InstantFilterEditor
                  {field}
                  value={candidate.filters[field]}
                  other={candidate.filters[
                    field === "from_date" ? "until_date" : "from_date"
                  ]}
                  bind:text={draft[field]}
                />
              </div>
            {/each}
          </div>
        </section>
      </div>
    {/key}
    {#if candidate.problems.length}<div role="alert">
        Filters not applied. {candidate.problems.join(" ")}
      </div>{/if}
    {#if hasPending}<p>
        Select a suggestion, add the exact value, or clear pending lookup input
        before Apply. Pending text is not a filter.
      </p>{/if}
    <div class="actions">
      <Button
        type="button"
        severity="brand"
        disabled={candidate.problems.length > 0 || hasPending}
        onclick={apply}>Apply filters</Button
      >
      <Button type="button" onclick={clearDrafts}>Clear optional drafts</Button>
    </div>
    <p class="hint">
      Clearing only edits drafts. Apply filters to update results; the pinned
      issue is never cleared.
    </p>
  </div>
</div>

<style>
  .issue-result-filters {
    margin-block: var(--lp-dimension-spacing-block-m);
  }
  .groups {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
    gap: var(--lp-dimension-spacing-inline-xl);
  }
  .groups > * {
    min-width: 0;
  }
  .dates {
    grid-column: 1 / -1;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: var(--lp-dimension-spacing-inline-m);
    margin-block: var(--lp-dimension-spacing-block-m);
  }
  .hint {
    color: var(--lp-color-text-muted);
  }
</style>
