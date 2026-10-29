<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  let {
    heading,
    itemLabel,
    items,
    itemLayout,
    ownerKey,
    onshow,
  }: {
    heading: string;
    itemLabel: string;
    items: {
      key: string;
      label: string;
      detail?: string;
      href?: string;
      ariaLabel?: string;
    }[];
    itemLayout?: "metadata-table";
    ownerKey: string;
    onshow: (
      heading: string,
      itemLabel: string,
      items: {
        key: string;
        label: string;
        detail?: string;
        href?: string;
        ariaLabel?: string;
      }[],
      ownerKey: string,
      trigger: HTMLButtonElement,
      itemLayout?: "metadata-table",
    ) => void;
  } = $props();
  const summary = $derived(
    `${items.length} ${itemLabel}${items.length === 1 ? "" : "s"}`,
  );
</script>

<div class="value-cell" data-search-grid-values={heading}>
  <button
    type="button"
    class="summary"
    aria-haspopup="dialog"
    data-search-grid-value-owner={ownerKey}
    onpointerdown={(event) => event.stopPropagation()}
    onkeydown={(event) => event.stopPropagation()}
    onclick={(event) => {
      event.stopPropagation();
      onshow(
        heading,
        itemLabel,
        items,
        ownerKey,
        event.currentTarget,
        itemLayout,
      );
    }}
  >
    {summary}
  </button>
</div>

<style>
  .value-cell {
    box-sizing: border-box;
    min-width: 0;
    width: 100%;
    white-space: normal;
    overflow-wrap: anywhere;
  }
  .summary {
    display: block;
    max-width: 100%;
    margin: 0 0 0.15rem;
    padding: 0;
    border: 0;
    color: var(--lp-color-text-link, #06c);
    background: transparent;
    font: inherit;
    font-size: 0.75rem;
    text-align: left;
    text-decoration: underline;
    cursor: pointer;
    overflow-wrap: anywhere;
  }
  .summary:focus-visible {
    outline: 2px solid var(--lp-color-border-focus, #06c);
    outline-offset: 2px;
  }
</style>
