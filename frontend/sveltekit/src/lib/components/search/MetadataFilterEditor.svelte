<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { tick } from "svelte";
  import { Button, TextInput } from "@canonical/svelte-ds-app-launchpad";
  import {
    validateMetadataPart,
    type MetadataCondition,
  } from "$lib/testResultsFilters";
  import {
    metadataSuggestions,
    suggestionScope,
    suggestionError,
    type KnownMetadata,
  } from "$lib/searchFilterSuggestions";
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
  let known = $state<KnownMetadata>({});
  let loading = $state(false);
  let lookupError = $state("");
  let retry = $state(0);
  let categoryFocused = $state(false);
  let valueFocused = $state(false);
  let categoryActive = $state(-1);
  let valueActive = $state(-1);
  let generation = 0;
  const allCategories = $derived(Object.keys(known));
  const matchingCategories = $derived(
    allCategories.filter((key) =>
      key.toLowerCase().includes(category.toLowerCase()),
    ),
  );
  const categories = $derived(matchingCategories.slice(0, 50));
  const allValues = $derived(
    Object.hasOwn(known, category) ? known[category] : [],
  );
  const matchingValues = $derived(
    allValues.filter((item) => item.toLowerCase().includes(text.toLowerCase())),
  );
  const values = $derived(matchingValues.slice(0, 50));
  const showCategories = $derived(categoryFocused && categories.length > 0);
  const showValues = $derived(valueFocused && values.length > 0);
  const categoryActiveDescendant = $derived(
    showCategories && categoryActive >= 0 && categoryActive < categories.length
      ? `${id}-category-option-${categoryActive}`
      : undefined,
  );
  const valueActiveDescendant = $derived(
    showValues && valueActive >= 0 && valueActive < values.length
      ? `${id}-value-option-${valueActive}`
      : undefined,
  );

  $effect(() => {
    const scope = suggestionScope();
    void retry;
    const current = ++generation;
    const controller = new AbortController();
    known = {};
    loading = true;
    lookupError = "";
    const live = () =>
      !controller.signal.aborted &&
      current === generation &&
      scope === suggestionScope();
    void metadataSuggestions.load(scope, controller.signal).then(
      (map) => {
        if (!live()) return;
        known = map;
        loading = false;
      },
      (cause: unknown) => {
        if (!live()) return;
        loading = false;
        lookupError = suggestionError(cause);
      },
    );
    return () => controller.abort();
  });
  $effect(() => {
    valid = value.length > 0 && !category && !text;
  });
  $effect(() => {
    const active = categoryActive;
    if (active >= 0) {
      document
        .getElementById(`${id}-category-option-${active}`)
        ?.scrollIntoView?.({ block: "nearest" });
    }
  });
  $effect(() => {
    const active = valueActive;
    if (active >= 0) {
      document
        .getElementById(`${id}-value-option-${active}`)
        ?.scrollIntoView?.({ block: "nearest" });
    }
  });

  function changeCategory(next: string) {
    if (next !== category) {
      category = next;
      // Text entered for one category must not silently become a value in another.
      text = "";
      valueActive = -1;
    }
    categoryActive = -1;
    error = "";
  }

  async function selectCategory(item: string) {
    changeCategory(item);
    categoryFocused = false;
    // Let the field/list state settle before moving focus, so focusin on Value
    // reliably reopens its known options rather than being cleared by the
    // category field's focusout handler.
    await tick();
    document.getElementById(`${id}-value`)?.focus();
  }

  function selectValue(item: string) {
    text = item;
    valueFocused = false;
    valueActive = -1;
    error = "";
  }

  function suggestionKeydown(
    event: KeyboardEvent,
    count: number,
    active: number,
    setActive: (index: number) => void,
    select: (index: number) => void,
  ) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      if (!count) return;
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      setActive(
        active < 0
          ? direction > 0
            ? 0
            : count - 1
          : (active + direction + count) % count,
      );
    } else if (event.key === "Enter") {
      // Enter in either query field selects an active option; it never submits
      // the surrounding editor or silently commits typed text.
      event.preventDefault();
      if (active >= 0 && active < count) select(active);
    }
  }

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
      categoryFocused = false;
      valueFocused = false;
      categoryActive = -1;
      valueActive = -1;
      error = "";
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

<p class="hint">AND across categories · OR within each category</p>
<ul aria-label="Metadata conditions">
  {#each value as condition (condition.category)}
    <li>
      <strong>{JSON.stringify(condition.category)}</strong>
      <ul>
        {#each condition.values as item (item)}
          <li>
            <span>{JSON.stringify(item)}</span>
            <Button
              type="button"
              density="dense"
              aria-label={`Remove metadata ${JSON.stringify(condition.category)} = ${JSON.stringify(item)}`}
              onclick={() => remove(condition.category, item)}
              >Remove pair</Button
            >
          </li>
        {/each}
      </ul>
    </li>
  {/each}
</ul>
<div
  class="picker-field"
  onfocusin={() => (categoryFocused = true)}
  onfocusout={(event) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      categoryFocused = false;
      categoryActive = -1;
    }
  }}
>
  <label for={`${id}-category`}>Category</label>
  <TextInput
    id={`${id}-category`}
    name="metadata-category"
    placeholder="Select or search a category"
    role="combobox"
    aria-autocomplete="list"
    aria-controls={showCategories ? `${id}-categories` : undefined}
    aria-expanded={showCategories}
    aria-activedescendant={categoryActiveDescendant}
    value={category}
    oninput={(event) => {
      categoryFocused = true;
      changeCategory(event.currentTarget.value);
    }}
    onkeydown={(event) =>
      suggestionKeydown(
        event,
        categories.length,
        categoryActive,
        (index) => (categoryActive = index),
        (index) => selectCategory(categories[index]),
      )}
  />
  {#if showCategories}
    <div class="option-heading">Known categories</div>
    <ul
      id={`${id}-categories`}
      class="suggestions"
      role="listbox"
      aria-label="Known categories"
    >
      {#each categories as item, index (item)}
        <li
          id={`${id}-category-option-${index}`}
          role="option"
          aria-selected={categoryActive === index}
          tabindex="-1"
          onpointerdown={(event) => event.preventDefault()}
          onclick={() => selectCategory(item)}
          onkeydown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              selectCategory(item);
            }
          }}
        >
          {item}
        </li>
      {/each}
    </ul>
    {#if matchingCategories.length > categories.length}
      <p class="count">
        Showing {categories.length} of {matchingCategories.length}
      </p>
    {/if}
  {/if}
</div>
<div
  class="picker-field"
  onfocusin={() => (valueFocused = true)}
  onfocusout={(event) => {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      valueFocused = false;
      valueActive = -1;
    }
  }}
>
  <label for={`${id}-value`}
    >{category ? `Value for ${category}` : "Value"}</label
  >
  <TextInput
    id={`${id}-value`}
    name="metadata-value"
    placeholder="Select or search a value"
    disabled={!category}
    role="combobox"
    aria-autocomplete="list"
    aria-controls={showValues ? `${id}-values` : undefined}
    aria-expanded={showValues}
    aria-activedescendant={valueActiveDescendant}
    bind:value={text}
    oninput={() => {
      valueFocused = true;
      valueActive = -1;
      error = "";
    }}
    onkeydown={(event) =>
      suggestionKeydown(
        event,
        values.length,
        valueActive,
        (index) => (valueActive = index),
        (index) => selectValue(values[index]),
      )}
  />
  {#if showValues}
    <div class="option-heading">Known values for {category}</div>
    <ul
      id={`${id}-values`}
      class="suggestions"
      role="listbox"
      aria-label={`Known values for ${category}`}
    >
      {#each values as item, index (item)}
        <li
          id={`${id}-value-option-${index}`}
          role="option"
          aria-selected={valueActive === index}
          tabindex="-1"
          onpointerdown={(event) => event.preventDefault()}
          onclick={() => selectValue(item)}
          onkeydown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              selectValue(item);
            }
          }}
        >
          {item}
        </li>
      {/each}
    </ul>
    {#if matchingValues.length > values.length}
      <p class="count">Showing {values.length} of {matchingValues.length}</p>
    {/if}
  {/if}
</div>
<p class="hint status" role="status">
  {#if loading}Loading metadata…
  {:else if lookupError}{lookupError}
  {:else if categoryFocused && !matchingCategories.length}No matching
    categories.
  {:else if category && !matchingValues.length}No known values for this
    category.
  {:else if !Object.keys(known).length}No known metadata. Exact values can still
    be entered.{/if}
</p>
{#if lookupError}<Button type="button" density="dense" onclick={() => retry++}
    >Retry suggestions</Button
  >{/if}
<p class="hint">1–200 characters per category and value.</p>
<Button type="button" density="dense" onclick={add}>Add pair</Button>
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
  .hint,
  .count {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
  }
  .hint {
    margin: 0.5rem 0;
  }
  .status {
    min-height: 1.25em;
  }
  .picker-field {
    min-width: 0;
  }
  .option-heading {
    margin: 0.35rem 0;
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
  }
  .suggestions {
    max-height: min(12rem, 30dvh);
    overflow: auto;
    margin: 0.25rem 0 0.5rem;
    padding: 0.25rem;
    list-style: none;
    border: 1px solid var(--lp-color-border-default);
    border-radius: 0.25rem;
  }
  .suggestions li[role="option"] {
    margin: 0;
    padding: 0.375rem 0.5rem;
    border-radius: 0.2rem;
    overflow-wrap: anywhere;
    cursor: pointer;
  }
  .suggestions li[role="option"]:hover,
  .suggestions li[role="option"][aria-selected="true"] {
    background: var(--lp-color-background-hover);
  }
  .suggestions li[role="option"]:focus-visible {
    outline: 2px solid var(--lp-color-border-focus);
    outline-offset: -2px;
  }
</style>
