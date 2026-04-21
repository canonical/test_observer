<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    open?: boolean;
    title?: Snippet;
    children: Snippet;
    titleText?: string;
  }

  let { open = $bindable(false), title, children, titleText = '' }: Props = $props();
</script>

<details bind:open>
  <summary>
    {#if title}
      {@render title()}
    {:else}
      {titleText}
    {/if}
    <span class="chevron" class:open>▸</span>
  </summary>
  <div class="content">
    {@render children()}
  </div>
</details>

<style>
  details {
    border-bottom: 1px solid #e0e0e0;
  }

  summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 8px;
    cursor: pointer;
    list-style: none;
    user-select: none;
  }

  summary::-webkit-details-marker {
    display: none;
  }

  .chevron {
    margin-left: auto;
    transition: transform 0.2s;
    color: #757575;
    font-size: 14px;
  }

  .chevron.open {
    transform: rotate(90deg);
  }

  .content {
    padding: 0 8px 12px 24px;
  }
</style>
