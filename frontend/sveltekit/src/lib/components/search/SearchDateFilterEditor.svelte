<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import {
    compareInstants,
    parseIsoInstant,
    type IsoInstant,
  } from "$lib/testResultsFilters";
  import type { InstantFilterKey } from "$lib/searchFilterEditor";

  let {
    field,
    value = $bindable(),
    other,
    boundLabel,
    compactPresentation = false,
    utcNoteId,
    allowEmpty = false,
    disabled = false,
    filterAttribute,
    ontextchange,
    // eslint-disable-next-line no-useless-assignment -- Bindable validation output is read by the owning form.
    valid = $bindable(false),
    text = $bindable(untrack(() => value ?? "")),
  }: {
    field: InstantFilterKey;
    value: IsoInstant | null;
    other: IsoInstant | null;
    boundLabel?: string;
    compactPresentation?: boolean;
    utcNoteId?: string;
    allowEmpty?: boolean;
    disabled?: boolean;
    filterAttribute?: string;
    ontextchange?: (text: string) => void;
    valid?: boolean;
    /** Raw URL value retained until the user explicitly changes this picker. */
    text?: string;
  } = $props();
  const id = $props.id();
  const accessibleBoundLabel = $derived(
    field === "from_date" ? "Created — From (UTC)" : "Created — To (UTC)",
  );

  // An offset or fractional instant has no honest representation in this
  // seconds-only UTC picker. Keep it raw for query serialization and show no
  // projected/local-time value.
  const picker = $derived.by(() => {
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(text)) return "";
    try {
      parseIsoInstant(text);
      return text.slice(0, -1);
    } catch {
      return "";
    }
  });
  const pickerCannotRepresentValue = $derived.by(() => {
    if (!text) return false;
    try {
      parseIsoInstant(text);
      return picker === "";
    } catch {
      return false;
    }
  });

  let error = $state("");
  $effect(() => {
    error = "";
    if (!text) {
      value = null;
      valid = allowEmpty;
      return;
    }
    valid = false;
    try {
      const instant = parseIsoInstant(text);
      if (
        other &&
        (field === "from_date"
          ? compareInstants(instant, other) > 0
          : compareInstants(other, instant) > 0)
      )
        throw new Error("From must not be after Until (inclusive bounds).");
      value = instant;
      valid = true;
    } catch (cause) {
      error = cause instanceof Error ? cause.message : "Invalid timestamp.";
    }
  });

  function updatePicker(event: Event) {
    const picked = (event.currentTarget as HTMLInputElement).value;
    updateText(
      picked ? `${picked.length === 16 ? `${picked}:00` : picked}Z` : "",
    );
  }

  function updateText(next: string) {
    text = next;
    ontextchange?.(next);
  }
</script>

{#if boundLabel}
  {#if compactPresentation}
    <label for={`${id}-picker`} class="bound-label compact-bound-label">
      {boundLabel}
    </label>
  {:else}
    <h3 id={`${id}-bound`} class="bound-label">{boundLabel}</h3>
  {/if}
{/if}
<input
  id={`${id}-picker`}
  name={`${field}-picker`}
  data-search-grid-filter-picker={filterAttribute}
  data-search-grid-filter={filterAttribute}
  type="datetime-local"
  step="1"
  value={picker}
  {disabled}
  aria-invalid={Boolean(error)}
  aria-label={compactPresentation || !boundLabel
    ? accessibleBoundLabel
    : undefined}
  aria-labelledby={boundLabel && !compactPresentation
    ? `${id}-bound`
    : undefined}
  aria-describedby={compactPresentation ? utcNoteId : `${id}-hint`}
  oninput={updatePicker}
/>
{#if !compactPresentation}
  <p id={`${id}-hint`} class="hint">
    Inclusive {field === "from_date" ? "lower" : "upper"} bound on result creation time.
    Picker values are UTC and include whole seconds; clearing this picker removes this
    bound.
  </p>
{/if}
{#if pickerCannotRepresentValue}
  <p class="hint" data-utc-picker-note>
    This saved time is not shown in the picker. Select a new UTC time or clear
    this bound.
  </p>
{/if}
{#if other && !compactPresentation}<p class="hint">
    {field === "from_date" ? "Until" : "From"}: {other}
  </p>{/if}
{#if error}<p role="alert">{error}</p>{/if}

<style>
  input {
    width: 100%;
    box-sizing: border-box;
    min-width: 0;
    padding: 0.5rem;
    color: inherit;
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-default);
  }
  .hint {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
    overflow-wrap: anywhere;
  }
  .bound-label {
    margin: 0.75rem 0 0;
    font-weight: 600;
  }
  .compact-bound-label {
    display: block;
    margin: 0;
    font: inherit;
  }
  .bound-label + input {
    margin-top: 0.5rem;
  }
</style>
