<script lang="ts">
  import StatusSummary from './StatusSummary.svelte';
  import EnvironmentExpandable from './EnvironmentExpandable.svelte';
  import StartManualTestingDialog from './StartManualTestingDialog.svelte';
  import type { ArtefactEnvironment } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import { userStore } from '$lib/stores/user.svelte';
  import type { Family } from '$lib/types';

  interface Props {
    artefactId: number;
    family: Family;
    environments: ArtefactEnvironment[];
    store: ArtefactPageStore;
  }

  let { artefactId, family, environments, store }: Props = $props();

  let manualTestOpen = $state(false);

  // Count unique latest runs for rerun: one per unique (build_id, env_id, test_plan) triple
  const rerunCount = $derived.by(() => {
    const seen = new Set<string>();
    for (const env of environments) {
      const planMap = new Map<string, typeof env.runsDescending[0]>();
      for (const run of env.runsDescending) {
        const key = `${run.artefact_build_id}|${run.environment.id}|${run.test_plan}`;
        if (!planMap.has(key)) planMap.set(key, run);
      }
      for (const [key] of planMap) {
        seen.add(key);
      }
    }
    return seen.size;
  });

  // Collect latest run IDs per unique triple across all environments
  function getRerunIds(): number[] {
    const ids: number[] = [];
    for (const env of environments) {
      const planMap = new Map<string, number>();
      for (const run of env.runsDescending) {
        const key = `${run.artefact_build_id}|${run.environment.id}|${run.test_plan}`;
        if (!planMap.has(key)) planMap.set(key, run.id);
      }
      for (const id of planMap.values()) {
        ids.push(id);
      }
    }
    return ids;
  }

  let rerunning = $state(false);

  async function handleRerunAll() {
    rerunning = true;
    await store.rerunExecutions(getRerunIds());
    rerunning = false;
  }
</script>

<div class="artefact-body">
  <div class="title-row">
    <h2>Environments</h2>
    <StatusSummary {environments} />
    <span class="spacer"></span>

    {#if userStore.isLoggedIn && store.builds.length > 0}
      <button class="text-action" onclick={() => (manualTestOpen = true)}>
        Add Manual Testing
      </button>
    {/if}

    <button
      class="text-action"
      onclick={handleRerunAll}
      disabled={rerunning || rerunCount === 0}
    >
      Rerun {rerunCount} Filtered Test Plans
    </button>
  </div>

  <div class="environment-list">
    {#each environments as env (env.review.id)}
      <EnvironmentExpandable {env} {store} {artefactId} {family} />
    {/each}
  </div>
</div>

<StartManualTestingDialog
  {artefactId}
  {family}
  {store}
  open={manualTestOpen}
  onclose={() => (manualTestOpen = false)}
/>

<style>
  .artefact-body {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .spacer {
    flex: 1;
  }

  .text-action {
    all: unset;
    cursor: pointer;
    font-size: 14px;
    font-family: inherit;
    color: #E95420;
    white-space: nowrap;
  }

  .text-action:hover:not(:disabled) {
    text-decoration: underline;
  }

  .text-action:disabled {
    opacity: 0.5;
    cursor: default;
  }

  .environment-list {
    display: flex;
    flex-direction: column;
  }
</style>
