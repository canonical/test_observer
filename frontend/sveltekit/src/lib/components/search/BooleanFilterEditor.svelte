<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import {
    BOOLEAN_LABELS,
    type BooleanFilterKey,
  } from "$lib/searchFilterEditor";
  import { FILTER_DEFINITIONS } from "$lib/testResultsFilters";
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
  <legend class="visually-hidden">{FILTER_DEFINITIONS[field].label}</legend>
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
