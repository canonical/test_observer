<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Table, Spinner } from "@canonical/svelte-ds-app-launchpad";
  import { base } from "$app/paths";
  import type { TestResultWithContext, TestResultsSearchResult } from "$lib/types/test-result.js";
  import TestResultStatusChip from "./TestResultStatusChip.svelte";
  import { formatDate } from "$lib/utils/formatting.js";

  interface Props {
    results: TestResultsSearchResult;
    selectedIds: Set<number>;
    onselectionchange: (ids: Set<number>) => void;
    onloadmore: () => void;
    loading?: boolean;
  }

  const { results, selectedIds, onselectionchange, onloadmore, loading = false }: Props = $props();

  const allSelected = $derived(
    results.testResults.length > 0 &&
      results.testResults.every((r) => selectedIds.has(r.testResult.id)),
  );

  function toggleAll(): void {
    if (allSelected) {
      onselectionchange(new Set());
    } else {
      onselectionchange(new Set(results.testResults.map((r) => r.testResult.id)));
    }
  }

  function toggleRow(id: number): void {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    onselectionchange(next);
  }

  function artefactHref(row: TestResultWithContext): string {
    return `${base}/${row.artefact.family}/${row.artefact.id}`;
  }

  let expandedId = $state<number | null>(null);

  function toggleExpand(id: number): void {
    expandedId = expandedId === id ? null : id;
  }

  const headers = [
    { label: "", key: "select" },
    { label: "Test Name", key: "name" },
    { label: "Status", key: "status" },
    { label: "Category", key: "category" },
    { label: "Artefact", key: "artefact" },
    { label: "Environment", key: "environment" },
    { label: "Version", key: "version" },
    { label: "Date", key: "date" },
  ];

  const hasMore = $derived(results.testResults.length < results.count);
</script>

<div class="ds test-results-table">
  <div class="ds test-results-table__summary">
    <span>
      Found {results.count} results (showing {results.testResults.length})
    </span>
  </div>

  <table class="ds test-results-table__table">
    <thead>
      <tr>
        <th class="ds test-results-table__th--checkbox">
          <input
            type="checkbox"
            checked={allSelected}
            aria-label="Select all results"
            onchange={toggleAll}
          />
        </th>
        {#each headers.slice(1) as header (header.key)}
          <th>{header.label}</th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each results.testResults as row (row.testResult.id)}
        {@const selected = selectedIds.has(row.testResult.id)}
        {@const expanded = expandedId === row.testResult.id}
        <tr
          class:ds-selected={selected}
          onclick={() => toggleExpand(row.testResult.id)}
          aria-expanded={expanded}
        >
          <td class="ds test-results-table__td--checkbox" onclick={(e) => e.stopPropagation()}>
            <input
              type="checkbox"
              checked={selected}
              aria-label="Select {row.testResult.name}"
              onchange={() => toggleRow(row.testResult.id)}
            />
          </td>
          <td>{row.testResult.name}</td>
          <td>
            <TestResultStatusChip status={row.testResult.status} />
          </td>
          <td>{row.testResult.category}</td>
          <td>
            <a
              href={artefactHref(row)}
              onclick={(e) => e.stopPropagation()}
            >
              {row.artefact.name}
            </a>
          </td>
          <td>
            {row.testExecution.environment.architecture} / {row.testExecution.environment.name}
          </td>
          <td>{row.artefact.version}</td>
          <td>{formatDate(row.testResult.createdAt)}</td>
        </tr>
        {#if expanded}
          <tr class="ds test-results-table__expanded-row">
            <td colspan={headers.length}>
              <div class="ds test-results-table__details">
                <div class="ds test-results-table__detail-section">
                  <strong>IO Log</strong>
                  {#if row.testResult.ioLog}
                    <pre class="ds test-results-table__log">{row.testResult.ioLog}</pre>
                  {:else}
                    <p class="ds test-results-table__empty">No IO log available</p>
                  {/if}
                </div>

                {#if row.testResult.previousResults.length > 0}
                  <div class="ds test-results-table__detail-section">
                    <strong>Previous Results</strong>
                    <ul class="ds test-results-table__prev-results">
                      {#each row.testResult.previousResults as prev (prev.testResultId)}
                        <li>
                          <TestResultStatusChip status={prev.status} />
                          <span>v{prev.version}</span>
                        </li>
                      {/each}
                    </ul>
                  </div>
                {/if}

                {#if row.testResult.issueAttachments.length > 0}
                  <div class="ds test-results-table__detail-section">
                    <strong>Attached Issues</strong>
                    <ul>
                      {#each row.testResult.issueAttachments as attachment (attachment.issue.id)}
                        <li>
                          <a
                            href={attachment.issue.url}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {attachment.issue.url}
                          </a>
                        </li>
                      {/each}
                    </ul>
                  </div>
                {/if}

                <div class="ds test-results-table__detail-section">
                  <strong>Template ID:</strong> {row.testResult.templateId || "—"}
                </div>

                <div class="ds test-results-table__detail-section">
                  <strong>Test Plan:</strong> {row.testExecution.testPlan || "—"}
                </div>
              </div>
            </td>
          </tr>
        {/if}
      {/each}
    </tbody>
  </table>

  {#if loading}
    <div class="ds test-results-table__loading">
      <Spinner />
    </div>
  {/if}

  {#if results.testResults.length === 0 && !loading}
    <div class="ds test-results-table__empty-state">
      <p>No results found. Adjust your filters and try again.</p>
    </div>
  {/if}

  {#if hasMore && !loading}
    <div class="ds test-results-table__load-more">
      <button class="ds test-results-table__load-more-btn" onclick={onloadmore}>
        Load more results
      </button>
    </div>
  {/if}
</div>

<style>
  .ds.test-results-table__summary {
    padding: 0.5rem 0;
    font-size: 0.875rem;
    color: var(--color-text-muted, #666);
  }

  .ds.test-results-table__table {
    width: 100%;
    border-collapse: collapse;
  }

  .ds.test-results-table__table th,
  .ds.test-results-table__table td {
    padding: 0.5rem 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.test-results-table__table th {
    font-weight: 600;
    font-size: 0.875rem;
    background: var(--color-background-alt, #f7f7f7);
  }

  .ds.test-results-table__table tbody tr {
    cursor: pointer;
  }

  .ds.test-results-table__table tbody tr:hover {
    background: var(--color-background-alt, #f7f7f7);
  }

  .ds.test-results-table__table tr.ds-selected {
    background: var(--color-positive-background, #e6f5e6);
  }

  .ds.test-results-table__th--checkbox,
  .ds.test-results-table__td--checkbox {
    width: 2.5rem;
    text-align: center;
  }

  .ds.test-results-table__expanded-row td {
    background: var(--color-background-alt, #f7f7f7);
    padding: 1rem;
  }

  .ds.test-results-table__details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .ds.test-results-table__detail-section {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .ds.test-results-table__log {
    max-height: 20rem;
    overflow: auto;
    padding: 0.5rem;
    background: var(--color-background, #fff);
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    font-size: 0.75rem;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .ds.test-results-table__prev-results {
    list-style: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .ds.test-results-table__prev-results li {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .ds.test-results-table__loading {
    display: flex;
    justify-content: center;
    padding: 2rem;
  }

  .ds.test-results-table__empty-state {
    text-align: center;
    padding: 2rem;
    color: var(--color-text-muted, #666);
  }

  .ds.test-results-table__load-more {
    display: flex;
    justify-content: center;
    padding: 1rem;
  }

  .ds.test-results-table__load-more-btn {
    padding: 0.5rem 1.5rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background: var(--color-background, #fff);
    cursor: pointer;
    font-size: 0.875rem;
  }

  .ds.test-results-table__load-more-btn:hover {
    background: var(--color-background-alt, #f7f7f7);
  }

  .ds.test-results-table__empty {
    color: var(--color-text-muted, #666);
    font-style: italic;
  }
</style>
