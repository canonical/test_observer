<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import { Checkbox, TextInput } from "@canonical/svelte-ds-app-launchpad";
  import { listValues } from "$lib/testResultsFilters";
  import { RESULT_STATUSES } from "$lib/testResultsSearch";
  import type { ListFilterKey } from "$lib/searchFilterEditor";
  import { statusDisplayName } from "$lib/searchFilterEditor";
  import type { Family } from "$lib/types";
  import { familyDisplayName } from "$lib/types";
  import { isLookupList } from "$lib/searchFilterSuggestions";
  import ValueSuggestions from "./ValueSuggestions.svelte";

  let {
    field,
    value = $bindable(),
    // eslint-disable-next-line no-useless-assignment -- Bindable validation output is read by the owning form.
    valid = $bindable(false),
    families,
    draftFamilies,
  }: {
    field: ListFilterKey;
    value: string[];
    valid?: boolean;
    families: Family[];
    draftFamilies: string[];
  } = $props();
  const id = $props.id();
  const choice = $derived(
    field === "families" ||
      field === "test_result_statuses" ||
      field === "artefact_stages",
  );
  let text = $state(untrack(() => value.join(", ")));
  let pending = $state(false);
  const configured = $derived(
    field === "families"
      ? families.map((family) => ({
          value: family.api_name,
          label: familyDisplayName(family),
        }))
      : field === "test_result_statuses"
        ? RESULT_STATUSES.map((status) => ({
            value: status,
            label: statusDisplayName(status),
          }))
        : [
            ...new Set(["", ...families.flatMap((family) => family.stages)]),
          ].map((stage) => ({
            value: stage,
            label: stage === "" ? "(none)" : stage,
          })),
  );
  const unknown = $derived(
    value.filter((item) => !configured.some((option) => option.value === item)),
  );
  $effect(() => {
    if (!choice && !isLookupList(field)) value = listValues([text]);
  });
  $effect(() => {
    valid = value.length > 0 && !pending;
  });
</script>

{#if choice}
  <fieldset>
    <legend>Match any selected value</legend>
    <div class="options">
      {#each configured as option (option.value)}
        <label
          ><Checkbox
            bind:group={value}
            value={option.value}
          />{option.label}</label
        >
      {/each}
      {#each unknown as item (item)}
        <label
          ><Checkbox bind:group={value} value={item} />{item} (not configured)</label
        >
      {/each}
    </div>
    {#if unknown.length}<p class="hint">
        Unconfigured selections are retained. Uncheck them explicitly to remove
        them.
      </p>{/if}
    {#if field === "artefact_stages"}<p class="hint">
        Stages from all configured families. (none) matches an explicitly empty
        stage.
      </p>{/if}
    {#if field === "families" && !families.length}<p class="hint">
        Family configuration unavailable.
      </p>{/if}
  </fieldset>
{:else if isLookupList(field)}
  <ValueSuggestions
    {field}
    bind:selected={value}
    bind:pending
    {draftFamilies}
  />
{:else}
  <label for={id}>Exact values</label>
  <TextInput
    {id}
    name={field}
    bind:value={text}
    aria-describedby={`${id}-hint`}
  />
  <p id={`${id}-hint`} class="hint">
    Separate values with commas. Match any value, exactly.
  </p>
{/if}

<style>
  fieldset {
    border: 0;
    padding: 0;
    margin: 0 0 1rem;
    min-width: 0;
  }
  legend,
  label {
    margin-bottom: 0.5rem;
  }
  label {
    display: block;
  }
  .options {
    max-height: min(17rem, 40dvh);
    overflow: auto;
  }
  .options label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0;
    overflow-wrap: anywhere;
  }
  .hint {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
    margin: 0.5rem 0 1rem;
  }
</style>
