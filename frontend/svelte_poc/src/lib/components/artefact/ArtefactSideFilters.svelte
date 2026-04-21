<script lang="ts">
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { base } from '$app/paths';
  import Expandable from '$lib/components/ui/Expandable.svelte';
  import SearchableMultiSelect from '$lib/components/ui/SearchableMultiSelect.svelte';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import type { TestExecutionStatus } from '$lib/types/artefact-page';

  interface Props {
    store: ArtefactPageStore;
    family: string;
    artefactId: number;
  }

  let { store, family, artefactId }: Props = $props();

  // Read filter state from URL
  function getParam(key: string): string[] {
    const val = page.url.searchParams.get(key);
    return val ? val.split(',').map(decodeURIComponent) : [];
  }

  const selectedEnvironments = $derived(getParam('environment'));
  const selectedTestPlans = $derived(getParam('test_plan'));
  const selectedReviewStatuses = $derived(getParam('review_status'));
  const selectedExecutionStatuses = $derived(getParam('execution_status'));
  const selectedPlansLastRun = $derived(getParam('plans_last_run'));

  // Compute available options from store data
  const environmentOptions = $derived(
    [...new Set(store.allEnvironments.map((e) => e.name))].sort(),
  );

  const testPlanOptions = $derived(
    [...new Set(
      store.enrichedExecutions.map((ee) => ee.testExecution.test_plan).filter(Boolean),
    )].sort(),
  );

  // Compute review status options from actual data
  const reviewStatusOptions = $derived.by(() => {
    const statuses = new Set<string>();
    for (const env of store.allEnvironments) {
      const decisions = env.review.review_decision;
      if (decisions.length === 0) {
        statuses.add('Undecided');
      } else if (decisions.includes('REJECTED')) {
        statuses.add('Rejected');
      } else {
        statuses.add('Approved');
      }
    }
    return [...statuses].sort();
  });

  // Compute execution status options from actual data
  const executionStatusOptions = $derived.by(() => {
    const statuses = new Set<string>();
    for (const env of store.allEnvironments) {
      for (const run of env.runsDescending) {
        statuses.add(run.status);
      }
    }
    return [...statuses] as TestExecutionStatus[];
  });

  // Plans whose last run — derive from actual data
  const plansLastRunOptions = $derived.by(() => {
    const statuses = new Set<string>();
    for (const env of store.allEnvironments) {
      const latest = env.runsDescending[0];
      if (latest) statuses.add(latest.status);
    }
    return [...statuses] as TestExecutionStatus[];
  });

  // Count active filters
  const activeFilterCount = $derived(
    selectedEnvironments.length +
    selectedTestPlans.length +
    selectedReviewStatuses.length +
    selectedExecutionStatuses.length +
    selectedPlansLastRun.length,
  );

  function updateFilter(key: string, values: string[]) {
    const url = new URL(page.url);
    if (values.length === 0) {
      url.searchParams.delete(key);
    } else {
      url.searchParams.set(key, values.map(encodeURIComponent).join(','));
    }
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  function clearAll() {
    const url = new URL(page.url);
    ['environment', 'test_plan', 'review_status', 'execution_status', 'plans_last_run'].forEach(
      (k) => url.searchParams.delete(k),
    );
    goto(url.toString(), { replaceState: true, noScroll: true });
  }

  function toggleCheckbox(key: string, value: string, currentValues: string[]) {
    if (currentValues.includes(value)) {
      updateFilter(key, currentValues.filter((v) => v !== value));
    } else {
      updateFilter(key, [...currentValues, value]);
    }
  }
</script>

<section class="side-filters">
  <Expandable titleText="Environment" open={selectedEnvironments.length > 0}>
    <SearchableMultiSelect
      options={environmentOptions}
      selected={selectedEnvironments}
      onchange={(vals) => updateFilter('environment', vals)}
      placeholder="Search environments..."
    />
  </Expandable>

  <Expandable titleText="Test Plan" open={selectedTestPlans.length > 0}>
    <SearchableMultiSelect
      options={testPlanOptions}
      selected={selectedTestPlans}
      onchange={(vals) => updateFilter('test_plan', vals)}
      placeholder="Search test plans..."
    />
  </Expandable>

  <Expandable titleText="Review status" open={true}>
    <div class="checkbox-list">
      {#each reviewStatusOptions as opt (opt)}
        <label class="checkbox-row">
          <input
            type="checkbox"
            checked={selectedReviewStatuses.includes(opt)}
            onchange={() => toggleCheckbox('review_status', opt, selectedReviewStatuses)}
          />
          {opt}
        </label>
      {/each}
    </div>
  </Expandable>

  <Expandable titleText="Test Execution Status" open={true}>
    <div class="checkbox-list">
      {#each executionStatusOptions as opt (opt)}
        <label class="checkbox-row">
          <input
            type="checkbox"
            checked={selectedExecutionStatuses.includes(opt)}
            onchange={() => toggleCheckbox('execution_status', opt, selectedExecutionStatuses)}
          />
          {opt.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase())}
        </label>
      {/each}
    </div>
  </Expandable>

  <Expandable titleText="Plans whose last run" open={true}>
    <div class="checkbox-list">
      {#each plansLastRunOptions as opt (opt)}
        <label class="checkbox-row">
          <input
            type="checkbox"
            checked={selectedPlansLastRun.includes(opt)}
            onchange={() => toggleCheckbox('plans_last_run', opt, selectedPlansLastRun)}
          />
          {opt.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase())}
        </label>
      {/each}
    </div>
  </Expandable>

  <Expandable titleText="Test Execution Triaged" open={true}>
    <div class="checkbox-list">
      <label class="checkbox-row">
        <input
          type="checkbox"
          checked={page.url.searchParams.get('triaged') === 'Yes'}
          onchange={() => {
            const url = new URL(page.url);
            if (url.searchParams.get('triaged') === 'Yes') url.searchParams.delete('triaged');
            else url.searchParams.set('triaged', 'Yes');
            goto(url.toString(), { replaceState: true, noScroll: true });
          }}
        />
        Yes
      </label>
      <label class="checkbox-row">
        <input
          type="checkbox"
          checked={page.url.searchParams.get('triaged') === 'No'}
          onchange={() => {
            const url = new URL(page.url);
            if (url.searchParams.get('triaged') === 'No') url.searchParams.delete('triaged');
            else url.searchParams.set('triaged', 'No');
            goto(url.toString(), { replaceState: true, noScroll: true });
          }}
        />
        No
      </label>
    </div>
  </Expandable>
</section>

<style>
  .side-filters {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .filters-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 8px 8px;
  }

  .section-title {
    margin: 0;
    font-size: 13px;
    font-weight: 500;
    color: #333;
  }

  .clear-btn {
    all: unset;
    font-size: 12px;
    color: #E95420;
    cursor: pointer;
  }

  .clear-btn:hover {
    text-decoration: underline;
  }

  .checkbox-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .checkbox-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    cursor: pointer;
    padding: 2px 0;
  }

  .checkbox-row:hover {
    color: #E95420;
  }
</style>
