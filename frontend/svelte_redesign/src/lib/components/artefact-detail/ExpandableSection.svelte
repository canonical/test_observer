<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    header: Snippet;
    children: Snippet;
    open?: boolean;
  }

  const { header, children, open = false }: Props = $props();

  let expanded = $state(false);

  $effect(() => {
    expanded = open;
  });

  function toggle() {
    expanded = !expanded;
  }
</script>

<section class="ds expandable-section">
  <button
    type="button"
    class="ds expandable-section__header"
    onclick={toggle}
    aria-expanded={expanded}
  >
    <span class="ds expandable-section__chevron" class:open={expanded}>&#9656;</span>
    {@render header()}
  </button>
  {#if expanded}
    <div class="ds expandable-section__body">
      {@render children()}
    </div>
  {/if}
</section>

<style>
  .ds.expandable-section {
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
  }

  .ds.expandable-section__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    cursor: pointer;
    font: inherit;
    text-align: left;
  }

  .ds.expandable-section__header:hover {
    background-color: var(--color-background-hover, #f5f5f5);
  }

  .ds.expandable-section__chevron {
    display: inline-block;
    transition: transform 0.15s ease;
    font-size: 0.75rem;
  }

  .ds.expandable-section__chevron.open {
    transform: rotate(90deg);
  }

  .ds.expandable-section__body {
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--color-border, #d9d9d9);
  }
</style>
