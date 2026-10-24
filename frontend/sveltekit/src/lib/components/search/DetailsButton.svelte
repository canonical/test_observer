<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Button } from "@canonical/svelte-ds-app-launchpad";
  import { ShowIcon } from "@canonical/svelte-icons";

  let {
    name,
    resultId,
    prepare,
    show,
  }: {
    name: string;
    resultId: number;
    prepare: () => void;
    show: (trigger: HTMLButtonElement) => void;
  } = $props();
</script>

<Button
  class="details-button"
  type="button"
  density="dense"
  severity="base"
  aria-label={`View details for ${name}`}
  aria-haspopup="dialog"
  data-test-result-id={resultId}
  onpointerdown={(event) => {
    // Stop SvGrid's cell/range pointer handler, before native light-dismiss.
    event.stopPropagation();
    prepare();
  }}
  onkeydown={(event) => event.stopPropagation()}
  onclick={(event) => {
    event.stopPropagation();
    prepare();
    show(event.currentTarget);
  }}>
  {#snippet iconLeft()}
    <span class="details-icon" aria-hidden="true">
      <ShowIcon style="width: 100%; height: 100%;" />
    </span>
  {/snippet}
  Details</Button
>

<style>
  :global(.details-button) {
    --lp-color-text-context: var(--lp-color-text-link-default);
    --lp-dimension-padding-inline-context: 0.25rem;
    white-space: nowrap;
  }

  :global(.details-button .button-content) {
    column-gap: 0.25rem;
  }

  .details-icon {
    display: inline-flex;
    width: 1rem;
    min-width: 1rem;
    height: 1rem;
    flex: none;
  }

  :global(.details-button:hover .text),
  :global(.details-button:focus-visible .text) {
    text-decoration: underline;
    text-underline-offset: 0.15em;
  }
</style>
