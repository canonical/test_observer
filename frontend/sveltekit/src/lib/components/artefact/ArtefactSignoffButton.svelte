<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { tick } from "svelte";
  import { Chip } from "@canonical/svelte-ds-app-launchpad";
  import type { Artefact, ArtefactStatus } from "$lib/types";
  import { STATUS_LABELS } from "$lib/types";

  interface Props {
    artefact: Artefact;
    canChangeStatus: boolean;
    onstatuschange: (status: ArtefactStatus) => void;
  }

  let { artefact, canChangeStatus, onstatuschange }: Props = $props();

  let open = $state(false);
  let wrapperEl: HTMLDivElement | undefined = $state();
  let triggerEl: HTMLButtonElement | undefined = $state();
  let activeIndex = $state(0);

  const statuses: ArtefactStatus[] = [
    "APPROVED",
    "MARKED_AS_FAILED",
    "UNDECIDED",
  ];

  $effect(() => {
    if (!canChangeStatus) open = false;
  });

  const chipSeverity = $derived.by((): "positive" | "negative" | undefined => {
    if (artefact.status === "APPROVED") return "positive";
    if (artefact.status === "MARKED_AS_FAILED") return "negative";
    return undefined;
  });

  function menuItems() {
    return wrapperEl?.querySelectorAll<HTMLButtonElement>(
      '[role="menuitemradio"]',
    );
  }

  async function showMenu(index = statuses.indexOf(artefact.status)) {
    activeIndex = index < 0 ? 0 : index;
    open = true;
    await tick();
    menuItems()?.[activeIndex]?.focus();
  }

  function toggle() {
    if (!canChangeStatus) return;
    if (open) {
      open = false;
      return;
    }
    void showMenu();
  }

  function select(status: ArtefactStatus) {
    if (!canChangeStatus) return;
    open = false;
    onstatuschange(status);
    triggerEl?.focus();
  }

  function handleTriggerKeydown(e: KeyboardEvent) {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      void showMenu(e.key === "ArrowDown" ? 0 : statuses.length - 1);
    }
  }

  function handleOptionKeydown(e: KeyboardEvent, index: number) {
    const lastIndex = statuses.length - 1;
    let nextIndex: number;

    switch (e.key) {
      case "ArrowDown":
        nextIndex = index === lastIndex ? 0 : index + 1;
        break;
      case "ArrowUp":
        nextIndex = index === 0 ? lastIndex : index - 1;
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = lastIndex;
        break;
      case "Escape":
        e.preventDefault();
        open = false;
        triggerEl?.focus();
        return;
      case "Tab":
        // Let the browser move focus according to the user's Tab direction
        // before removing the focused menu item from the DOM.
        setTimeout(() => (open = false));
        return;
      default:
        return;
    }

    e.preventDefault();
    activeIndex = nextIndex;
    menuItems()?.[nextIndex]?.focus();
  }

  function handleClickOutside(e: MouseEvent) {
    if (wrapperEl && !wrapperEl.contains(e.target as Node)) {
      open = false;
    }
  }

  $effect(() => {
    if (open) {
      document.addEventListener("click", handleClickOutside, true);
      return () =>
        document.removeEventListener("click", handleClickOutside, true);
    }
  });
</script>

<div class="wrapper" bind:this={wrapperEl}>
  {#if canChangeStatus}
    <button
      bind:this={triggerEl}
      class="trigger"
      type="button"
      onclick={toggle}
      onkeydown={handleTriggerKeydown}
      aria-haspopup="menu"
      aria-expanded={open}
      aria-label={`Artefact status: ${STATUS_LABELS[artefact.status]}`}
    >
      <Chip
        value={STATUS_LABELS[artefact.status]}
        severity={chipSeverity}
        readonly
        density="dense"
      />
    </button>
  {:else}
    <Chip
      value={STATUS_LABELS[artefact.status]}
      severity={chipSeverity}
      readonly
      density="dense"
    />
  {/if}

  {#if open}
    <div class="dropdown" role="menu" aria-label="Artefact status">
      {#each statuses as status (status)}
        <button
          class="option"
          type="button"
          class:active={artefact.status === status}
          role="menuitemradio"
          aria-checked={artefact.status === status}
          tabindex={activeIndex === statuses.indexOf(status) ? 0 : -1}
          onfocus={() => (activeIndex = statuses.indexOf(status))}
          onkeydown={(e) => handleOptionKeydown(e, statuses.indexOf(status))}
          onclick={() => select(status)}
        >
          {STATUS_LABELS[status]}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .wrapper {
    position: relative;
  }

  .trigger {
    all: unset;
    cursor: pointer;
  }

  .trigger:focus-visible {
    outline: 2px solid var(--lp-color-brand-default);
    outline-offset: 2px;
    border-radius: 2px;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    z-index: 50;
    min-width: 200px;
    padding: 4px 0;
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .option {
    display: block;
    width: 100%;
    padding: 8px 16px;
    background: none;
    border: none;
    text-align: left;
    font-size: 0.875rem;
    cursor: pointer;
    color: var(--lp-color-text-default);
    font-family: inherit;
  }

  .option:hover {
    background: var(--lp-color-background-hover);
  }

  .option.active {
    font-weight: 600;
    color: var(--lp-color-brand-default);
  }
</style>
