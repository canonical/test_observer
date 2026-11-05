<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  let { option }: { option: 2 | 3 | 4 } = $props();
</script>

<svelte:head>
  <title>Search (Option {option}) — Test Observer</title>
</svelte:head>

<section class="placeholder" aria-labelledby="search-option-title">
  <h1 id="search-option-title">Search (Option {option})</h1>
  <p>
    This option is a scaffold only. Search controls and results are not
    implemented yet.
  </p>
</section>

<style>
  .placeholder {
    padding: 2rem 0;
  }

  h1 {
    margin: 0 0 1rem;
    font-size: 1.75rem;
    font-weight: 500;
  }

  p {
    margin: 0;
    color: var(--lp-color-text-muted);
  }
</style>
