<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import DetailsButton from "./DetailsButton.svelte";
  import SearchRunLink from "./SearchRunLink.svelte";

  let {
    row,
    ondetails,
  }: {
    row: { id: number; testCase: string; runHref: string | null };
    ondetails: (id: number, trigger: HTMLButtonElement) => void;
  } = $props();

  function prepare() {
    document.dispatchEvent(new Event("search-grid-close-menus"));
  }
</script>

<div class="row-actions">
  <DetailsButton
    name={row.testCase}
    resultId={row.id}
    {prepare}
    show={(trigger) => ondetails(row.id, trigger)}
  />
  <SearchRunLink href={row.runHref} name={row.testCase} />
</div>

<style>
  .row-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }
</style>
