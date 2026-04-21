<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import type { ArtefactVersion } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import { formatDueDate } from '$lib/types';
  import { base } from '$app/paths';
  import { goto } from '$app/navigation';
  import StagesBreadcrumb from './StagesBreadcrumb.svelte';
  import UserAvatar from '$lib/components/dashboard/UserAvatar.svelte';
  import ArtefactSignoffButton from './ArtefactSignoffButton.svelte';

  interface Props {
    artefact: Artefact;
    family: Family;
    versions: ArtefactVersion[];
    store: ArtefactPageStore;
  }

  let { artefact, family, versions, store }: Props = $props();

  const dueDate = $derived(formatDueDate(artefact.due_date));

  async function handleStatusChange(status: string) {
    await store.updateArtefactStatus(artefact.id, status);
  }

  function navigateToVersion(e: Event) {
    const target = e.target as HTMLSelectElement;
    const artefactId = target.value;
    if (artefactId) {
      goto(`${base}/${family}/${artefactId}`);
    }
  }
</script>

<header class="artefact-header">
  <div class="header-top">
    <h1 class="artefact-name">{artefact.name}</h1>
    <ArtefactSignoffButton {artefact} onstatuschange={handleStatusChange} />
    <UserAvatar
      assignee={artefact.assignee}
      completed={artefact.completed_environment_reviews_count}
      total={artefact.all_environment_reviews_count}
    />
    {#if dueDate}
      <span class="due-date">Due {dueDate}</span>
    {/if}
  </div>

  <div class="header-bottom">
    <StagesBreadcrumb {artefact} {family} />
  </div>

  <div class="header-meta">
    <div class="version-row">
      <label class="version-label" for="version-select">version:</label>
      <select
        id="version-select"
        class="version-select"
        value={artefact.id.toString()}
        onchange={navigateToVersion}
      >
        {#each versions as v (v.artefact_id)}
          <option value={v.artefact_id.toString()}>
            {v.version}
          </option>
        {/each}
      </select>
    </div>
  </div>
</header>

<style>
  .artefact-header {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-bottom: 8px;
  }

  .header-top {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .artefact-name {
    margin: 0;
    font-size: 28px;
    font-weight: 400;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .due-date {
    font-size: 14px;
    color: #E95420;
  }

  .header-bottom {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-meta {
    display: flex;
    align-items: center;
    gap: 24px;
  }

  .version-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .version-label {
    font-size: 14px;
    color: #333;
  }

  .version-select {
    padding: 4px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
    font-family: inherit;
    background: #fff;
    cursor: pointer;
  }
</style>
