<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import type { ArtefactStatus } from "$lib/types";
  import type { ApprovalAuthorResponse } from "$lib/types/openapi";

  let {
    status,
    author,
  }: {
    status: ArtefactStatus;
    author: ApprovalAuthorResponse | null | undefined;
  } = $props();
</script>

{#if status === "APPROVED"}
  <span class="approval-author">
    {#if author === undefined}
      Loading approval author…
    {:else if author?.name}
      Approved by {author.name}{author.kind === "application"
        ? " (application)"
        : author.kind === "automation"
          ? " (automation)"
          : ""}
    {:else}
      Approval author unavailable
    {/if}
  </span>
{/if}

<style>
  .approval-author {
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }
</style>
