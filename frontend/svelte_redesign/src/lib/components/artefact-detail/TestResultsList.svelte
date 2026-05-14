<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Chip } from "@canonical/svelte-ds-app-launchpad";
  import type { TestResult, TestResultStatus } from "$lib/types/test-result.js";

  interface Props {
    results: TestResult[];
  }

  const { results }: Props = $props();

  function resultSeverity(status: TestResultStatus): "positive" | "negative" | "neutral" {
    if (status === "PASSED") return "positive";
    if (status === "FAILED") return "negative";
    return "neutral";
  }
</script>

<div class="ds test-results-list">
  <h4 class="ds test-results-list__heading">Test Results ({results.length})</h4>
  <table class="ds test-results-list__table">
    <thead>
      <tr>
        <th scope="col">Status</th>
        <th scope="col">Name</th>
        <th scope="col">Category</th>
      </tr>
    </thead>
    <tbody>
      {#each results as result (result.id)}
        <tr>
          <td><Chip value={result.status} severity={resultSeverity(result.status)} readonly /></td>
          <td>{result.name}</td>
          <td>{result.category}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .ds.test-results-list {
    margin-bottom: 1rem;
  }

  .ds.test-results-list__heading {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .ds.test-results-list__table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  .ds.test-results-list__table th,
  .ds.test-results-list__table td {
    padding: 0.375rem 0.5rem;
    text-align: left;
    border-bottom: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.test-results-list__table th {
    font-weight: 600;
    color: var(--color-text-muted, #666);
  }
</style>
