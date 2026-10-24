<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { untrack } from "svelte";
  import { TextInput } from "@canonical/svelte-ds-app-launchpad";
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
    // eslint-disable-next-line no-useless-assignment -- Bindable validation output is read by the owning form.
    valid = $bindable(false),
  }: {
    field: InstantFilterKey;
    value: IsoInstant | null;
    other: IsoInstant | null;
    valid?: boolean;
  } = $props();
  const id = $props.id();
  let text = $state(untrack(() => value ?? ""));
  // This display-only projection can truncate fractions. It is NEVER applied
  // unless the user actually changes the picker; exact restored text stays intact.
  const picker = $derived.by(() => {
    try {
      parseIsoInstant(text);
      return new Date(text).toISOString().slice(0, 19);
    } catch {
      return "";
    }
  });
  let error = $state("");
  $effect(() => {
    error = "";
    valid = false;
    if (!text) return;
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
    const input = event.currentTarget as HTMLInputElement;
    const picked = input.value;
    text = picked ? `${picked.length === 16 ? `${picked}:00` : picked}Z` : "";
  }
</script>

<p class="hint">
  Inclusive {field === "from_date" ? "lower" : "upper"} bound on result creation time.
  The other bound is optional.
</p>
<label for={`${id}-picker`}>Date and time (UTC)</label>
<input
  id={`${id}-picker`}
  name={`${field}-picker`}
  type="datetime-local"
  step="1"
  value={picker}
  oninput={updatePicker}
  aria-describedby={`${id}-hint`}
/>
<p id={`${id}-hint`} class="hint">
  Changing the UTC picker selects a new timestamp at second precision. Unchanged
  restored timestamps retain their original timezone and fractional precision.
</p>
<label for={id}>Exact timestamp (explicit timezone)</label>
<TextInput
  {id}
  name={field}
  bind:value={text}
  aria-invalid={Boolean(error)}
  aria-describedby={`${id}-format`}
/>
<p id={`${id}-format`} class="hint">
  ISO timestamp with Z or ±HH:MM; up to six fractional digits (microseconds).
  Example: 2026-01-01T12:00:00.123456+01:00.
</p>
{#if other}<p class="hint">
    {field === "from_date" ? "Until" : "From"}: {other}
  </p>{/if}
{#if error}<p role="alert">{error}</p>{/if}

<style>
  label {
    display: block;
    margin: 0.75rem 0 0.5rem;
  }
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
</style>
