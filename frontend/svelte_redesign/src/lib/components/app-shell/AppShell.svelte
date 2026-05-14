<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    sidebar: Snippet;
    header: Snippet;
    children: Snippet;
  }

  const { sidebar, header, children }: Props = $props();
</script>

<div class="ds app-shell">
  <aside class="ds app-shell__sidebar">
    {@render sidebar()}
  </aside>
  <header class="ds app-shell__header">
    {@render header()}
  </header>
  <main class="ds app-shell__content">
    {@render children()}
  </main>
</div>

<style>
  .ds.app-shell {
    display: grid;
    grid-template-columns: auto 1fr;
    grid-template-rows: var(--header-height, 56px) 1fr;
    grid-template-areas:
      "sidebar header"
      "sidebar content";
    height: 100vh;
    overflow: hidden;
  }

  .ds.app-shell__sidebar {
    grid-area: sidebar;
    overflow: hidden;
  }

  .ds.app-shell__header {
    grid-area: header;
    display: flex;
    align-items: center;
    padding: 0 var(--spacing-4);
    background-color: var(--lp-color-background-brand-default);
  }

  .ds.app-shell__content {
    grid-area: content;
    overflow-y: auto;
    padding: var(--spacing-4);
    background-color: var(--lp-color-background-default);
  }
</style>
