<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Button, TextInput } from "@canonical/svelte-ds-app-launchpad";
  import {
    validateMetadataPart,
    type MetadataCondition,
  } from "$lib/testResultsFilters";
  let {
    value = $bindable(),
    // eslint-disable-next-line no-useless-assignment -- Bindable validation output is read by the owning form.
    valid = $bindable(false),
  }: {
    value: MetadataCondition[];
    valid?: boolean;
  } = $props();
  const id = $props.id();
  let category = $state("");
  let text = $state("");
  let error = $state("");
  $effect(() => {
    valid = value.length > 0 && !category && !text;
  });
  function add() {
    try {
      validateMetadataPart(category);
      validateMetadataPart(text);
      const existing = value.find((item) => item.category === category);
      value = existing
        ? value.map((item) =>
            item === existing
              ? { category, values: [...new Set([...item.values, text])] }
              : item,
          )
        : [...value, { category, values: [text] }];
      category = "";
      text = "";
      error = "";
      document.getElementById(`${id}-category`)?.focus();
    } catch (cause) {
      error = cause instanceof Error ? cause.message : "Invalid metadata pair.";
    }
  }
  function remove(category: string, text: string) {
    value = value
      .map((item) =>
        item.category === category
          ? { ...item, values: item.values.filter((v) => v !== text) }
          : item,
      )
      .filter((item) => item.values.length);
  }
</script>

<p class="hint">
  Match all categories (AND). Within each category, match any value (OR).
  Punctuation, spaces and Unicode are exact; commas and colons are not
  separators.
</p>
<ul aria-label="Metadata conditions">
  {#each value as condition (condition.category)}
    <li>
      <strong>{JSON.stringify(condition.category)}</strong>
      <ul>
        {#each condition.values as item (item)}<li>
            <span>{JSON.stringify(item)}</span><Button
              type="button"
              density="dense"
              aria-label={`Remove metadata ${JSON.stringify(condition.category)} = ${JSON.stringify(item)}`}
              onclick={() => remove(condition.category, item)}
              >Remove pair</Button
            >
          </li>{/each}
      </ul>
    </li>
  {/each}
</ul>
<label for={`${id}-category`}>Category</label>
<TextInput
  id={`${id}-category`}
  name="metadata-category"
  bind:value={category}
/>
<label for={`${id}-value`}>Value</label>
<TextInput id={`${id}-value`} name="metadata-value" bind:value={text} />
<p class="hint">Each category and value must contain 1–200 characters.</p>
<Button type="button" density="dense" onclick={add}>Add pair</Button>
{#if category || text}<p class="hint">
    Add this pair, or empty both inputs before saving.
  </p>{/if}
{#if error}<p role="alert">{error}</p>{/if}

<style>
  label {
    display: block;
    margin: 0.75rem 0 0.5rem;
  }
  ul {
    padding-left: 1.25rem;
    overflow-wrap: anywhere;
  }
  li {
    margin: 0.5rem 0;
  }
  li span {
    margin-right: 0.5rem;
  }
  .hint {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
  }
</style>
