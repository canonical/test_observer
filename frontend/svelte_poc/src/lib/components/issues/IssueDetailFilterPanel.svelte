<script lang="ts">
  import SearchableMultiSelect from '$lib/components/ui/SearchableMultiSelect.svelte';
  import AsyncMultiSelect from '$lib/components/ui/AsyncMultiSelect.svelte';
  import { TEST_RESULT_STATUSES } from '$lib/types/test-results';
  import type { IssueDetailStore } from '$lib/stores/issue-detail.svelte';

  interface Props {
    store: IssueDetailStore;
  }

  let { store }: Props = $props();

  const familyOptions = ['snap', 'deb', 'charm', 'image'];
  const statusOptions = [...TEST_RESULT_STATUSES];

  function apply() {
    store.searchResults(store.workingFilters);
  }

  function reset() {
    store.workingFilters = JSON.parse(JSON.stringify(store.appliedFilters));
  }

  function setFamilies(selected: string[]) {
    store.workingFilters = { ...store.workingFilters, families: selected };
  }

  function setStatuses(selected: string[]) {
    store.workingFilters = { ...store.workingFilters, statuses: selected };
  }

  function setArtefacts(selected: string[]) {
    store.workingFilters = { ...store.workingFilters, artefacts: selected };
  }

  function setEnvironments(selected: string[]) {
    store.workingFilters = { ...store.workingFilters, environments: selected };
  }

  function setTestCases(selected: string[]) {
    store.workingFilters = { ...store.workingFilters, testCases: selected };
  }

  async function fetchArtefactOptions(q: string) {
    const results = await store.searchArtefacts(q, store.workingFilters.families);
    return results.map((name) => ({ label: name, value: name }));
  }

  async function fetchEnvironmentOptions(q: string) {
    const results = await store.searchEnvironments(q, store.workingFilters.families);
    return results.map((name) => ({ label: name, value: name }));
  }

  async function fetchTestCaseOptions(q: string) {
    const results = await store.searchTestCases(q, store.workingFilters.families);
    return results.map((name) => ({ label: name, value: name }));
  }
</script>

<aside class="filter-panel">
  <div class="filter-header">
    <h3>Filters</h3>
    <div class="filter-actions">
      <button class="btn-reset" onclick={reset} disabled={!store.filtersModified}>
        Reset
      </button>
      <button class="btn-apply" onclick={apply}>
        Apply
      </button>
    </div>
  </div>

  <details open>
    <summary>Family</summary>
    <div class="filter-body">
      <SearchableMultiSelect
        options={familyOptions}
        selected={store.workingFilters.families}
        onchange={setFamilies}
        placeholder="Filter families..."
      />
    </div>
  </details>

  <details open>
    <summary>Status</summary>
    <div class="filter-body">
      <SearchableMultiSelect
        options={statusOptions}
        selected={store.workingFilters.statuses}
        onchange={setStatuses}
        placeholder="Filter statuses..."
      />
    </div>
  </details>

  <details>
    <summary>Artefact</summary>
    <div class="filter-body">
      <AsyncMultiSelect
        fetchOptions={fetchArtefactOptions}
        selected={store.workingFilters.artefacts}
        onchange={setArtefacts}
        placeholder="Search artefacts..."
      />
    </div>
  </details>

  <details>
    <summary>Environment</summary>
    <div class="filter-body">
      <AsyncMultiSelect
        fetchOptions={fetchEnvironmentOptions}
        selected={store.workingFilters.environments}
        onchange={setEnvironments}
        placeholder="Search environments..."
      />
    </div>
  </details>

  <details>
    <summary>Test Case</summary>
    <div class="filter-body">
      <AsyncMultiSelect
        fetchOptions={fetchTestCaseOptions}
        selected={store.workingFilters.testCases}
        onchange={setTestCases}
        placeholder="Search test cases..."
      />
    </div>
  </details>

  <details>
    <summary>Date Range</summary>
    <div class="filter-body">
      <label class="date-label">
        From
        <input
          type="datetime-local"
          value={store.workingFilters.fromDate}
          oninput={(e) => { store.workingFilters = { ...store.workingFilters, fromDate: (e.target as HTMLInputElement).value }; }}
        />
      </label>
      <label class="date-label">
        Until
        <input
          type="datetime-local"
          value={store.workingFilters.untilDate}
          oninput={(e) => { store.workingFilters = { ...store.workingFilters, untilDate: (e.target as HTMLInputElement).value }; }}
        />
      </label>
    </div>
  </details>
</aside>

<style>
  .filter-panel {
    width: 280px;
    min-width: 280px;
    border-right: 1px solid #e0e0e0;
    overflow-y: auto;
    padding: 12px;
    font-size: 13px;
    background: #fafafa;
  }

  .filter-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .filter-header h3 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
  }

  .filter-actions {
    display: flex;
    gap: 6px;
  }

  .btn-apply {
    background: #E95420;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 12px;
    cursor: pointer;
    font-weight: 500;
  }

  .btn-apply:hover {
    background: #d4471a;
  }

  .btn-reset {
    background: none;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
    cursor: pointer;
    color: #555;
  }

  .btn-reset:hover:not(:disabled) {
    border-color: #999;
    color: #333;
  }

  .btn-reset:disabled {
    opacity: 0.4;
    cursor: default;
  }

  details {
    border-bottom: 1px solid #e8e8e8;
  }

  summary {
    padding: 8px 0;
    cursor: pointer;
    font-weight: 500;
    color: #333;
    user-select: none;
    list-style: none;
  }

  summary::before {
    content: '▸ ';
    font-size: 11px;
    color: #999;
  }

  details[open] > summary::before {
    content: '▾ ';
  }

  .filter-body {
    padding: 4px 0 12px 0;
  }

  .date-label {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 12px;
    color: #666;
    margin-bottom: 8px;
  }

  .date-label input {
    padding: 5px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
  }

  .date-label input:focus {
    border-color: #E95420;
    outline: none;
  }
</style>
