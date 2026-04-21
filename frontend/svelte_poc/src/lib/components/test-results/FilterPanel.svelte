<script lang="ts">
  import { goto } from '$app/navigation';
  import { base } from '$app/paths';
  import SearchableMultiSelect from '$lib/components/ui/SearchableMultiSelect.svelte';
  import AsyncMultiSelect from '$lib/components/ui/AsyncMultiSelect.svelte';
  import { TEST_RESULT_STATUSES } from '$lib/types/test-results';
  import type { IssueFilterMode, AssigneeFilterMode } from '$lib/types/test-results';
  import type { TestResultsStore } from '$lib/stores/test-results.svelte';
  import { serializeFilters } from '$lib/stores/test-results.svelte';

  interface Props {
    store: TestResultsStore;
  }

  let { store }: Props = $props();

  const familyOptions = ['snap', 'deb', 'charm', 'image'];
  const statusOptions = [...TEST_RESULT_STATUSES];

  function apply() {
    const params = serializeFilters(store.workingFilters);
    goto(`${base}/test-results?${params}`, { replaceState: false });
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

  function setIssueMode(mode: IssueFilterMode) {
    store.workingFilters = {
      ...store.workingFilters,
      issueMode: mode,
      issueIds: mode !== 'specific' ? [] : store.workingFilters.issueIds,
    };
  }

  function setIssueIds(selected: string[]) {
    store.workingFilters = {
      ...store.workingFilters,
      issueIds: selected.map(Number).filter((n) => !isNaN(n)),
    };
  }

  function setAssigneeMode(mode: AssigneeFilterMode) {
    store.workingFilters = {
      ...store.workingFilters,
      assigneeMode: mode,
      assigneeIds: mode !== 'specific' ? [] : store.workingFilters.assigneeIds,
    };
  }

  function setAssigneeIds(selected: string[]) {
    store.workingFilters = {
      ...store.workingFilters,
      assigneeIds: selected.map(Number).filter((n) => !isNaN(n)),
    };
  }

  function setMetadata(selected: string[]) {
    store.workingFilters = { ...store.workingFilters, metadata: selected };
  }

  function toggleMetadataItem(encoded: string) {
    const current = store.workingFilters.metadata;
    if (current.includes(encoded)) {
      setMetadata(current.filter((m) => m !== encoded));
    } else {
      setMetadata([...current, encoded]);
    }
  }

  function encodeMetadata(category: string, value: string): string {
    return `${btoa(category)}:${btoa(value)}`;
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

  async function fetchIssueOptions(q: string) {
    const issues = await store.loadIssues(q);
    return issues.map((i) => ({ label: `${i.key} — ${i.title}`, value: String(i.id) }));
  }

  async function fetchAssigneeOptions(q: string) {
    await store.loadUsers();
    const lower = q.toLowerCase();
    return store.cachedUsers
      .filter((u) => u.name.toLowerCase().includes(lower) || u.email.toLowerCase().includes(lower))
      .map((u) => ({ label: u.name || u.email, value: String(u.id) }));
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

  <!-- Family -->
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

  <!-- Status -->
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

  <!-- Artefact -->
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

  <!-- Environment -->
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

  <!-- Test Case -->
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

  <!-- Issues -->
  <details>
    <summary>Issues</summary>
    <div class="filter-body">
      <div class="radio-group">
        <label>
          <input type="radio" name="issue-mode" checked={store.workingFilters.issueMode === 'any_value'} onchange={() => setIssueMode('any_value')} />
          Any value
        </label>
        <label>
          <input type="radio" name="issue-mode" checked={store.workingFilters.issueMode === 'has_any'} onchange={() => setIssueMode('has_any')} />
          Has any issue
        </label>
        <label>
          <input type="radio" name="issue-mode" checked={store.workingFilters.issueMode === 'has_none'} onchange={() => setIssueMode('has_none')} />
          Has no issues
        </label>
        <label>
          <input type="radio" name="issue-mode" checked={store.workingFilters.issueMode === 'specific'} onchange={() => setIssueMode('specific')} />
          Specific issues
        </label>
      </div>
      {#if store.workingFilters.issueMode === 'specific'}
        <AsyncMultiSelect
          fetchOptions={fetchIssueOptions}
          selected={store.workingFilters.issueIds.map(String)}
          onchange={setIssueIds}
          placeholder="Search issues..."
          minChars={1}
        />
      {/if}
    </div>
  </details>

  <!-- Assignees -->
  <details>
    <summary>Assignee</summary>
    <div class="filter-body">
      <div class="radio-group">
        <label>
          <input type="radio" name="assignee-mode" checked={store.workingFilters.assigneeMode === 'any_value'} onchange={() => setAssigneeMode('any_value')} />
          Any value
        </label>
        <label>
          <input type="radio" name="assignee-mode" checked={store.workingFilters.assigneeMode === 'has_any'} onchange={() => setAssigneeMode('has_any')} />
          Has any assignee
        </label>
        <label>
          <input type="radio" name="assignee-mode" checked={store.workingFilters.assigneeMode === 'has_none'} onchange={() => setAssigneeMode('has_none')} />
          Has no assignee
        </label>
        <label>
          <input type="radio" name="assignee-mode" checked={store.workingFilters.assigneeMode === 'specific'} onchange={() => setAssigneeMode('specific')} />
          Specific assignees
        </label>
      </div>
      {#if store.workingFilters.assigneeMode === 'specific'}
        <AsyncMultiSelect
          fetchOptions={fetchAssigneeOptions}
          selected={store.workingFilters.assigneeIds.map(String)}
          onchange={setAssigneeIds}
          placeholder="Search assignees..."
          minChars={1}
        />
      {/if}
    </div>
  </details>

  <!-- Boolean filters -->
  <details>
    <summary>Archived</summary>
    <div class="filter-body">
      <select
        value={store.workingFilters.archived}
        onchange={(e) => { store.workingFilters = { ...store.workingFilters, archived: (e.target as HTMLSelectElement).value as 'any' | 'yes' | 'no' }; }}
      >
        <option value="any">Any</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </div>
  </details>

  <details>
    <summary>Rerun Requested</summary>
    <div class="filter-body">
      <select
        value={store.workingFilters.rerunRequested}
        onchange={(e) => { store.workingFilters = { ...store.workingFilters, rerunRequested: (e.target as HTMLSelectElement).value as 'any' | 'yes' | 'no' }; }}
      >
        <option value="any">Any</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </div>
  </details>

  <details>
    <summary>Execution Version</summary>
    <div class="filter-body">
      <select
        value={store.workingFilters.executionIsLatest}
        onchange={(e) => { store.workingFilters = { ...store.workingFilters, executionIsLatest: (e.target as HTMLSelectElement).value as 'any' | 'yes' | 'no' }; }}
      >
        <option value="any">Any</option>
        <option value="yes">Latest only</option>
        <option value="no">Non-latest only</option>
      </select>
    </div>
  </details>

  <!-- Date filters -->
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

  <!-- Metadata -->
  {#if Object.keys(store.metadataOptions).length > 0}
    <details>
      <summary>Metadata</summary>
      <div class="filter-body metadata-body">
        {#each Object.entries(store.metadataOptions) as [category, values] (category)}
          <div class="metadata-group">
            <div class="metadata-category">{category}</div>
            {#each values as value (value)}
              {@const encoded = encodeMetadata(category, value)}
              <label class="option-row">
                <input
                  type="checkbox"
                  checked={store.workingFilters.metadata.includes(encoded)}
                  onchange={() => toggleMetadataItem(encoded)}
                />
                <span class="option-label">{value}</span>
              </label>
            {/each}
          </div>
        {/each}
      </div>
    </details>
  {/if}
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

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 8px;
  }

  .radio-group label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    cursor: pointer;
  }

  select {
    width: 100%;
    padding: 5px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    background: white;
  }

  select:focus {
    border-color: #E95420;
    outline: none;
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

  .metadata-body {
    max-height: 300px;
    overflow-y: auto;
  }

  .metadata-group {
    margin-bottom: 8px;
  }

  .metadata-category {
    font-weight: 500;
    color: #555;
    font-size: 12px;
    margin-bottom: 2px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .option-row {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 4px;
    cursor: pointer;
    border-radius: 3px;
    font-size: 13px;
  }

  .option-row:hover {
    background: #f0f0f0;
  }

  .option-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
