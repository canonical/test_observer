<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import { TextInput } from "@canonical/svelte-ds-app-launchpad";
  import { FILTER_DEFINITIONS, type IdFilter } from "$lib/testResultsFilters";
  import { ID_MODE_LABELS } from "$lib/searchFilterEditor";
  import {
    idLabelKey,
    loadingIdLabel,
    type IdFilterKey,
  } from "$lib/searchFilterLabels";
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
  let text = $state(
    untrack(() => (Array.isArray(value) ? value.join(", ") : "")),
  );
  let error = $state("");
  $effect(() => {
    error = "";
    if (mode !== "ids") {
      value = mode;
      valid = true;
      return;
    }
    try {
      const ids = text.trim() ? FILTER_DEFINITIONS[field].parse([text]) : [];
      if (!Array.isArray(ids))
        throw new Error("Enter specific IDs here, or choose a mode above.");
      value = ids;
      valid = ids.length > 0;
    } catch (cause) {
      valid = false;
      error = cause instanceof Error ? cause.message : "Invalid IDs.";
    }
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
  <label for={id}>Specific IDs</label>
  <TextInput
    {id}
    name={field}
    bind:value={text}
    aria-invalid={Boolean(error)}
    aria-describedby={`${id}-hint`}
  />
  <p id={`${id}-hint`} class="hint">
    Positive integer IDs, separated by commas. Match any selected ID.
  </p>
  {#if Array.isArray(value)}
    <ul aria-label="Selected details">
      {#each value as item (item)}<li>
          {labels[idLabelKey(field, item)] ?? loadingIdLabel(item)}
        </li>{/each}
    </ul>
  {/if}
{/if}
{#if error}<p role="alert">{error}</p>{/if}

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
  ul {
    padding-left: 1.25rem;
    overflow-wrap: anywhere;
  }
  .hint {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
  }
</style>
