<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import {
    BOOLEAN_LABELS,
    type BooleanFilterKey,
  } from "$lib/searchFilterEditor";
  let {
    field,
    value = $bindable(),
    // eslint-disable-next-line no-useless-assignment -- Bindable validation output is read by the owning form.
    valid = $bindable(false),
  }: {
    field: BooleanFilterKey;
    value: boolean | null;
    valid?: boolean;
  } = $props();
  const id = $props.id();
  $effect(() => {
    valid = value !== null;
  });
</script>

<fieldset>
  <legend>Choose one</legend>
  {#each [false, true] as option (option)}
    <label
      ><input
        type="radio"
        name={id}
        bind:group={value}
        value={option}
      />{BOOLEAN_LABELS[field][Number(option)]}</label
    >
  {/each}
</fieldset>

<style>
  fieldset {
    border: 0;
    padding: 0;
    margin: 0 0 1rem;
  }
  label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.75rem 0;
  }
</style>
