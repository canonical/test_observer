<script lang="ts">
  import Expandable from '$lib/components/ui/Expandable.svelte';

  interface Props {
    metadata: Record<string, string[]>;
  }

  let { metadata }: Props = $props();

  const entries = $derived(Object.entries(metadata));
  let open = $state(false);
</script>

{#if entries.length > 0}
  <Expandable bind:open titleText="Execution Metadata">
    <table class="metadata-table">
      <tbody>
        {#each entries as [key, values] (key)}
          <tr>
            <td class="key">{key}</td>
            <td class="value">{values.join(', ')}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Expandable>
{/if}

<style>
  .metadata-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }

  .metadata-table td {
    padding: 4px 8px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top;
  }

  .key {
    font-weight: 600;
    color: #555;
    width: 200px;
    white-space: nowrap;
  }

  .value {
    word-break: break-word;
    color: #333;
  }
</style>
