<script lang="ts">
  import { page } from '$app/state';
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import StatusIcon from '$lib/components/ui/StatusIcon.svelte';
  import EnvironmentReviewButton from './EnvironmentReviewButton.svelte';
  import EnvironmentIssuesExpandable from './EnvironmentIssuesExpandable.svelte';
  import TestPlanExpandable from './TestPlanExpandable.svelte';
  import type { ArtefactEnvironment } from '$lib/types/artefact-page';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    env: ArtefactEnvironment;
    store: ArtefactPageStore;
    artefactId: number;
    family: string;
  }

  let { env, store, artefactId, family }: Props = $props();

  const targetExecutionId = $derived(
    page.url.searchParams.get('testExecutionId'),
  );

  let open = $state(false);

  // Auto-expand if URL targets a run in this env
  $effect(() => {
    if (
      targetExecutionId &&
      env.runsDescending.some((r) => r.id === parseInt(targetExecutionId, 10))
    ) {
      open = true;
    }
  });

  const latestRun = $derived(env.runsDescending[0]);

  // Group runs by test_plan name
  const planGroups = $derived.by(() => {
    const map = new Map<string, typeof env.runsDescending>();
    for (const run of env.runsDescending) {
      const plan = run.test_plan || '(unnamed)';
      if (!map.has(plan)) map.set(plan, []);
      map.get(plan)!.push(run);
    }
    return Array.from(map.entries());
  });
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="env-title">
      {#if latestRun}
        <StatusIcon status={latestRun.status} size="20px" />
      {/if}
      <span class="arch-text">{env.architecture}</span>
      <span class="env-name">{env.name}</span>
      <span class="spacer"></span>
      <EnvironmentReviewButton review={env.review} {store} {artefactId} />
    </span>
  {/snippet}

  <div class="env-content">
    <EnvironmentIssuesExpandable environmentName={env.name} {store} />

    {#each planGroups as [planName, runs] (planName)}
      <TestPlanExpandable
        {planName}
        {runs}
        {store}
        {artefactId}
        {family}
        isOnlyPlan={planGroups.length === 1}
      />
    {/each}
  </div>
</Expandable>

<style>
  .env-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .arch-text {
    font-size: 13px;
    color: #666;
    white-space: nowrap;
  }

  .env-name {
    font-size: 14px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .spacer {
    flex: 1;
  }

  .env-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
</style>
