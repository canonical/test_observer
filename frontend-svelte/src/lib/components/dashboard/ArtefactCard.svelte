<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { UserAvatar } from "@canonical/svelte-ds-app-launchpad";
  import { StatusBadge } from "$lib/components/common/index.js";
  import type { Artefact } from "$lib/types/artefact.js";
  import { artefactPath } from "$lib/utils/url.js";
  import { formatDate } from "$lib/utils/formatting.js";

  interface Props {
    artefact: Artefact;
    family: string;
  }

  const { artefact, family }: Props = $props();

  const statusSeverity = $derived(
    artefact.status === "APPROVED"
      ? "positive"
      : artefact.status === "MARKED_AS_FAILED"
        ? "negative"
        : "neutral",
  );
</script>

<a href={artefactPath(family, artefact.id)} class="ds artefact-card {statusSeverity}">
  <div class="ds artefact-card__header">
    <h3 class="ds artefact-card__name">{artefact.name}</h3>
    <StatusBadge status={artefact.status} />
  </div>

  <span class="ds artefact-card__version">v{artefact.version}</span>

  {#if artefact.track || artefact.series}
    <span class="ds artefact-card__meta">
      {#if artefact.track}{artefact.track}{/if}
      {#if artefact.track && artefact.series} · {/if}
      {#if artefact.series}{artefact.series}{/if}
    </span>
  {/if}

  <div class="ds artefact-card__footer">
    <div class="ds artefact-card__reviews">
      {#if artefact.reviewers.length > 0}
        <div class="ds artefact-card__avatars">
          {#each artefact.reviewers.slice(0, 3) as reviewer (reviewer.id)}
            <UserAvatar userName={reviewer.name} size="small" />
          {/each}
          {#if artefact.reviewers.length > 3}
            <span class="ds artefact-card__more-reviewers">+{artefact.reviewers.length - 3}</span>
          {/if}
        </div>
      {/if}
      <span class="ds artefact-card__progress">
        {artefact.completedEnvironmentReviewsCount}/{artefact.allEnvironmentReviewsCount}
      </span>
    </div>

    {#if artefact.dueDate}
      <span class="ds artefact-card__due-date">{formatDate(artefact.dueDate)}</span>
    {/if}
  </div>
</a>

<style>
  .ds.artefact-card {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
    padding: 0.75rem;
    background-color: var(--color-background, #fff);
    border: 1px solid var(--color-border, #d9d9d9);
    border-left: 3px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    text-decoration: none;
    color: inherit;
    transition: box-shadow 0.15s ease;
  }

  .ds.artefact-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .ds.artefact-card.positive {
    border-left-color: var(--color-positive, #0e8420);
  }

  .ds.artefact-card.negative {
    border-left-color: var(--color-negative, #c7162b);
  }

  .ds.artefact-card.neutral {
    border-left-color: var(--color-border, #d9d9d9);
  }

  .ds.artefact-card__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .ds.artefact-card__name {
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .ds.artefact-card__version {
    font-size: 0.75rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-card__meta {
    font-size: 0.75rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-card__footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    margin-top: 0.25rem;
  }

  .ds.artefact-card__reviews {
    display: flex;
    align-items: center;
    gap: 0.375rem;
  }

  .ds.artefact-card__avatars {
    display: flex;
    align-items: center;
    gap: -0.25rem;
  }

  .ds.artefact-card__more-reviewers {
    font-size: 0.75rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-card__progress {
    font-size: 0.75rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-card__due-date {
    font-size: 0.75rem;
    color: var(--color-text-muted, #666);
  }

  :global(.density-compact) .ds.artefact-card {
    padding: 0.5rem;
    gap: 0.25rem;
  }
</style>
