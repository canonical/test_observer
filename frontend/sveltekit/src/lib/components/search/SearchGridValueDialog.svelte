<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Button, Modal } from "@canonical/svelte-ds-app-launchpad";

  let {
    selection,
    onclose,
  }: {
    selection: {
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
    } | null;
    onclose: () => void;
  } = $props();
  const id = $props.id();
  let open = $derived(selection !== null);
  const summary = $derived(
    selection
      ? `${selection.items.length} ${selection.itemLabel}${selection.items.length === 1 ? "" : "s"}`
      : "",
  );
</script>

<Modal
  class="search-grid-value-dialog"
  aria-labelledby={`${id}-heading`}
  bind:open
  onclose={(event) => {
    // A queued close from a previous open must not close a newer selection.
    if (!event.currentTarget.open) onclose();
  }}
>
  {#snippet children(commandfor, close)}
    <Modal.Content class="value-content">
      <Modal.Content.Header>
        <h2 id={`${id}-heading`}>{selection?.heading ?? "Values"}</h2>
        <Modal.Content.Header.CloseButton
          {commandfor}
          command="close"
          aria-label={`Close ${selection?.heading.toLowerCase() ?? "values"}`}
        />
      </Modal.Content.Header>
      <Modal.Content.Body
        class="value-body"
        role="region"
        aria-label={`${selection?.heading ?? "Values"} values`}
        tabindex={0}
      >
        {#if selection?.items.length}
          {#if selection.itemLayout === "metadata-table"}
            <table class="metadata-table" aria-label={selection.heading}>
              <thead>
                <tr><th scope="col">Category</th><th scope="col">Value</th></tr>
              </thead>
              <tbody>
                {#each selection.items as item (item.key)}
                  <tr>
                    <th scope="row">{item.label}</th>
                    <td>{item.detail}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {:else}
            <ul aria-label={`All ${selection.heading.toLowerCase()}`}>
              {#each selection.items as item (item.key)}
                <li>
                  {#if item.href}
                    <a
                      class="issue-link"
                      href={item.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={item.ariaLabel}
                    >
                      <strong>{item.label}</strong>
                      {#if item.detail}<span>{item.detail}</span>{/if}
                    </a>
                  {:else}
                    <strong>{item.label}</strong>
                    {#if item.detail}<span>{item.detail}</span>{/if}
                  {/if}
                </li>
              {/each}
            </ul>
          {/if}
        {:else if selection}
          <p>No {selection.heading.toLowerCase()} available.</p>
        {/if}
      </Modal.Content.Body>
      <Modal.Content.Footer>
        <span>{summary}</span>
        <Button type="button" density="dense" onclick={close}>Close</Button>
      </Modal.Content.Footer>
    </Modal.Content>
  {/snippet}
</Modal>

<style>
  :global(html:has(dialog.search-grid-value-dialog[open])) {
    overflow: hidden;
  }
  /* Keep the single list-value modal in the same responsive design-system
     frame as SearchResultDetails, regardless of the stylesheet's rule order. */
  :global(dialog.ds.modal.search-grid-value-dialog) {
    width: min(900px, calc(100vw - 2rem));
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }
  :global(.search-grid-value-dialog .value-content) {
    max-height: calc(100dvh - 2rem);
    min-height: 0;
    box-sizing: border-box;
  }
  :global(.search-grid-value-dialog .dialog-content-header),
  :global(.search-grid-value-dialog .dialog-content-footer) {
    flex-shrink: 0;
  }
  :global(.search-grid-value-dialog .value-body) {
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    overflow-wrap: anywhere;
  }
  :global(.search-grid-value-dialog .value-body ul) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    list-style: none;
    white-space: normal;
    overflow-wrap: anywhere;
  }
  :global(.search-grid-value-dialog .value-body li) {
    margin: 0.15rem 0;
  }
  :global(.search-grid-value-dialog .issue-link) {
    overflow-wrap: anywhere;
  }
  :global(.search-grid-value-dialog .value-body strong) {
    margin-right: 0.25rem;
  }
  :global(.search-grid-value-dialog .metadata-table) {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }
  :global(.search-grid-value-dialog .metadata-table th),
  :global(.search-grid-value-dialog .metadata-table td) {
    min-width: 0;
    padding: 0.35rem 0.5rem;
    overflow-wrap: anywhere;
    text-align: start;
    vertical-align: top;
  }
  :global(
    .search-grid-value-dialog .metadata-table th[scope="col"]:first-child
  ),
  :global(.search-grid-value-dialog .metadata-table th[scope="row"]) {
    width: 34%;
  }
  :global(.search-grid-value-dialog h2) {
    margin: 0;
    overflow-wrap: anywhere;
  }
</style>
