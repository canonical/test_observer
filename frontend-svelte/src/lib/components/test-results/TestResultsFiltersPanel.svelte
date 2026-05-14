<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Chip, SearchBox } from "@canonical/svelte-ds-app-launchpad";
  import type { TestResultsFilters, IntListFilter } from "$lib/types/filters.js";
  import type { TestResultStatus } from "$lib/types/test-result.js";
  import { formatStatus } from "$lib/utils/formatting.js";

  interface Props {
    filters: TestResultsFilters;
    familyOptions: string[];
    onapply: (filters: TestResultsFilters) => void;
    onreset: () => void;
  }

  const { filters, familyOptions, onapply, onreset }: Props = $props();

  const allStatuses: TestResultStatus[] = ["PASSED", "FAILED", "SKIPPED"];

  let draft: TestResultsFilters = $state(undefined!);

  $effect(() => {
    draft = structuredClone($state.snapshot(filters));
  });

  function toggleFamily(family: string): void {
    if (draft.families.includes(family)) {
      draft.families = draft.families.filter((f) => f !== family);
    } else {
      draft.families = [...draft.families, family];
    }
  }

  function toggleStatus(status: TestResultStatus): void {
    if (draft.testResultStatuses.includes(status)) {
      draft.testResultStatuses = draft.testResultStatuses.filter((s) => s !== status);
    } else {
      draft.testResultStatuses = [...draft.testResultStatuses, status];
    }
  }

  function handleArtefactInput(e: Event): void {
    const target = e.target as HTMLInputElement;
    const value = target.value.trim();
    if (value && !draft.artefacts.includes(value)) {
      draft.artefacts = [...draft.artefacts, value];
    }
  }

  function handleEnvironmentInput(e: Event): void {
    const target = e.target as HTMLInputElement;
    const value = target.value.trim();
    if (value && !draft.environments.includes(value)) {
      draft.environments = [...draft.environments, value];
    }
  }

  function handleTestCaseInput(e: Event): void {
    const target = e.target as HTMLInputElement;
    const value = target.value.trim();
    if (value && !draft.testCases.includes(value)) {
      draft.testCases = [...draft.testCases, value];
    }
  }

  function handleTemplateIdInput(e: Event): void {
    const target = e.target as HTMLInputElement;
    const value = target.value.trim();
    if (value && !draft.templateIds.includes(value)) {
      draft.templateIds = [...draft.templateIds, value];
    }
  }

  function setIssuesFilter(type: IntListFilter["type"]): void {
    draft.issues = { type } as IntListFilter;
  }

  function setAssigneesFilter(type: IntListFilter["type"]): void {
    draft.assignees = { type } as IntListFilter;
  }

  function removeArtefact(name: string): void {
    draft.artefacts = draft.artefacts.filter((a) => a !== name);
  }

  function removeEnvironment(name: string): void {
    draft.environments = draft.environments.filter((e) => e !== name);
  }

  function removeTestCase(name: string): void {
    draft.testCases = draft.testCases.filter((t) => t !== name);
  }

  function removeTemplateId(id: string): void {
    draft.templateIds = draft.templateIds.filter((t) => t !== id);
  }

  function handleApply(): void {
    onapply(structuredClone(draft));
  }

  function handleReset(): void {
    onreset();
  }

  const activeFilterChips = $derived.by(() => {
    const chips: { label: string; key: string; dismiss: () => void }[] = [];

    for (const f of draft.families) {
      chips.push({ label: `Family: ${f}`, key: `family-${f}`, dismiss: () => toggleFamily(f) });
    }
    for (const s of draft.testResultStatuses) {
      chips.push({
        label: `Status: ${formatStatus(s)}`,
        key: `status-${s}`,
        dismiss: () => toggleStatus(s),
      });
    }
    for (const a of draft.artefacts) {
      chips.push({ label: `Artefact: ${a}`, key: `artefact-${a}`, dismiss: () => removeArtefact(a) });
    }
    for (const e of draft.environments) {
      chips.push({ label: `Env: ${e}`, key: `env-${e}`, dismiss: () => removeEnvironment(e) });
    }
    for (const t of draft.testCases) {
      chips.push({ label: `Test: ${t}`, key: `test-${t}`, dismiss: () => removeTestCase(t) });
    }
    for (const t of draft.templateIds) {
      chips.push({ label: `Template: ${t}`, key: `tpl-${t}`, dismiss: () => removeTemplateId(t) });
    }
    if (draft.fromDate) {
      chips.push({
        label: `From: ${draft.fromDate}`,
        key: "from",
        dismiss: () => { draft.fromDate = undefined; },
      });
    }
    if (draft.untilDate) {
      chips.push({
        label: `Until: ${draft.untilDate}`,
        key: "until",
        dismiss: () => { draft.untilDate = undefined; },
      });
    }
    if (draft.issues.type === "none") {
      chips.push({ label: "Issues: None", key: "issues-none", dismiss: () => setIssuesFilter("any") });
    }
    if (draft.assignees.type === "none") {
      chips.push({ label: "Assignees: None", key: "assignees-none", dismiss: () => setAssigneesFilter("any") });
    }
    return chips;
  });
</script>

<div class="ds filter-panel">
  <div class="ds filter-panel__row">
    <fieldset class="ds filter-panel__group">
      <legend>Family</legend>
      <div class="ds filter-panel__chips">
        {#each familyOptions as family (family)}
          {@const active = draft.families.includes(family)}
          <Chip
            value={family}
            severity={active ? "positive" : undefined}
            onclick={() => toggleFamily(family)}
          />
        {/each}
      </div>
    </fieldset>

    <fieldset class="ds filter-panel__group">
      <legend>Status</legend>
      <div class="ds filter-panel__chips">
        {#each allStatuses as status (status)}
          {@const active = draft.testResultStatuses.includes(status)}
          <Chip
            value={formatStatus(status)}
            severity={active
              ? status === "PASSED"
                ? "positive"
                : status === "FAILED"
                  ? "negative"
                  : "neutral"
              : undefined}
            onclick={() => toggleStatus(status)}
          />
        {/each}
      </div>
    </fieldset>
  </div>

  <div class="ds filter-panel__row">
    <div class="ds filter-panel__group">
      <label for="artefact-search">Artefact</label>
      <SearchBox
        id="artefact-search"
        placeholder="Search artefacts…"
        aria-label="Filter by artefact name"
        onchange={handleArtefactInput}
      />
      {#if draft.artefacts.length > 0}
        <div class="ds filter-panel__chips">
          {#each draft.artefacts as name (name)}
            <Chip value={name} ondismiss={() => removeArtefact(name)} />
          {/each}
        </div>
      {/if}
    </div>

    <div class="ds filter-panel__group">
      <label for="env-search">Environment</label>
      <SearchBox
        id="env-search"
        placeholder="Search environments…"
        aria-label="Filter by environment"
        onchange={handleEnvironmentInput}
      />
      {#if draft.environments.length > 0}
        <div class="ds filter-panel__chips">
          {#each draft.environments as name (name)}
            <Chip value={name} ondismiss={() => removeEnvironment(name)} />
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <div class="ds filter-panel__row">
    <div class="ds filter-panel__group">
      <label for="testcase-search">Test Case</label>
      <SearchBox
        id="testcase-search"
        placeholder="Search test cases…"
        aria-label="Filter by test case"
        onchange={handleTestCaseInput}
      />
      {#if draft.testCases.length > 0}
        <div class="ds filter-panel__chips">
          {#each draft.testCases as name (name)}
            <Chip value={name} ondismiss={() => removeTestCase(name)} />
          {/each}
        </div>
      {/if}
    </div>

    <div class="ds filter-panel__group">
      <label for="template-search">Template ID</label>
      <SearchBox
        id="template-search"
        placeholder="Search template IDs…"
        aria-label="Filter by template ID"
        onchange={handleTemplateIdInput}
      />
      {#if draft.templateIds.length > 0}
        <div class="ds filter-panel__chips">
          {#each draft.templateIds as id (id)}
            <Chip value={id} ondismiss={() => removeTemplateId(id)} />
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <div class="ds filter-panel__row">
    <fieldset class="ds filter-panel__group">
      <legend>Issues</legend>
      <div class="ds filter-panel__chips">
        <Chip
          value="Any"
          severity={draft.issues.type === "any" ? "positive" : undefined}
          onclick={() => setIssuesFilter("any")}
        />
        <Chip
          value="None"
          severity={draft.issues.type === "none" ? "positive" : undefined}
          onclick={() => setIssuesFilter("none")}
        />
      </div>
    </fieldset>

    <fieldset class="ds filter-panel__group">
      <legend>Assignees</legend>
      <div class="ds filter-panel__chips">
        <Chip
          value="Any"
          severity={draft.assignees.type === "any" ? "positive" : undefined}
          onclick={() => setAssigneesFilter("any")}
        />
        <Chip
          value="None"
          severity={draft.assignees.type === "none" ? "positive" : undefined}
          onclick={() => setAssigneesFilter("none")}
        />
      </div>
    </fieldset>
  </div>

  <div class="ds filter-panel__row">
    <div class="ds filter-panel__group">
      <label>
        <input
          type="checkbox"
          checked={draft.artefactIsArchived === true}
          onchange={() => {
            draft.artefactIsArchived = draft.artefactIsArchived === true ? undefined : true;
          }}
        />
        Archived artefacts
      </label>
    </div>

    <div class="ds filter-panel__group">
      <label>
        <input
          type="checkbox"
          checked={draft.rerunIsRequested === true}
          onchange={() => {
            draft.rerunIsRequested = draft.rerunIsRequested === true ? undefined : true;
          }}
        />
        Rerun requested
      </label>
    </div>

    <div class="ds filter-panel__group">
      <label>
        <input
          type="checkbox"
          checked={draft.executionIsLatest === true}
          onchange={() => {
            draft.executionIsLatest = draft.executionIsLatest === true ? undefined : true;
          }}
        />
        Latest execution only
      </label>
    </div>
  </div>

  <div class="ds filter-panel__row">
    <div class="ds filter-panel__group">
      <label for="from-date">From</label>
      <input
        id="from-date"
        type="date"
        value={draft.fromDate ?? ""}
        onchange={(e) => { draft.fromDate = e.currentTarget.value || undefined; }}
      />
    </div>

    <div class="ds filter-panel__group">
      <label for="until-date">Until</label>
      <input
        id="until-date"
        type="date"
        value={draft.untilDate ?? ""}
        onchange={(e) => { draft.untilDate = e.currentTarget.value || undefined; }}
      />
    </div>
  </div>

  <div class="ds filter-panel__actions">
    <button type="button" class="ds filter-panel__apply-btn" onclick={handleApply}>Apply Filters</button>
    <button type="button" class="ds filter-panel__reset-btn" onclick={handleReset}>Reset</button>
  </div>

  {#if activeFilterChips.length > 0}
    <div class="ds filter-panel__active" aria-live="polite">
      {#each activeFilterChips as chip (chip.key)}
        <Chip value={chip.label} ondismiss={chip.dismiss} />
      {/each}
    </div>
  {/if}
</div>

<style>
  .ds.filter-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background: var(--color-background, #fff);
  }

  .ds.filter-panel__row {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: flex-start;
  }

  .ds.filter-panel__group {
    flex: 1;
    min-width: 12rem;
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    border: none;
    padding: 0;
    margin: 0;
  }

  .ds.filter-panel__group legend,
  .ds.filter-panel__group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text, #333);
  }

  .ds.filter-panel__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .ds.filter-panel__actions {
    display: flex;
    gap: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.filter-panel__active {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
    padding-top: 0.5rem;
  }
</style>
