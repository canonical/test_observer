<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import { Button } from "@canonical/svelte-ds-app-launchpad";
  import type { Family } from "$lib/types";
  import { familyDisplayName } from "$lib/types";
  import {
    EXECUTION_STATUSES,
    RESULT_STATUSES,
    type SearchFilter,
  } from "$lib/testResultsSearch";
  import { listValues, type SearchFilters } from "$lib/testResultsFilters";
  import {
    clearFilter,
    cloneFilters,
    filterIsActive,
    type IdFilter,
    type MetadataCondition,
  } from "$lib/testResultsSearch";
  import {
    idLabelKey,
    loadingIdLabel,
    searchFilterLabelCache,
  } from "$lib/searchFilterLabels";
  import type { IdFilterKey } from "$lib/searchFilterLabels";
  import IdFilterEditor from "./IdFilterEditor.svelte";
  import MetadataFilterEditor from "./MetadataFilterEditor.svelte";
  import ListFilterEditor from "./ListFilterEditor.svelte";
  import {
    isLookupList,
    suggestionScope,
    type LookupListField,
  } from "$lib/searchFilterSuggestions";

  type MenuFilter = SearchFilter;
  type ListFilter = Extract<
    MenuFilter,
    | "families"
    | "test_result_statuses"
    | "test_execution_statuses"
    | "artefacts"
    | "artefact_versions"
    | "artefact_stages"
    | "artefact_tracks"
    | "environments"
    | "test_cases"
    | "test_plans"
    | "template_ids"
  >;

  let {
    filterKey,
    filters,
    families,
    invalidFields = [],
    disabled = false,
    open = false,
    onedit,
  }: {
    filterKey: MenuFilter;
    filters: SearchFilters;
    families: Family[];
    invalidFields?: SearchFilter[];
    disabled?: boolean;
    open?: boolean;
    onedit: (key: SearchFilter, next: SearchFilters) => void;
  } = $props();

  const initialFilters = untrack(() => cloneFilters(filters));
  let issueDraft = $state<IdFilter>(initialFilters.issues);
  let reviewerDraft = $state<IdFilter>(initialFilters.reviewer_ids);
  let metadataDraft = $state<MetadataCondition[]>(
    initialFilters.execution_metadata,
  );
  let observedIssue = JSON.stringify(initialFilters.issues);
  let observedReviewer = JSON.stringify(initialFilters.reviewer_ids);
  let observedMetadata = JSON.stringify(initialFilters.execution_metadata);
  let idLabels = $state<Record<string, string>>({});
  let labelGeneration = 0;
  let observedLabelSnapshot = "";
  let activeLabelRequest: {
    snapshot: string;
    controller: AbortController;
  } | null = null;
  let componentLive = true;
  onDestroy(() => {
    componentLive = false;
    activeLabelRequest?.controller.abort();
  });
  const idLabelSnapshot = $derived.by(() =>
    filterKey === "issues"
      ? JSON.stringify([filters.issues, suggestionScope()])
      : filterKey === "reviewer_ids"
        ? JSON.stringify([filters.reviewer_ids, suggestionScope()])
        : "",
  );
  let metadataValid = $state(false);
  const initialLookupDraft = untrack(() =>
    isLookupList(filterKey) ? [...filters[filterKey]] : [],
  );
  let lookupDraft = $state<string[]>(initialLookupDraft);
  let observedLookup = JSON.stringify(initialLookupDraft);

  function cloneIds(value: IdFilter): IdFilter {
    return Array.isArray(value) ? [...value] : value;
  }

  function cloneMetadata(value: MetadataCondition[]): MetadataCondition[] {
    return value.map(({ category, values }) => ({
      category,
      values: [...values],
    }));
  }

  $effect.pre(() => {
    if (filterKey === "issues") {
      const snapshot = JSON.stringify(filters.issues);
      if (snapshot !== observedIssue) {
        issueDraft = cloneIds(filters.issues);
        observedIssue = snapshot;
      }
    } else if (filterKey === "reviewer_ids") {
      const snapshot = JSON.stringify(filters.reviewer_ids);
      if (snapshot !== observedReviewer) {
        reviewerDraft = cloneIds(filters.reviewer_ids);
        observedReviewer = snapshot;
      }
    } else if (filterKey === "execution_metadata") {
      const snapshot = JSON.stringify(filters.execution_metadata);
      if (snapshot !== observedMetadata) {
        metadataDraft = cloneMetadata(filters.execution_metadata);
        observedMetadata = snapshot;
      }
    }
  });

  $effect(() => {
    if (filterKey === "issues") {
      const snapshot = JSON.stringify(issueDraft);
      if (snapshot !== observedIssue) {
        observedIssue = snapshot;
        update("issues", cloneIds(issueDraft));
      }
    } else if (filterKey === "reviewer_ids") {
      const snapshot = JSON.stringify(reviewerDraft);
      if (snapshot !== observedReviewer) {
        observedReviewer = snapshot;
        update("reviewer_ids", cloneIds(reviewerDraft));
      }
    } else if (filterKey === "execution_metadata") {
      const snapshot = JSON.stringify(metadataDraft);
      if (snapshot !== observedMetadata) {
        observedMetadata = snapshot;
        update("execution_metadata", cloneMetadata(metadataDraft));
      }
    }
  });

  $effect(() => {
    if (filterKey !== "issues" && filterKey !== "reviewer_ids") return;
    const kind: IdFilterKey = filterKey;
    const snapshot = idLabelSnapshot;
    if (snapshot === observedLabelSnapshot) return;
    observedLabelSnapshot = snapshot;
    if (activeLabelRequest) activeLabelRequest.controller.abort();
    const [selected] = JSON.parse(snapshot) as [IdFilter, string];
    const cache = searchFilterLabelCache();
    const generation = ++labelGeneration;
    const controller = new AbortController();
    activeLabelRequest = { snapshot, controller };
    const ids = Array.isArray(selected) ? selected : [];
    idLabels = Object.fromEntries(
      ids.map((id) => [
        idLabelKey(kind, id),
        cache.peek(kind, id) ?? loadingIdLabel(id),
      ]),
    );
    for (const id of ids) {
      void cache.load(kind, id, controller.signal).then((value) => {
        if (
          value !== undefined &&
          !controller.signal.aborted &&
          generation === labelGeneration
        )
          idLabels[idLabelKey(kind, id)] = value;
      });
    }
    return () =>
      // Grid state can replace an equal filter object during initial
      // hydration. Let the immediately-following effect compare the canonical
      // snapshot before cancelling shared cache consumers.
      queueMicrotask(() => {
        if (!componentLive || activeLabelRequest?.snapshot !== snapshot)
          controller.abort();
      });
  });

  $effect.pre(() => {
    if (!isLookupList(filterKey)) return;
    const snapshot = JSON.stringify(filters[filterKey]);
    if (snapshot !== observedLookup) {
      lookupDraft = [...filters[filterKey]];
      observedLookup = snapshot;
    }
  });

  $effect(() => {
    if (!isLookupList(filterKey)) return;
    const snapshot = JSON.stringify(lookupDraft);
    if (snapshot !== observedLookup) {
      observedLookup = snapshot;
      update(filterKey, [...lookupDraft]);
    }
  });

  let listDraft = $state<string | undefined>(undefined);
  let parsedDraft: string[] | undefined;
  const textListFields: Partial<
    Record<ListFilter, { label: string; placeholder: string }>
  > = {
    artefact_versions: {
      label: "Artefact Version",
      placeholder: "version, version",
    },
    artefact_tracks: { label: "Artefact Track", placeholder: "track, track" },
    template_ids: { label: "Template ID", placeholder: "ID, ID" },
  };

  $effect.pre(() => {
    if (!(filterKey in textListFields)) return;
    const key = filterKey as ListFilter;
    const parsed = parsedDraft;
    const current = filters[key];
    if (
      parsed &&
      (parsed.length !== current.length ||
        parsed.some((value, index) => value !== current[index]))
    ) {
      listDraft = undefined;
      parsedDraft = [...current];
    } else if (!parsed) {
      parsedDraft = [...current];
    }
  });

  const stages = $derived(
    [
      ...new Set([
        "",
        ...families.flatMap((family) => family.stages),
        ...filters.artefact_stages,
      ]),
    ].sort(),
  );

  function update<K extends SearchFilter>(key: K, value: SearchFilters[K]) {
    onedit(key, { ...filters, [key]: value });
  }

  function setList(key: ListFilter, value: string) {
    const parsed = listValues([value], key === "artefact_stages");
    listDraft = value;
    parsedDraft = parsed;
    update(key, parsed);
  }

  function toggleList(key: ListFilter, value: string, checked: boolean) {
    const previous = filters[key];
    const next = checked
      ? previous.includes(value)
        ? previous
        : [...previous, value]
      : previous.filter((item) => item !== value);
    update(key, next);
  }

  function setBoolean(
    key: "artefact_is_archived" | "rerun_is_requested" | "execution_is_latest",
    value: string,
  ) {
    update(key, value === "" ? null : value === "true");
  }

  function setDate(key: "from_date" | "until_date", value: string) {
    // URL parsing is the validation boundary. Keep invalid text literal so
    // Search reports the problem instead of coercing or rounding it.
    update(key, value ? (value as SearchFilters[typeof key]) : null);
  }

  function textValues(key: ListFilter): string {
    return listDraft ?? filters[key].join(", ");
  }

  function noneLabel(value: string): string {
    return value === "" ? "(none)" : value;
  }

  function hasCurrentFilter(): boolean {
    return filterKey === "from_date"
      ? Boolean(filters.from_date || filters.until_date)
      : filterIsActive(filterKey, filters);
  }

  function clearCurrentFilter() {
    if (filterKey === "from_date") {
      const next = { ...filters, from_date: null, until_date: null };
      onedit("from_date", next);
      onedit("until_date", next);
      return;
    }
    update(filterKey, clearFilter(filters, filterKey)[filterKey]);
  }
</script>

<div
  class="grid-filter-menu"
  data-testid={`search-grid-filter-menu-${filterKey}`}
  data-search-grid-menu={filterKey}
  aria-label="Server-backed exact filter"
>
  <p class="hint">
    {#if filterKey === "artefact_is_archived" || filterKey === "rerun_is_requested" || filterKey === "execution_is_latest"}
      Boolean equality; other fields are combined. Changes are drafts until
      Search.
    {:else if filterKey === "issues" || filterKey === "reviewer_ids"}
      Specific IDs, any, or none; selections are applied with Search.
    {:else if filterKey === "execution_metadata"}
      AND across categories; values within a category are alternatives. Changes
      are applied with Search.
    {:else if filterKey === "from_date"}
      Inclusive Test-result Created bounds; other fields are combined. Changes
      are drafts until Search.
    {:else}
      Exact match. Values in this field are alternatives; other fields are
      combined. Changes are drafts until Search.
    {/if}
  </p>

  {#if filterKey === "families"}
    <fieldset>
      <legend>Family</legend>
      {#each families as family (family.api_name)}
        <label>
          <input
            type="checkbox"
            value={family.api_name}
            data-search-grid-filter="families"
            checked={filters.families.includes(family.api_name)}
            {disabled}
            onchange={(event) =>
              toggleList(
                "families",
                family.api_name,
                event.currentTarget.checked,
              )}
          />
          {familyDisplayName(family)}
        </label>
      {/each}
      {#each filters.families.filter((name) => !families.some((family) => family.api_name === name)) as unavailable (unavailable)}
        <label class="unavailable">
          <input
            type="checkbox"
            value={unavailable}
            data-search-grid-filter="families"
            checked
            {disabled}
            onchange={(event) =>
              toggleList("families", unavailable, event.currentTarget.checked)}
          />
          Unavailable: {unavailable}
        </label>
      {/each}
    </fieldset>
  {:else if filterKey === "test_result_statuses"}
    <fieldset>
      <legend>Result status</legend>
      {#each RESULT_STATUSES as status (status)}
        <label>
          <input
            type="checkbox"
            value={status}
            data-search-grid-filter="test_result_statuses"
            checked={filters.test_result_statuses.includes(status)}
            {disabled}
            onchange={(event) =>
              toggleList(
                "test_result_statuses",
                status,
                event.currentTarget.checked,
              )}
          />
          {status}
        </label>
      {/each}
      {#each filters.test_result_statuses.filter((value) => !RESULT_STATUSES.includes(value as (typeof RESULT_STATUSES)[number])) as unavailable (unavailable)}
        <label class="unavailable">
          <input
            type="checkbox"
            value={unavailable}
            data-search-grid-filter="test_result_statuses"
            checked
            {disabled}
            onchange={(event) =>
              toggleList(
                "test_result_statuses",
                unavailable,
                event.currentTarget.checked,
              )}
          />
          Unsupported: {unavailable}
        </label>
      {/each}
    </fieldset>
  {:else if filterKey === "test_execution_statuses"}
    <fieldset>
      <legend>Execution status</legend>
      {#each EXECUTION_STATUSES as status (status)}
        <label>
          <input
            type="checkbox"
            value={status}
            data-search-grid-filter="test_execution_statuses"
            checked={filters.test_execution_statuses.includes(status)}
            {disabled}
            onchange={(event) =>
              toggleList(
                "test_execution_statuses",
                status,
                event.currentTarget.checked,
              )}
          />
          {status}
        </label>
      {/each}
      {#each filters.test_execution_statuses.filter((value) => !EXECUTION_STATUSES.includes(value as (typeof EXECUTION_STATUSES)[number])) as unavailable (unavailable)}
        <label class="unavailable">
          <input
            type="checkbox"
            value={unavailable}
            data-search-grid-filter="test_execution_statuses"
            checked
            {disabled}
            onchange={(event) =>
              toggleList(
                "test_execution_statuses",
                unavailable,
                event.currentTarget.checked,
              )}
          />
          Unsupported: {unavailable}
        </label>
      {/each}
    </fieldset>
  {:else if filterKey === "artefact_stages"}
    <fieldset>
      <legend>Artefact stage</legend>
      {#each stages as stage (stage)}
        <label>
          <input
            type="checkbox"
            value={stage}
            data-search-grid-filter="artefact_stages"
            checked={filters.artefact_stages.includes(stage)}
            {disabled}
            onchange={(event) =>
              toggleList("artefact_stages", stage, event.currentTarget.checked)}
          />
          {noneLabel(stage)}
        </label>
      {/each}
    </fieldset>
  {:else if filterKey in textListFields}
    {@const key = filterKey as ListFilter}
    {@const field = textListFields[key]}
    <label class="text-filter">
      {field?.label}
      <input
        type="text"
        autocomplete="off"
        placeholder={field?.placeholder}
        value={textValues(key)}
        {disabled}
        data-search-grid-filter={key}
        oninput={(event) => setList(key, event.currentTarget.value)}
        onblur={() => (listDraft = undefined)}
      />
      <span>Typed exact values; comma-separated alternatives.</span>
    </label>
  {:else if isLookupList(filterKey)}
    {@const key = filterKey as LookupListField}
    <ListFilterEditor
      field={key}
      bind:value={lookupDraft}
      {families}
      draftFamilies={filters.families}
    />
  {:else if filterKey === "artefact_is_archived" || filterKey === "rerun_is_requested" || filterKey === "execution_is_latest"}
    {@const key = filterKey}
    <label class="select-filter">
      {key === "artefact_is_archived"
        ? "Archived"
        : key === "rerun_is_requested"
          ? "Rerun Requested"
          : "Latest Execution"}
      <select
        value={filters[key] === null ? "" : String(filters[key])}
        {disabled}
        data-search-grid-filter={key}
        onchange={(event) => setBoolean(key, event.currentTarget.value)}
      >
        <option value="">Any</option>
        <option value="false">No</option>
        <option value="true">Yes</option>
      </select>
    </label>
  {:else if filterKey === "from_date"}
    <label class="text-filter date-filter">
      Test-result Created — From (inclusive)
      <input
        type="text"
        autocomplete="off"
        placeholder="2026-01-01T00:00:00Z"
        value={filters.from_date ?? ""}
        {disabled}
        data-search-grid-filter="from_date"
        oninput={(event) => setDate("from_date", event.currentTarget.value)}
      />
      <span>ISO instant with Z or an explicit ±HH:MM offset.</span>
    </label>
    <label class="text-filter date-filter">
      Test-result Created — Until (inclusive)
      <input
        type="text"
        autocomplete="off"
        placeholder="2026-01-31T23:59:59Z"
        value={filters.until_date ?? ""}
        {disabled}
        data-search-grid-filter="until_date"
        oninput={(event) => setDate("until_date", event.currentTarget.value)}
      />
      <span>Either inclusive bound may be left empty.</span>
    </label>
  {:else if filterKey === "issues"}
    <IdFilterEditor
      field="issues"
      bind:value={issueDraft}
      labels={idLabels}
      {disabled}
    />
  {:else if filterKey === "reviewer_ids"}
    <IdFilterEditor
      field="reviewer_ids"
      bind:value={reviewerDraft}
      labels={idLabels}
      {disabled}
    />
  {:else if filterKey === "execution_metadata"}
    <MetadataFilterEditor
      bind:value={metadataDraft}
      bind:valid={metadataValid}
      enabled={open}
      {disabled}
    />
  {/if}
  {#if hasCurrentFilter() || invalidFields.includes(filterKey)}
    <Button
      type="button"
      density="dense"
      {disabled}
      data-search-grid-clear={filterKey}
      onclick={clearCurrentFilter}>Clear filter</Button
    >
  {/if}
</div>

<style>
  .grid-filter-menu {
    box-sizing: border-box;
    width: min(20rem, calc(100vw - 1rem));
    padding: 0.75rem;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-default);
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1.5rem rgb(0 0 0 / 20%);
  }
  .hint {
    margin: 0 0 0.65rem;
    color: var(--lp-color-text-muted);
    font-size: 0.8rem;
    line-height: 1.35;
  }
  fieldset {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem 0.8rem;
    min-width: 0;
    margin: 0;
    padding: 0.5rem;
    border: 1px solid var(--lp-color-border-default);
  }
  fieldset label {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }
  .unavailable {
    color: var(--lp-color-text-muted);
  }
  .text-filter,
  .select-filter {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 0;
  }
  .text-filter input,
  .select-filter select {
    box-sizing: border-box;
    width: 100%;
    min-height: 2rem;
  }
  .text-filter span {
    color: var(--lp-color-text-muted);
    font-size: 0.75rem;
  }
  .date-filter + .date-filter {
    margin-top: 0.6rem;
  }
</style>
