<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { tick } from "svelte";
  import {
    Button,
    Chip,
    Popover,
    TextInput,
  } from "@canonical/svelte-ds-app-launchpad";
  import { CloseIcon } from "@canonical/svelte-icons";
  import type { Family } from "$lib/types";
  import {
    EDITABLE_SEARCH_FILTERS,
    FILTER_DEFINITIONS,
    clearFilter,
    cloneFilters,
    emptyFilters,
    filterIsActive,
    type EditableSearchFilter,
    type SearchFilters,
  } from "$lib/testResultsSearch";
  import FilterEditor from "./FilterEditor.svelte";
  import { filterValueLabels } from "$lib/searchFilterEditor";
  import {
    idLabelKey,
    loadingIdLabel,
    searchFilterLabelCache,
    type IdFilterKey,
  } from "$lib/searchFilterLabels";
  import {
    metadataSuggestions,
    suggestionScope,
  } from "$lib/searchFilterSuggestions";

  let {
    filters = $bindable(),
    families,
    disabled = false,
    invalidFields = [],
    onedit,
  }: {
    filters: SearchFilters;
    families: Family[];
    disabled?: boolean;
    invalidFields?: EditableSearchFilter[];
    onedit?: (key: EditableSearchFilter) => void;
  } = $props();

  const label = (key: EditableSearchFilter) => FILTER_DEFINITIONS[key].label;
  type Source = EditableSearchFilter | "add";
  const id = $props.id();
  let active = $state<Source | null>(null);
  let opened = $state<Source | null>(null);
  let placement = $state("visibility: hidden;");
  let field = $state<EditableSearchFilter | null>(null);
  let query = $state("");
  let editorDraft = $state(emptyFilters());
  let valid = $state(false);
  let idLabels = $state<Record<string, string>>({});
  let labelGeneration = 0;
  let addButton: HTMLButtonElement | undefined = $state();
  $effect(() => {
    // Invalidate even while Metadata is closed (including logout/login as the
    // same profile). No private options survive a different session context.
    metadataSuggestions.setScope(suggestionScope());
  });
  const available = $derived(
    EDITABLE_SEARCH_FILTERS.filter(
      (key) =>
        !isActive(key) &&
        label(key).toLowerCase().includes(query.trim().toLowerCase()),
    ),
  );
  const isActive = (key: EditableSearchFilter) =>
    filterIsActive(key, filters) || invalidFields.includes(key);

  const hydrationTargets = $derived.by(() => {
    const targets: [IdFilterKey, number][] = [];
    for (const key of ["issues", "reviewer_ids"] as const) {
      const confirmed = filters[key];
      const editing = field === key ? editorDraft[key] : [];
      const ids = [
        ...new Set([
          ...(Array.isArray(confirmed) ? confirmed : []),
          ...(Array.isArray(editing) ? editing : []),
        ]),
      ];
      targets.push(...ids.map((id): [IdFilterKey, number] => [key, id]));
    }
    // Identity, not array allocation/editor opening, controls request lifetime.
    return JSON.stringify(targets);
  });
  $effect(() => {
    const cache = searchFilterLabelCache();
    const generation = ++labelGeneration;
    const controller = new AbortController();
    const targets = JSON.parse(hydrationTargets) as [IdFilterKey, number][];
    idLabels = Object.fromEntries(
      targets.map(([key, id]) => [
        idLabelKey(key, id),
        cache.peek(key, id) ?? loadingIdLabel(id),
      ]),
    );
    for (const [key, id] of targets) {
      void cache.load(key, id, controller.signal).then((value) => {
        if (
          value !== undefined &&
          !controller.signal.aborted &&
          generation === labelGeneration
        )
          idLabels[idLabelKey(key, id)] = value;
      });
    }
    return () => controller.abort();
  });

  function valueLabels(key: EditableSearchFilter) {
    return invalidFields.includes(key)
      ? ["Invalid URL value"]
      : filterValueLabels(key, filters, families, idLabels);
  }

  function summary(key: EditableSearchFilter) {
    const names = valueLabels(key);
    const first = names[0];
    return names.length > 1 ? `${first} +${names.length - 1}` : first;
  }

  function fullLabel(key: EditableSearchFilter) {
    return `${label(key)}: ${valueLabels(key).join(", ")}`;
  }

  async function focusPanel(source: Source) {
    await tick();
    if (active !== source) return;
    const popover = document.getElementById(`${id}-${source}`);
    if (!popover?.matches(":popover-open")) return;
    positionPanel(source);
    await tick();
    if (active === source && popover.matches(":popover-open"))
      popover
        .querySelector<HTMLElement>("input, button")
        ?.focus({ preventScroll: true });
  }

  function positionPanel(source: Source) {
    const popover = document.getElementById(`${id}-${source}`);
    const trigger = document.getElementById(`${id}-trigger-${source}`);
    const panel = popover?.querySelector<HTMLElement>(".panel");
    if (
      active !== source ||
      !popover?.matches(":popover-open") ||
      !trigger ||
      !panel
    )
      return;

    // Pragma owns native top-layer/dismissal semantics. Measure placement against
    // the *visible viewport*, not CSS anchor positioning's taller document area.
    const viewport = window.visualViewport;
    const margin = 16;
    const gap = 4;
    const leftEdge = (viewport?.offsetLeft ?? 0) + margin;
    const topEdge = (viewport?.offsetTop ?? 0) + margin;
    const rightEdge =
      leftEdge + (viewport?.width ?? window.innerWidth) - 2 * margin;
    const bottomEdge =
      topEdge + (viewport?.height ?? window.innerHeight) - 2 * margin;
    const anchor = trigger.getBoundingClientRect();
    const content = panel.getBoundingClientRect();
    const below = Math.max(
      0,
      bottomEdge - Math.max(topEdge, anchor.bottom + gap),
    );
    const above = Math.max(0, Math.min(bottomEdge, anchor.top - gap) - topEdge);
    const useBelow = content.height <= below || below >= above;
    const maxHeight = useBelow ? below : above;
    const height = Math.min(content.height, maxHeight);
    const width = Math.min(
      popover.getBoundingClientRect().width,
      rightEdge - leftEdge,
    );
    const left = Math.max(leftEdge, Math.min(anchor.left, rightEdge - width));
    const preferredTop = useBelow
      ? anchor.bottom + gap
      : anchor.top - gap - height;
    const top = Math.max(topEdge, Math.min(preferredTop, bottomEdge - height));
    placement = `left: ${left}px; top: ${top}px; max-height: ${maxHeight}px; max-width: ${rightEdge - leftEdge}px;`;
  }

  $effect(() => {
    const source = opened;
    if (!source) return;
    const popover = document.getElementById(`${id}-${source}`);
    const trigger = document.getElementById(`${id}-trigger-${source}`);
    const panel = popover?.querySelector(".panel");
    const update = () => positionPanel(source);
    const observer = new ResizeObserver(update);
    if (trigger) observer.observe(trigger);
    if (panel) observer.observe(panel);
    window.addEventListener("resize", update);
    document.addEventListener("scroll", update, true);
    window.visualViewport?.addEventListener("resize", update);
    window.visualViewport?.addEventListener("scroll", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
      document.removeEventListener("scroll", update, true);
      window.visualViewport?.removeEventListener("resize", update);
      window.visualViewport?.removeEventListener("scroll", update);
    };
  });

  function afterToggle(event: ToggleEvent, source: Source) {
    if (event.newState !== "open" || active !== source) return;
    opened = source;
    // beforetoggle can flush Svelte updates while the native popover is still
    // closed, where browsers ignore focus(). The toggle event is post-opening.
    void focusPanel(source);
  }

  function start(key: EditableSearchFilter, source: Source) {
    field = key;
    editorDraft = cloneFilters(filters);
    valid = false;
    if (opened === source) void focusPanel(source);
  }

  function beforeToggle(event: ToggleEvent, source: Source) {
    if (event.newState === "open") {
      active = source;
      placement = "visibility: hidden;";
      query = "";
      field = null;
      if (source !== "add") start(source, source);
    } else if (active === source) {
      // Native light dismissal (outside click/Escape) never confirms an edit.
      active = null;
      opened = null;
      field = null;
    }
  }

  function close(source: Source, returnFocus = true) {
    document.getElementById(`${id}-${source}`)?.hidePopover();
    if (returnFocus)
      document.getElementById(`${id}-trigger-${source}`)?.focus();
  }

  async function confirm(event: SubmitEvent, source: Source) {
    event.preventDefault();
    if (!field || !valid || !filterIsActive(field, editorDraft)) return;
    const key = field;
    const next = cloneFilters(editorDraft);
    close(source, false);
    filters = next;
    onedit?.(key);
    await tick();
    document.getElementById(`${id}-trigger-${key}`)?.focus();
  }

  async function remove(key: EditableSearchFilter) {
    if (active) close(active, false);
    filters = clearFilter(filters, key);
    onedit?.(key);
    await tick();
    addButton?.focus();
  }

  function escape(event: KeyboardEvent, source: Source) {
    if (event.key !== "Escape") return;
    event.preventDefault();
    event.stopPropagation();
    close(source);
  }
</script>

{#snippet condition(source: Source)}
  <Popover
    id={`${id}-${source}`}
    class="condition-popover"
    role="dialog"
    aria-label={field && active === source
      ? `Edit ${label(field)}`
      : "Add filter"}
    style={`position: fixed; position-area: none; inset: auto; margin: 0; ${placement}`}
    onbeforetoggle={(event) => beforeToggle(event, source)}
    ontoggle={(event) => afterToggle(event, source)}
    onkeydown={(event) => escape(event, source)}
  >
    {#snippet trigger(triggerProps, open)}
      {#if source === "add"}
        <Button
          {...triggerProps}
          id={`${id}-trigger-add`}
          bind:ref={addButton}
          type="button"
          density="dense"
          {disabled}
          aria-haspopup="dialog"
          aria-expanded={open}>+ Add filter</Button
        >
      {:else}
        <button
          {...triggerProps}
          id={`${id}-trigger-${source}`}
          class="chip-trigger"
          type="button"
          {disabled}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-label={`Edit ${fullLabel(source)}`}
          title={fullLabel(source)}
        >
          <Chip
            lead={label(source)}
            value={summary(source)}
            readonly
            density="dense"
          />
        </button>
      {/if}
    {/snippet}
    {#if active === source}
      <div class="panel">
        {#if field}
          <form
            aria-label={`Edit ${label(field)}`}
            onsubmit={(event) => confirm(event, source)}
          >
            <h2>{label(field)}</h2>
            {#if invalidFields.includes(field)}
              <p class="hint">
                The original URL value is invalid. Save an explicit replacement
                or remove this filter. Unrelated edits preserve it.
              </p>
            {/if}
            {#key field}
              <FilterEditor
                {field}
                bind:filters={editorDraft}
                bind:valid
                {families}
                labels={idLabels}
              />
            {/key}
            {#if !valid}
              <p class="hint">
                {isActive(field)
                  ? "Select a value to save, or remove this filter."
                  : "Choose at least one value to add this filter."}
              </p>
            {/if}
            <div class="editor-actions">
              <Button
                type="submit"
                severity="brand"
                density="dense"
                disabled={!valid}
                >{source === "add" ? "Add filter" : "Save changes"}</Button
              >
              <Button
                type="button"
                density="dense"
                onclick={() => close(source)}>Cancel</Button
              >
              {#if isActive(field)}
                <Button
                  type="button"
                  density="dense"
                  onclick={() => field && remove(field)}>Remove filter</Button
                >
              {/if}
            </div>
          </form>
        {:else}
          <h2>Add filter</h2>
          <label class="input-label" for={`${id}-find`}>Find a filter</label>
          <TextInput id={`${id}-find`} bind:value={query} type="search" />
          <ul class="filter-list" aria-label="Available filters">
            {#each available as key (key)}
              <li>
                <Button
                  type="button"
                  density="dense"
                  onclick={() => start(key, source)}>{label(key)}</Button
                >
              </li>
            {/each}
          </ul>
          {#if !available.length}
            <p class="hint">
              {EDITABLE_SEARCH_FILTERS.every(isActive)
                ? "All filters are in use. Select a chip to edit it."
                : "No matching filters."}
            </p>
          {/if}
          <Button type="button" density="dense" onclick={() => close(source)}
            >Cancel</Button
          >
        {/if}
      </div>
    {/if}
  </Popover>
{/snippet}

<div class="conditions" role="group" aria-label="Confirmed search filters">
  {#each EDITABLE_SEARCH_FILTERS.filter(isActive) as key (key)}
    <div class="condition">
      {@render condition(key)}
      <Button
        type="button"
        class="remove-condition"
        density="dense"
        {disabled}
        aria-label={`Remove ${label(key)} filter`}
        title={`Remove ${label(key)} filter`}
        onclick={() => remove(key)}
      >
        {#snippet iconLeft()}<CloseIcon />{/snippet}
      </Button>
    </div>
  {/each}
  {@render condition("add")}
</div>

<style>
  .conditions,
  .condition,
  .editor-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    min-width: 0;
  }
  .condition {
    flex-wrap: nowrap;
    gap: 0;
    max-width: 100%;
    border: 1px solid var(--lp-color-border-default);
    border-radius: 0.25rem;
    background: var(--lp-color-background-alt);
  }
  .chip-trigger {
    border: 0;
    background: transparent;
    color: inherit;
    padding: 0.15rem;
    cursor: pointer;
    min-width: 0;
    max-width: 24rem;
  }
  .chip-trigger:hover {
    background: var(--lp-color-background-hover);
  }
  .chip-trigger:focus-visible {
    outline: 2px solid var(--lp-color-border-focus);
    outline-offset: 2px;
  }
  .chip-trigger :global(.chip) {
    max-width: 100%;
    box-sizing: border-box;
    background: transparent;
    border: 0;
    border-radius: 0;
  }
  .chip-trigger :global(.lead) {
    flex-shrink: 0;
  }
  .chip-trigger :global(.value) {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .condition :global(.remove-condition) {
    flex-shrink: 0;
    border: 0;
    padding: 0.25rem;
    min-height: 2rem;
  }
  :global(.condition-popover) {
    width: 23rem;
    box-sizing: border-box;
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    padding: 0;
    overflow: auto;
    border-radius: 0.25rem;
    box-shadow: 0 4px 16px rgb(0 0 0 / 20%);
  }
  .panel {
    width: 100%;
    box-sizing: border-box;
    padding: 1rem;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-default);
  }
  h2 {
    margin: 0 0 0.75rem;
    font-size: 1rem;
    font-weight: 550;
  }
  .input-label {
    display: block;
    margin-bottom: 0.5rem;
  }
  .filter-list {
    max-height: min(17rem, 40dvh);
    overflow: auto;
  }
  .panel :global(.text-input) {
    width: 100%;
    box-sizing: border-box;
  }
  .filter-list {
    list-style: none;
    margin: 0.5rem 0 0.75rem;
    padding: 0;
  }
  .filter-list :global(button) {
    width: 100%;
    justify-content: flex-start;
  }
  .hint {
    color: var(--lp-color-text-muted);
    font-size: 0.875rem;
    margin: 0.5rem 0 1rem;
  }
</style>
