<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { Family } from "$lib/types";
  import type { SearchFilter, SearchFilters } from "$lib/testResultsFilters";
  import {
    isListFilter,
    isBooleanFilter,
    isIdFilter,
    isInstantFilter,
  } from "$lib/searchFilterEditor";
  import ListFilterEditor from "./ListFilterEditor.svelte";
  import BooleanFilterEditor from "./BooleanFilterEditor.svelte";
  import IdFilterEditor from "./IdFilterEditor.svelte";
  import MetadataFilterEditor from "./MetadataFilterEditor.svelte";
  import InstantFilterEditor from "./InstantFilterEditor.svelte";
  let {
    field,
    filters = $bindable(),
    valid = $bindable(false),
    families,
    labels,
  }: {
    field: SearchFilter;
    filters: SearchFilters;
    valid?: boolean;
    families: Family[];
    labels: Record<string, string>;
  } = $props();
</script>

{#if isListFilter(field)}
  <ListFilterEditor
    {field}
    bind:value={filters[field]}
    bind:valid
    {families}
    draftFamilies={filters.families}
  />
{:else if isBooleanFilter(field)}
  <BooleanFilterEditor {field} bind:value={filters[field]} bind:valid />
{:else if isIdFilter(field)}
  <IdFilterEditor {field} bind:value={filters[field]} bind:valid {labels} />
{:else if field === "execution_metadata"}
  <MetadataFilterEditor bind:value={filters.execution_metadata} bind:valid />
{:else if isInstantFilter(field)}
  <InstantFilterEditor
    {field}
    bind:value={filters[field]}
    other={field === "from_date" ? filters.until_date : filters.from_date}
    bind:valid
  />
{/if}
