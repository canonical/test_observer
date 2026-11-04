<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import { type IdFilter } from "$lib/testResultsFilters";
  import { ID_MODE_LABELS } from "$lib/searchFilterEditor";
  import { type IdFilterKey } from "$lib/searchFilterLabels";
  import ValueSuggestions from "./ValueSuggestions.svelte";
  let {
    field,
    value = $bindable(),
    // eslint-disable-next-line no-useless-assignment -- Bindable validation output is read by the owning form.
    valid = $bindable(false),
    labels,
  }: {
    field: IdFilterKey;
    value: IdFilter;
    valid?: boolean;
    labels: Record<string, string>;
  } = $props();
  const id = $props.id();
  let mode = $state<"ids" | "any" | "none">(
    untrack(() => (Array.isArray(value) ? "ids" : value)),
  );
  let selected = $state(
    untrack(() => (Array.isArray(value) ? value.map(String) : [])),
  );
  let pending = $state(false);
  $effect(() => {
    if (mode !== "ids") {
      value = mode;
      valid = true;
      return;
    }
    value = selected.map(Number);
    valid = selected.length > 0 && !pending;
  });
</script>

<fieldset>
  <legend>Match mode (choose one)</legend>
  <label
    ><input
      type="radio"
      name={`${id}-mode`}
      bind:group={mode}
      value="ids"
    />Specific IDs</label
  >
  <label
    ><input
      type="radio"
      name={`${id}-mode`}
      bind:group={mode}
      value="any"
    />{ID_MODE_LABELS[field].any}</label
  >
  <label
    ><input
      type="radio"
      name={`${id}-mode`}
      bind:group={mode}
      value="none"
    />{ID_MODE_LABELS[field].none}</label
  >
</fieldset>
{#if mode === "ids"}
  <ValueSuggestions {field} bind:selected bind:pending {labels} />
{/if}

<style>
  fieldset {
    border: 0;
    padding: 0;
    margin: 0 0 1rem;
  }
  label {
    display: block;
    margin: 0.5rem 0;
  }
  fieldset label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
</style>
