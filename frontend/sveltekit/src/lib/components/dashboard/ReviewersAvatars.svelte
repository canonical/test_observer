<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { UserAvatar, Badge } from '@canonical/svelte-ds-app-launchpad';
  import type { User } from '$lib/types';

  let {
    reviewers: rawReviewers,
    allEnvironmentReviewsCount,
    completedEnvironmentReviewsCount,
  }: {
    reviewers: Pick<User, 'id' | 'name'>[] | undefined | null;
    allEnvironmentReviewsCount: number;
    completedEnvironmentReviewsCount: number;
  } = $props();

  const reviewers = $derived(rawReviewers ?? []);
  const remaining = $derived(
    allEnvironmentReviewsCount - completedEnvironmentReviewsCount,
  );
</script>

<div class="reviewers-row">
  {#each reviewers.slice(0, 3) as reviewer (reviewer.id)}
    <UserAvatar userName={reviewer.name} size="small" />
  {/each}
  {#if reviewers.length > 3}
    <span class="more">+{reviewers.length - 3}</span>
  {/if}
  {#if allEnvironmentReviewsCount > 0}
    <Badge
      value={remaining}
      severity={remaining === 0 ? 'positive' : 'caution'}
    />
  {/if}
</div>

<style>
  .reviewers-row {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }
  .more {
    font-size: 0.75rem;
    color: #666;
  }
</style>
