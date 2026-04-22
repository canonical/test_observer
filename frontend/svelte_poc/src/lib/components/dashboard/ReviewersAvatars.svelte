<script lang="ts">
  import type { User } from '$lib/types';
  import UserAvatar from './UserAvatar.svelte';

  let { reviewers: rawReviewers, allEnvironmentReviewsCount, completedEnvironmentReviewsCount }: {
    reviewers: User[] | undefined | null;
    allEnvironmentReviewsCount: number;
    completedEnvironmentReviewsCount: number;
  } = $props();

  const reviewers = $derived(rawReviewers ?? []);
</script>

<div class="reviewers-avatars">
  {#if reviewers.length === 0}
    <UserAvatar
      user={null}
      completed={completedEnvironmentReviewsCount}
      total={allEnvironmentReviewsCount}
    />
  {:else}
    {#each reviewers as reviewer, i (reviewer.id)}
      <div class="avatar-slot" style:margin-left="{i > 0 ? -8 : 0}px" style:z-index={reviewers.length - i}>
        <UserAvatar
          user={reviewer}
          completed={completedEnvironmentReviewsCount}
          total={allEnvironmentReviewsCount}
        />
      </div>
    {/each}
  {/if}
</div>

<style>
  .reviewers-avatars {
    display: flex;
    align-items: center;
  }

  .avatar-slot {
    position: relative;
  }
</style>
