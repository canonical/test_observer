<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { ArtefactStatus } from "$lib/types/artefact.js";
  import { formatStatus } from "$lib/utils/formatting.js";

  interface Props {
    status: ArtefactStatus;
  }

  const { status }: Props = $props();

  const severity = $derived(
    status === "APPROVED"
      ? "positive"
      : status === "MARKED_AS_FAILED"
        ? "negative"
        : "neutral",
  );
</script>

<span class="ds status-badge {severity}" role="status">{formatStatus(status)}</span>

<style>
  .ds.status-badge {
    display: inline-block;
    padding: 0.125rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .ds.status-badge.positive {
    background-color: var(--color-positive-background, #e6f5e6);
    color: var(--color-positive-text, #0e6e0e);
  }

  .ds.status-badge.negative {
    background-color: var(--color-negative-background, #fde8e8);
    color: var(--color-negative-text, #c7162b);
  }

  .ds.status-badge.neutral {
    background-color: var(--color-background-alt, #f0f0f0);
    color: var(--color-text, #333);
  }
</style>
