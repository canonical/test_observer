<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { tick } from "svelte";
  import { Button, TextInput } from "@canonical/svelte-ds-app-launchpad";
  import { FILTER_DEFINITIONS } from "$lib/testResultsFilters";
  import {
    exactValueProblem,
    isLookupList,
    lookupValues,
    suggestionError,
    suggestionScope,
    type LookupField,
    type ValueSuggestion,
  } from "$lib/searchFilterSuggestions";
  import {
    idLabelKey,
    loadingIdLabel,
    searchFilterLabelCache,
  } from "$lib/searchFilterLabels";

  let {
    field,
    selected = $bindable(),
    // eslint-disable-next-line no-useless-assignment -- Output consumed by the editor form.
    pending = $bindable(false),
    draftFamilies = [],
    labels = {},
  }: {
    field: LookupField;
    selected: string[];
    pending?: boolean;
    draftFamilies?: string[];
    labels?: Record<string, string>;
  } = $props();
  const id = $props.id();
  const isList = $derived(isLookupList(field));
  const familyKey = $derived(
    isList ? JSON.stringify([...new Set(draftFamilies)].sort()) : "[]",
  );
  let query = $state("");
  let results = $state<ValueSuggestion[]>([]);
  let status = $state<"hint" | "loading" | "ready" | "error">("hint");
  let error = $state("");
  let exactError = $state("");
  let retry = $state(0);
  let generation = 0;
  const options = $derived(
    results.filter((item) => !selected.includes(item.value)),
  );

  $effect(() => {
    pending = Boolean(query);
  });
  $effect(() => {
    const text = query.trim();
    const kind = field;
    const families = JSON.parse(familyKey) as string[];
    const scope = suggestionScope();
    void retry;
    const current = ++generation;
    const controller = new AbortController();
    results = [];
    error = "";
    exactError = "";
    status = text.length < 2 ? "hint" : "loading";
    const live = () =>
      !controller.signal.aborted &&
      current === generation &&
      scope === suggestionScope();
    const timer =
      text.length < 2
        ? undefined
        : setTimeout(() => {
            void lookupValues(kind, text, families, controller.signal).then(
              (items) => {
                // Guard after JSON parsing too: aborted transports may still resolve.
                if (!live()) return;
                results = items;
                status = "ready";
              },
              (cause: unknown) => {
                if (!live()) return;
                status = "error";
                error = suggestionError(cause);
              },
            );
          }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  });

  function choose(item: ValueSuggestion) {
    if (item.unavailable) return;
    if (field === "issues" || field === "reviewer_ids")
      searchFilterLabelCache().prime(field, Number(item.value), item.label);
    selected = [...new Set([...selected, item.value])];
    query = "";
    document.getElementById(id)?.focus();
  }
  function exact() {
    try {
      if (isLookupList(field)) {
        const text = query.trim();
        const problem = exactValueProblem(text);
        if (problem) throw new Error(problem);
        choose({ value: text, label: text });
      } else {
        const ids = FILTER_DEFINITIONS[field].parse([query]);
        if (!Array.isArray(ids) || !ids.length)
          throw new Error("Enter positive integer IDs, separated by commas.");
        selected = [...new Set([...selected, ...ids.map(String)])];
        query = "";
        document.getElementById(id)?.focus();
      }
      exactError = "";
    } catch (cause) {
      exactError =
        cause instanceof Error ? cause.message : "Invalid exact value.";
    }
  }

  // Ordinary buttons, not a pretend combobox: Tab/Enter work natively. Arrows
  // additionally move between the input and inline results, without an overlay.
  async function navigate(event: KeyboardEvent) {
    if (event.key === "Enter" && event.target === document.getElementById(id)) {
      event.preventDefault();
      return; // Selecting a result or the explicit exact action is deliberate.
    }
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    const root = document.getElementById(`${id}-picker`);
    const buttons = Array.from(
      root?.querySelectorAll<HTMLButtonElement>(
        ".suggestions button:not(:disabled)",
      ) ?? [],
    );
    const input = document.getElementById(id);
    const targets = [input, ...buttons];
    const index = targets.indexOf(document.activeElement as HTMLElement);
    if (index < 0 || !buttons.length) return;
    event.preventDefault();
    const next = Math.max(
      0,
      Math.min(
        targets.length - 1,
        index + (event.key === "ArrowDown" ? 1 : -1),
      ),
    );
    await tick();
    targets[next]?.focus();
  }
  function selectedLabel(item: string) {
    return field === "issues" || field === "reviewer_ids"
      ? (labels[idLabelKey(field, Number(item))] ??
          loadingIdLabel(Number(item)))
      : item;
  }
</script>

<!-- Keyboard navigation is supplementary to the native input/buttons. -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div id={`${id}-picker`} onkeydown={navigate}>
  <label for={id}>Find {FILTER_DEFINITIONS[field].label}</label>
  <TextInput
    {id}
    name={field}
    type="search"
    bind:value={query}
    aria-invalid={Boolean(exactError)}
    aria-describedby={`${id}-hint${exactError ? ` ${id}-error` : ""}`}
  />
  <p id={`${id}-hint`} class="hint">
    Type at least 2 characters for suggestions. Select a result, or use the
    explicit exact-value action. Enter in this input does not save.
  </p>
  <div role="status" class="hint">
    {#if status === "hint"}Type at least 2 characters to search.
    {:else if status === "loading"}Loading suggestions…
    {:else if status === "error"}{error}
    {:else if !options.length}No unselected matches.
    {:else}Select a suggestion (up to {isList ? 50 : 10} results).{/if}
  </div>
  {#if status === "error"}<Button
      type="button"
      density="dense"
      onclick={() => retry++}>Retry suggestions</Button
    >{/if}
  <ul class="suggestions" aria-label="Value suggestions">
    {#each options as item (item.value)}
      <li>
        <Button
          type="button"
          density="dense"
          disabled={Boolean(item.unavailable)}
          onclick={() => choose(item)}>{item.label}</Button
        >
        {#if item.unavailable}<p class="hint">{item.unavailable}</p>{/if}
      </li>
    {/each}
  </ul>
  <Button type="button" density="dense" disabled={!query.trim()} onclick={exact}
    >{isList ? "Add exact value" : "Add exact IDs"}</Button
  >
  {#if query}<Button type="button" density="dense" onclick={() => (query = "")}
      >Clear input</Button
    >
    <p class="hint">
      Choose a result, add the exact value, or clear this input before saving. {isList
        ? "Add one exact value at a time; commas cannot round-trip in search links."
        : "Exact IDs must be positive integers; commas separate IDs."}
    </p>{/if}
  {#if exactError}<p id={`${id}-error`} role="alert">{exactError}</p>{/if}
  <ul class="selected" aria-label="Selected details">
    {#each selected as item (item)}
      <li>
        <span>{selectedLabel(item)}</span><Button
          type="button"
          density="dense"
          aria-label={`Remove selected ${item}`}
          onclick={() => (selected = selected.filter((v) => v !== item))}
          >Remove</Button
        >
      </li>
    {/each}
  </ul>
  {#if !selected.length}<p class="hint">No selected values.</p>{/if}
</div>

<style>
  label {
    display: block;
    margin-bottom: 0.5rem;
  }
  ul {
    list-style: none;
    padding: 0;
    margin: 0.5rem 0;
    overflow-wrap: anywhere;
  }
  li {
    margin: 0.4rem 0;
  }
  .suggestions,
  .selected {
    max-height: min(12rem, 25dvh);
    overflow: auto;
  }
  .suggestions :global(button) {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
    white-space: normal;
    overflow-wrap: anywhere;
  }
  .selected li {
    display: flex;
    align-items: start;
    gap: 0.5rem;
  }
  .selected span {
    flex: 1;
    min-width: 0;
  }
  .selected :global(button) {
    flex-shrink: 0;
  }
  .hint {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
    margin: 0.5rem 0;
  }
</style>
