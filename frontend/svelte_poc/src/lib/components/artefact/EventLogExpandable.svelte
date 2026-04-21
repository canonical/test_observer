<script lang="ts">
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    executionId: number;
    store: ArtefactPageStore;
    isCompleted: boolean;
  }

  let { executionId, store, isCompleted }: Props = $props();

  let open = $state(false);

  // Auto-expand if execution not completed
  $effect(() => {
    if (!isCompleted) open = true;
  });

  const events = $derived(store.getTestEvents(executionId));

  // Lazy load when opened
  $effect(() => {
    if (open) {
      store.fetchTestEvents(executionId);
    }
  });
</script>

<Expandable bind:open titleText="Event Log">
  {#if events === 'loading' || events === undefined}
    <div class="loading-row">
      <span class="material-symbols-outlined spin" style="font-size:16px">progress_activity</span>
      Loading events...
    </div>
  {:else if events.length === 0}
    <p class="empty">No events recorded.</p>
  {:else}
    <table class="events-table">
      <thead>
        <tr>
          <th>Event</th>
          <th>Timestamp</th>
          <th>Detail</th>
        </tr>
      </thead>
      <tbody>
        {#each events as evt}
          <tr>
            <td>{evt.event_name}</td>
            <td class="timestamp">{new Date(evt.timestamp).toLocaleString()}</td>
            <td class="detail">{evt.detail}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</Expandable>

<style>
  .loading-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #666;
    padding: 8px 0;
  }

  .spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .empty {
    color: #999;
    font-size: 13px;
    margin: 0;
  }

  .events-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  .events-table th {
    text-align: left;
    font-weight: 600;
    padding: 6px 8px;
    border-bottom: 1px solid #ddd;
    color: #555;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .events-table td {
    padding: 5px 8px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top;
  }

  .timestamp {
    white-space: nowrap;
    color: #666;
    font-size: 12px;
  }

  .detail {
    word-break: break-word;
  }
</style>
