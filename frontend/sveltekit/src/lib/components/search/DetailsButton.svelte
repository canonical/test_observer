<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Button } from "@canonical/svelte-ds-app-launchpad";

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
  }}>Details</Button
>
