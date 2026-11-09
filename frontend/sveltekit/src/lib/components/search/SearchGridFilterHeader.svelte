<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, tick } from "svelte";
  import type { Family } from "$lib/types";
  import type { SearchFilter, SearchFilters } from "$lib/testResultsFilters";
  import SearchGridFilterMenu from "./SearchGridFilterMenu.svelte";

  type MenuFilter = SearchFilter;

  let {
    label,
    filterKey,
    filters,
    families,
    invalidFields = [],
    disabled = false,
    hideLabel = false,
    onedit,
  }: {
    label: string;
    filterKey: MenuFilter;
    filters: SearchFilters;
    families: Family[];
    invalidFields?: SearchFilter[];
    disabled?: boolean;
    hideLabel?: boolean;
    onedit: (key: SearchFilter, next: SearchFilters) => void;
  } = $props();

  let open = $state(false);
  let trigger: HTMLButtonElement;
  let menu: HTMLDivElement;
  let position = $state({ left: 8, top: 8, maxHeight: 400 });
  let unmounted = false;
  onDestroy(() => {
    unmounted = true;
  });

  const menuId = $derived(`search-grid-menu-${filterKey}`);
  function isActive(): boolean {
    switch (filterKey) {
      case "families":
        return filters.families.length > 0;
      case "test_result_statuses":
        return filters.test_result_statuses.length > 0;
      case "test_execution_statuses":
        return filters.test_execution_statuses.length > 0;
      case "artefact_stages":
        return filters.artefact_stages.length > 0;
      case "artefact_is_archived":
        return filters.artefact_is_archived !== null;
      case "rerun_is_requested":
        return filters.rerun_is_requested !== null;
      case "execution_is_latest":
        return filters.execution_is_latest !== null;
      case "from_date":
        return !!(filters.from_date || filters.until_date);
      case "artefacts":
        return filters.artefacts.length > 0;
      case "artefact_versions":
        return filters.artefact_versions.length > 0;
      case "artefact_tracks":
        return filters.artefact_tracks.length > 0;
      case "environments":
        return filters.environments.length > 0;
      case "test_cases":
        return filters.test_cases.length > 0;
      case "test_plans":
        return filters.test_plans.length > 0;
      case "template_ids":
        return filters.template_ids.length > 0;
      case "issues":
        return Array.isArray(filters.issues) ? filters.issues.length > 0 : true;
      case "reviewer_ids":
        return Array.isArray(filters.reviewer_ids)
          ? filters.reviewer_ids.length > 0
          : true;
      case "execution_metadata":
        return filters.execution_metadata.length > 0;
    }
    return false;
  }

  function positionMenu() {
    if (!trigger || typeof window === "undefined") return;
    const rect = trigger.getBoundingClientRect();
    const width = Math.min(320, window.innerWidth - 16);
    const maxHeight = Math.max(160, window.innerHeight - 16);
    const expectedHeight = Math.min(420, maxHeight);
    const top =
      rect.bottom + 4 + expectedHeight <= window.innerHeight
        ? rect.bottom + 4
        : Math.max(8, rect.top - expectedHeight - 4);
    const left = Math.max(
      8,
      Math.min(rect.left, window.innerWidth - width - 8),
    );
    position = { left, top, maxHeight };
  }

  async function toggleMenu() {
    if (disabled) return;
    if (open) {
      open = false;
      return;
    }
    const event = new Event("search-grid-open-menu");
    Object.defineProperty(event, "detail", { value: filterKey });
    document.dispatchEvent(event);
    open = true;
    if (!open) return;
    await tick();
    if (unmounted || !open) return;
    positionMenu();
    menu
      ?.querySelector<HTMLElement>(
        'input[type="search"], input[type="text"], input:not([type]), select, input, button',
      )
      ?.focus({ preventScroll: true });
  }

  function closeMenu(restoreFocus = false) {
    if (!open) return;
    open = false;
    if (restoreFocus)
      void tick().then(() => trigger?.focus({ preventScroll: true }));
  }

  $effect(() => {
    if (!open || typeof document === "undefined") return;
    const closeForDetails = () => closeMenu();
    const closeForAnotherMenu = (event: Event) => {
      if ((event as CustomEvent<string>).detail !== filterKey) closeMenu();
    };
    const outside = (event: PointerEvent) => {
      const target = event.target;
      if (
        target instanceof Node &&
        !menu?.contains(target) &&
        !trigger?.contains(target)
      )
        closeMenu();
    };
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        closeMenu(true);
      }
    };
    const focusOutside = (event: FocusEvent) => {
      const target = event.target;
      if (
        target instanceof Node &&
        !menu?.contains(target) &&
        !trigger?.contains(target)
      )
        closeMenu();
    };
    const reposition = () => positionMenu();
    document.addEventListener("pointerdown", outside, true);
    document.addEventListener("keydown", keydown, true);
    document.addEventListener("focusin", focusOutside, true);
    document.addEventListener("search-grid-close-menus", closeForDetails);
    document.addEventListener("search-grid-open-menu", closeForAnotherMenu);
    document.addEventListener("scroll", reposition, true);
    window.addEventListener("resize", reposition);
    window.addEventListener("scroll", reposition, true);
    return () => {
      document.removeEventListener("pointerdown", outside, true);
      document.removeEventListener("keydown", keydown, true);
      document.removeEventListener("focusin", focusOutside, true);
      document.removeEventListener("search-grid-close-menus", closeForDetails);
      document.removeEventListener(
        "search-grid-open-menu",
        closeForAnotherMenu,
      );
      document.removeEventListener("scroll", reposition, true);
      window.removeEventListener("resize", reposition);
      window.removeEventListener("scroll", reposition, true);
    };
  });
</script>

<div class="header-content">
  {#if !hideLabel}<span>{label}</span>{/if}
  <button
    bind:this={trigger}
    type="button"
    class:active={isActive() || invalidFields.includes(filterKey)}
    class="column-filter-trigger"
    aria-label={`Filter ${label}`}
    aria-haspopup="dialog"
    aria-expanded={open}
    aria-controls={menuId}
    title={`Set an exact server-side ${label} filter`}
    {disabled}
    onclick={toggleMenu}
  >
    Filter{#if isActive() || invalidFields.includes(filterKey)}<span
        class="indicator"
        aria-hidden="true"
      >
        ●</span
      >{/if}
  </button>
  <div
    bind:this={menu}
    id={menuId}
    class="menu-anchor"
    role="dialog"
    aria-label={`${label} column filter`}
    hidden={!open}
    style:left="{position.left}px"
    style:top="{position.top}px"
    style:max-height="{position.maxHeight}px"
  >
    <SearchGridFilterMenu
      {filterKey}
      {filters}
      {families}
      {invalidFields}
      {disabled}
      {open}
      compactFilterPresentation
      {onedit}
    />
  </div>
</div>

<style>
  .header-content {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    min-width: 0;
  }
  .column-filter-trigger {
    border: 0;
    border-radius: 0.2rem;
    padding: 0.125rem 0.25rem;
    color: var(--lp-color-text-muted);
    background: transparent;
    font: inherit;
    font-size: 0.75rem;
    cursor: pointer;
  }
  .column-filter-trigger:hover,
  .column-filter-trigger:focus-visible,
  .column-filter-trigger.active {
    color: var(--lp-color-text-default);
    text-decoration: underline;
  }
  .column-filter-trigger:disabled {
    cursor: default;
  }
  .indicator {
    color: var(--lp-color-status-positive, var(--lp-color-text-default));
    font-size: 0.65rem;
  }
  .menu-anchor {
    position: fixed;
    z-index: 905;
    box-sizing: border-box;
    width: min(20rem, calc(100vw - 1rem));
    overflow: auto;
    overscroll-behavior: contain;
  }
</style>
