<script lang="ts">
  import { formatDueDate } from '$lib/types';

  let { dueDate }: { dueDate: string | null } = $props();
  const formatted = $derived(formatDueDate(dueDate));
</script>

{#if formatted}
  <span class="due-chip">Due {formatted}</span>
{/if}

<style>
  .due-chip {
    display: inline-block;
    padding: 2px 8px;
    border: 1px solid #c7162b;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
    color: #e0522d;
    white-space: nowrap;
  }
</style>
