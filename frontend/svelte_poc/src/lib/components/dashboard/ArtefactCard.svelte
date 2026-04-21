<script lang="ts">
  import { base } from '$app/paths';
  import type { Artefact, Family } from '$lib/types';
  import StatusChip from './StatusChip.svelte';
  import DueDateChip from './DueDateChip.svelte';
  import UserAvatar from './UserAvatar.svelte';

  let { artefact, family }: { artefact: Artefact; family: Family } = $props();

  const fields = $derived(
    [
      artefact.track && `track: ${artefact.track}`,
      artefact.store && `store: ${artefact.store}`,
      artefact.branch && `branch: ${artefact.branch}`,
      artefact.series && `series: ${artefact.series}`,
      artefact.repo && `repo: ${artefact.repo}`,
      artefact.source && `source: ${artefact.source}`,
      artefact.os && `os: ${artefact.os}`,
      artefact.release && `release: ${artefact.release}`,
      artefact.owner && `owner: ${artefact.owner}`,
    ].filter(Boolean) as string[]
  );
</script>

<a href="{base}/{family}/{artefact.id}" class="card">
  <div class="card-body">
    <h3 class="name">{artefact.name}</h3>
    <p class="field">version: {artefact.version}</p>
    {#each fields as field}
      <p class="field">{field}</p>
    {/each}
  </div>
  <div class="card-footer">
    <StatusChip status={artefact.status} />
    <DueDateChip dueDate={artefact.due_date} />
    <div class="spacer"></div>
    <UserAvatar
      assignee={artefact.assignee}
      completed={artefact.completed_environment_reviews_count}
      total={artefact.all_environment_reviews_count}
    />
  </div>
</a>

<style>
  .card {
    display: flex;
    flex-direction: column;
    width: 320px;
    min-height: 182px;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 2px;
    padding: 16px;
    text-decoration: none;
    color: inherit;
    transition: box-shadow 0.15s;
  }

  .card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .card-body {
    flex: 1;
  }

  .name {
    margin: 0 0 4px;
    font-size: 1rem;
    font-weight: 600;
    line-height: 1.3;
  }

  .field {
    margin: 0;
    font-size: 0.82rem;
    color: #555;
    line-height: 1.4;
  }

  .card-footer {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  .spacer {
    flex: 1;
  }
</style>
