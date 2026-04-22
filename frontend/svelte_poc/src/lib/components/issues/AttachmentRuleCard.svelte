<script lang="ts">
  import { base } from '$app/paths';
  import type { AttachmentRule } from '$lib/types/issues';

  interface Props {
    rule: AttachmentRule;
    expanded?: boolean;
    onenable: (ruleId: number) => void;
    ondisable: (ruleId: number) => void;
    ondelete: (ruleId: number) => void;
  }

  let { rule, expanded = false, onenable, ondisable, ondelete }: Props = $props();

  let isOpen = $state(expanded);

  function handleToggleEnabled() {
    if (rule.enabled) {
      ondisable(rule.id);
    } else {
      onenable(rule.id);
    }
  }

  function handleDelete() {
    if (window.confirm(`Delete attachment rule #${rule.id}? This cannot be undone.`)) {
      ondelete(rule.id);
    }
  }

  const metadataEntries = $derived(Object.entries(rule.execution_metadata));
  const hasCriteria = $derived(
    rule.families.length > 0 ||
      rule.environment_names.length > 0 ||
      rule.test_case_names.length > 0 ||
      rule.test_result_statuses.length > 0 ||
      rule.template_ids.length > 0 ||
      metadataEntries.length > 0,
  );

  const viewFiltersUrl = $derived.by(() => {
    const params = new URLSearchParams();
    for (const f of rule.families) params.append('families', f);
    for (const e of rule.environment_names) params.append('environments', e);
    for (const t of rule.test_case_names) params.append('testCases', t);
    for (const s of rule.test_result_statuses) params.append('statuses', s);
    return `${base}/test-results?${params}`;
  });
</script>

<div class="rule-card" class:disabled={!rule.enabled}>
  <details bind:open={isOpen}>
    <summary class="rule-summary">
      <span class="rule-id">Attachment Rule #{rule.id}</span>
      <span class="badge" class:badge-enabled={rule.enabled} class:badge-disabled={!rule.enabled}>
        {rule.enabled ? 'enabled' : 'disabled'}
      </span>
      <span class="rule-actions">
        {#if hasCriteria}
          <a class="btn-view-filters" href={viewFiltersUrl}>view filters</a>
        {/if}
        <button class="btn-toggle" onclick={handleToggleEnabled}>
          {rule.enabled ? 'disable' : 'enable'}
        </button>
        <button class="btn-delete" onclick={handleDelete}>delete</button>
      </span>
    </summary>
    <div class="rule-body">
      {#if !hasCriteria}
        <p class="no-criteria">No filter criteria (matches all test results)</p>
      {:else}
        <dl class="criteria-list">
          {#if rule.families.length > 0}
            <dt>Families</dt>
            <dd>{rule.families.join(', ')}</dd>
          {/if}
          {#if rule.environment_names.length > 0}
            <dt>Environments</dt>
            <dd>{rule.environment_names.join(', ')}</dd>
          {/if}
          {#if rule.test_case_names.length > 0}
            <dt>Test Cases</dt>
            <dd>{rule.test_case_names.join(', ')}</dd>
          {/if}
          {#if rule.test_result_statuses.length > 0}
            <dt>Statuses</dt>
            <dd>{rule.test_result_statuses.join(', ')}</dd>
          {/if}
          {#if rule.template_ids.length > 0}
            <dt>Template IDs</dt>
            <dd>{rule.template_ids.join(', ')}</dd>
          {/if}
          {#each metadataEntries as [category, values] (category)}
            <dt>{category}</dt>
            <dd>{values.join(', ')}</dd>
          {/each}
        </dl>
      {/if}
    </div>
  </details>
</div>

<style>
  .rule-card {
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    margin-bottom: 8px;
    background: white;
  }

  .rule-card.disabled {
    opacity: 0.7;
    background: #fafafa;
  }

  .rule-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    cursor: pointer;
    user-select: none;
    list-style: none;
    font-size: 13px;
  }

  .rule-summary::-webkit-details-marker {
    display: none;
  }

  .rule-summary::before {
    content: '▸';
    font-size: 11px;
    color: #999;
    transition: transform 0.15s;
  }

  details[open] > .rule-summary::before {
    content: '▾';
  }

  .rule-id {
    font-weight: 600;
    color: #333;
  }

  .badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
  }

  .badge-enabled {
    background: #e8f5e9;
    color: #0e8420;
  }

  .badge-disabled {
    background: #f5f5f5;
    color: #888;
  }

  .rule-actions {
    margin-left: auto;
    display: flex;
    gap: 12px;
  }

  .btn-toggle {
    background: none;
    border: none;
    padding: 0;
    font-size: 12px;
    cursor: pointer;
    color: #E95420;
    text-decoration: none;
    font-weight: 500;
  }

  .btn-toggle:hover {
    text-decoration: underline;
  }

  .btn-delete {
    background: none;
    border: none;
    padding: 0;
    font-size: 12px;
    cursor: pointer;
    color: #c7162b;
    text-decoration: none;
    font-weight: 500;
  }

  .btn-delete:hover {
    text-decoration: underline;
  }

  .btn-view-filters {
    font-size: 12px;
    color: #0645ad;
    text-decoration: none;
    font-weight: 500;
  }

  .btn-view-filters:hover {
    text-decoration: underline;
  }

  .rule-body {
    padding: 0 12px 12px 24px;
    font-size: 13px;
  }

  .no-criteria {
    color: #888;
    font-style: italic;
    margin: 0;
  }

  .criteria-list {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 4px 12px;
    margin: 0;
  }

  .criteria-list dt {
    font-weight: 500;
    color: #555;
  }

  .criteria-list dd {
    margin: 0;
    color: #333;
    word-break: break-word;
  }
</style>
