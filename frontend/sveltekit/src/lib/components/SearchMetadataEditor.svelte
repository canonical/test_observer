<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<script lang="ts">
  import { silentApi } from "$lib/api/client";
  import type { SearchMetadataCondition } from "$lib/searchPageFilters";

  let {
    value = $bindable(),
    onedit,
  }: {
    value: SearchMetadataCondition[];
    onedit: () => void;
  } = $props();
  const id = $props.id();
  let category = $state("");
  let metadataValue = $state("");
  let known = $state<Record<string, string[]>>({});
  let suggestionStatus = $state<"idle" | "loading" | "ready" | "error">("idle");
  let enabled = $state(false);
  let error = $state("");

  $effect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    suggestionStatus = "loading";
    void silentApi<unknown>("execution-metadata", {
      signal: controller.signal,
    }).then(
      (response) => {
        if (controller.signal.aborted) return;
        if (
          !response ||
          typeof response !== "object" ||
          Array.isArray(response)
        ) {
          suggestionStatus = "error";
          return;
        }
        const map = (response as Record<string, unknown>).execution_metadata;
        if (!map || typeof map !== "object" || Array.isArray(map)) {
          suggestionStatus = "error";
          return;
        }
        known = Object.fromEntries(
          Object.entries(map as Record<string, unknown>)
            .filter(
              ([, values]) =>
                Array.isArray(values) &&
                values.every((item) => typeof item === "string"),
            )
            .map(([key, values]) => [key, [...new Set(values as string[])]]),
        );
        suggestionStatus = "ready";
      },
      () => {
        if (!controller.signal.aborted) suggestionStatus = "error";
      },
    );
    return () => controller.abort();
  });

  const categories = $derived(
    Object.keys(known)
      .filter((item) => item.toLowerCase().includes(category.toLowerCase()))
      .slice(0, 50),
  );
  const values = $derived(
    (known[category] ?? [])
      .filter((item) =>
        item.toLowerCase().includes(metadataValue.toLowerCase()),
      )
      .slice(0, 50),
  );

  function add() {
    const categoryLength = Array.from(category).length;
    const valueLength = Array.from(metadataValue).length;
    if (
      categoryLength < 1 ||
      categoryLength > 200 ||
      valueLength < 1 ||
      valueLength > 200
    ) {
      error = "Category and value must each contain 1–200 characters.";
      return;
    }
    const existing = value.find((item) => item.category === category);
    value = existing
      ? value.map((item) =>
          item === existing
            ? { ...item, values: [...new Set([...item.values, metadataValue])] }
            : item,
        )
      : [...value, { category, values: [metadataValue] }];
    onedit();
    category = "";
    metadataValue = "";
    error = "";
  }

  function removePair(targetCategory: string, targetValue: string) {
    value = value
      .map((item) =>
        item.category === targetCategory
          ? {
              ...item,
              values: item.values.filter(
                (itemValue) => itemValue !== targetValue,
              ),
            }
          : item,
      )
      .filter((item) => item.values.length > 0);
    onedit();
  }
</script>

<p class="hint">
  AND across categories · OR among values within each category.
</p>
<ul aria-label="Execution metadata conditions">
  {#each value as condition (condition.category)}
    <li>
      <strong>{JSON.stringify(condition.category)}</strong>
      <ul>
        {#each condition.values as item (item)}
          <li>
            <span>{JSON.stringify(item)}</span>
            <button
              type="button"
              aria-label={`Remove metadata ${JSON.stringify(condition.category)} = ${JSON.stringify(item)}`}
              onclick={() => removePair(condition.category, item)}
              >Remove</button
            >
          </li>
        {/each}
      </ul>
    </li>
  {/each}
</ul>
<div class="metadata-entry">
  <label for={`${id}-category`}>Category</label>
  <input
    id={`${id}-category`}
    name="metadata-category"
    bind:value={category}
    list={`${id}-categories`}
    autocomplete="off"
    onfocus={() => (enabled = true)}
  />
  <datalist id={`${id}-categories`}>
    {#each categories as item (item)}<option value={item}></option>{/each}
  </datalist>
  <label for={`${id}-value`}>Value</label>
  <input
    id={`${id}-value`}
    name="metadata-value"
    bind:value={metadataValue}
    list={`${id}-values`}
    autocomplete="off"
  />
  <datalist id={`${id}-values`}>
    {#each values as item (item)}<option value={item}></option>{/each}
  </datalist>
  <p class="hint" role="status">
    {suggestionStatus === "idle"
      ? "Focus to load metadata suggestions, or enter exact values."
      : suggestionStatus === "loading"
        ? "Loading metadata suggestions…"
        : suggestionStatus === "error"
          ? "Metadata suggestions unavailable. Enter exact category and value to continue."
          : Object.keys(known).length === 0
            ? "No metadata suggestions. Exact category and value entry is available."
            : "Choose known values or enter exact values."}
  </p>
  <p class="hint">1–200 Unicode characters per category and value.</p>
  <button type="button" onclick={add}>Add pair</button>
</div>
{#if error}<p role="alert">{error}</p>{/if}

<style>
  .metadata-entry {
    display: grid;
    gap: 0.25rem;
  }
  label {
    font-size: 0.8125rem;
  }
  input,
  button {
    box-sizing: border-box;
    min-height: 2rem;
    border: 1px solid var(--lp-color-border-default, #ccc);
    border-radius: 0.25rem;
    color: var(--lp-color-text-default, #222);
    background: var(--lp-color-background-default, #fff);
    font: inherit;
  }
  input {
    width: 100%;
    padding: 0.25rem 0.5rem;
    appearance: none;
  }
  button {
    appearance: none;
    cursor: pointer;
    padding: 0.25rem 0.625rem;
  }
  button:focus-visible,
  input:focus-visible {
    outline: 2px solid var(--lp-color-brand-default, #06c);
    outline-offset: 1px;
  }
  ul {
    padding-left: 1.25rem;
    overflow-wrap: anywhere;
  }
  li {
    margin: 0.35rem 0;
  }
  li span {
    margin-right: 0.5rem;
  }
  .hint {
    margin: 0.25rem 0;
    color: var(--lp-color-text-muted, #666);
    font-size: 0.8rem;
  }
</style>
