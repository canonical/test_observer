<script lang="ts">
  import type { User } from '$lib/types';
  import { userInitials } from '$lib/types';

  let { reviewers: rawReviewers }: { reviewers: User[] | undefined | null } = $props();

  const reviewers = $derived(rawReviewers ?? []);

  const COLORS = ['#FF5252', '#FFFF00', '#448AFF', '#FFAB40', '#69F0AE', '#E040FB'];
</script>

{#if reviewers.length > 0}
  <div class="env-reviewers">
    {#each reviewers as reviewer, i (reviewer.id)}
      <div
        class="env-avatar"
        style:margin-left="{i > 0 ? -8 : 0}px"
        style:z-index={reviewers.length - i}
        style:background-color={COLORS[Math.abs(reviewer.id) % COLORS.length]}
        title={reviewer.name}
      >
        {userInitials(reviewer.name)}
      </div>
    {/each}
  </div>
{/if}

<style>
  .env-reviewers {
    display: flex;
    align-items: center;
  }

  .env-avatar {
    position: relative;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.65rem;
    font-weight: 600;
    border: 2px solid white;
    flex-shrink: 0;
  }
</style>
