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
    disabled = false,
    hideLabel = false,
    conciseGuidance = false,
  }: {
    field: IdFilterKey;
    value: IdFilter;
    valid?: boolean;
    labels: Record<string, string>;
    disabled?: boolean;
    hideLabel?: boolean;
    conciseGuidance?: boolean;
  } = $props();
  const id = $props.id();
  const initial = untrack(() => value);
  let mode = $state<"ids" | "any" | "none">(
    Array.isArray(initial) ? "ids" : initial,
  );
  let selected = $state(Array.isArray(initial) ? initial.map(String) : []);
  let observed = JSON.stringify(initial);
  let pending = $state(false);
  $effect.pre(() => {
    const snapshot = JSON.stringify(value);
    if (snapshot === observed) return;
    observed = snapshot;
    mode = Array.isArray(value) ? "ids" : value;
    selected = Array.isArray(value) ? value.map(String) : [];
  });
  $effect(() => {
    let next: typeof value;
    if (mode !== "ids") {
      next = mode;
      valid = true;
    } else {
      next = selected.map(Number);
      valid = selected.length > 0 && !pending;
    }
    const snapshot = JSON.stringify(next);
    if (snapshot !== observed) {
      observed = snapshot;
      value = next;
    }
  });
</script>

<fieldset>
  <legend class:visually-hidden={hideLabel}>Match mode (choose one)</legend>
  <label
    ><input
      type="radio"
      name={`${id}-mode`}
      bind:group={mode}
      value="ids"
      {disabled}
    />Specific IDs</label
  >
  <label
    ><input
      type="radio"
      name={`${id}-mode`}
      bind:group={mode}
      value="any"
      {disabled}
    />{ID_MODE_LABELS[field].any}</label
  >
  <label
    ><input
      type="radio"
      name={`${id}-mode`}
      bind:group={mode}
      value="none"
      {disabled}
    />{ID_MODE_LABELS[field].none}</label
  >
</fieldset>
{#if mode === "ids"}
  <ValueSuggestions
    {field}
    bind:selected
    bind:pending
    {labels}
    {disabled}
    {hideLabel}
    {conciseGuidance}
  />
{/if}

<style>
  fieldset {
    border: 0;
    padding: 0;
    margin: 0 0 1rem;
  }
  .visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
    border: 0;
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
