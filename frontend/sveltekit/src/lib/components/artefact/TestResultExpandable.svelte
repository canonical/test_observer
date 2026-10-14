<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Chip, Link } from "@canonical/svelte-ds-app-launchpad";
  import { page } from "$app/state";
  import Expandable from "./Expandable.svelte";
  import ExecutionStatusChip from "./ExecutionStatusChip.svelte";
  import TestResultHistory from "./TestResultHistory.svelte";
  import type { TestResult } from "$lib/types/artefact-page";
  import type { TestReportedIssueResponse } from "$lib/types/openapi";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";

  interface Props {
    result: TestResult;
    store: ArtefactPageStore;
  }

  let { result, store }: Props = $props();

  const targetResultId = $derived.by(() => {
    const queryValue = page.url.searchParams.get("testResultId");
    if (!queryValue || !/^\d+$/.test(queryValue)) return null;

    const parsedId = Number(queryValue);
    return Number.isSafeInteger(parsedId) && parsedId > 0 ? parsedId : null;
  });

  let open = $state(false);

  $effect(() => {
    if (targetResultId === result.id) open = true;
  });

  // Test issues matching this test result's template_id or name
  const matchedTestIssues = $derived(
    store.testIssues.filter(
      (ti: TestReportedIssueResponse) =>
        (result.template_id && ti.template_id === result.template_id) ||
        (result.name && ti.case_name === result.name),
    ),
  );

  const issueCount = $derived(result.issues.length + matchedTestIssues.length);
</script>

<Expandable bind:open>
  {#snippet title()}
    <span class="result-title">
      <ExecutionStatusChip status={result.status} />
      <span class="result-name">{result.name}</span>
      {#if issueCount > 0}
        <span class="issue-badge">{issueCount}</span>
      {/if}
      <span class="spacer"></span>
      <TestResultHistory
        previousResults={result.previous_results}
        getHref={(previousResult) => {
          const pathSegments = page.url.pathname.split("/");
          const currentArtefactIndex =
            pathSegments[pathSegments.length - 1] === ""
              ? pathSegments.length - 2
              : pathSegments.length - 1;
          if (/^\d+$/.test(pathSegments[currentArtefactIndex] ?? "")) {
            pathSegments[currentArtefactIndex] = String(
              previousResult.artefact_id,
            );
          } else {
            pathSegments.splice(
              currentArtefactIndex + 1,
              0,
              String(previousResult.artefact_id),
            );
          }
          const query = [
            ...Array.from(page.url.searchParams.entries()).filter(
              ([key]) => key !== "testResultId" && key !== "testExecutionId",
            ),
            ["testResultId", String(previousResult.test_result_id)],
            ["testExecutionId", String(previousResult.test_execution_id)],
          ]
            .map(
              ([key, value]) =>
                `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
            )
            .join("&");
          return `${pathSegments.join("/")}?${query}${page.url.hash}`;
        }}
      />
    </span>
  {/snippet}

  <div class="result-details">
    {#if matchedTestIssues.length > 0}
      <div class="detail-section">
        <h5 class="detail-heading">Reported Test Issues</h5>
        {#each matchedTestIssues as ti (ti.id)}
          <div class="ti-row">
            <span class="ti-desc">{ti.description}</span>
            {#if ti.url}
              <Link href={ti.url}>URL</Link>
            {/if}
          </div>
        {/each}
      </div>
    {/if}

    {#if result.issues.length > 0}
      <div class="detail-section">
        <h5 class="detail-heading">Attached Issues</h5>
        {#each result.issues as attachment (attachment.issue.id)}
          <div class="attachment-row">
            <Chip
              value={attachment.issue.status}
              severity={attachment.issue.status === "open"
                ? "caution"
                : attachment.issue.status === "closed"
                  ? "positive"
                  : "neutral"}
              readonly
              density="dense"
            />
            <Link href={attachment.issue.url}>
              [{attachment.issue.source}] {attachment.issue.project} #{attachment
                .issue.key}
            </Link>
            <span class="att-title">{attachment.issue.title}</span>
          </div>
        {/each}
      </div>
    {/if}

    <div class="detail-section">
      {#if result.category}
        <div class="detail-row">
          <span class="detail-label">Category</span>
          <span class="detail-value">{result.category}</span>
        </div>
      {/if}
      {#if result.comment}
        <div class="detail-row">
          <span class="detail-label">Comment</span>
          <span class="detail-value">{result.comment}</span>
        </div>
      {/if}
      {#if result.io_log}
        <div class="detail-row column">
          <span class="detail-label">IO Log</span>
          <pre class="io-log">{result.io_log}</pre>
        </div>
      {/if}
    </div>
  </div>
</Expandable>

<style>
  .result-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .result-name {
    font-size: 0.85rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--lp-color-text-default);
    font-family: monospace;
  }

  .issue-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    border-radius: 9px;
    background: #c7162b;
    color: #fff;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0 4px;
    flex-shrink: 0;
  }

  .spacer {
    flex: 1;
  }

  .result-details {
    display: flex;
    flex-direction: column;
    gap: 10px;
    font-size: 0.85rem;
  }

  .detail-section {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .detail-heading {
    margin: 0;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--lp-color-text-muted);
  }

  .ti-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 2px 0;
  }

  .ti-desc {
    color: var(--lp-color-text-default);
  }

  .attachment-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 2px 0;
    flex-wrap: wrap;
  }

  .att-title {
    color: var(--lp-color-text-muted);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .detail-row {
    display: flex;
    gap: 8px;
    align-items: flex-start;
  }

  .detail-row.column {
    flex-direction: column;
    gap: 4px;
  }

  .detail-label {
    font-weight: 600;
    color: var(--lp-color-text-muted);
    min-width: 72px;
    flex-shrink: 0;
  }

  .detail-value {
    color: var(--lp-color-text-default);
    word-break: break-word;
  }

  .io-log {
    margin: 0;
    padding: 8px;
    background: var(--lp-color-background-alt);
    border: 1px solid var(--lp-color-border-low-contrast);
    border-radius: 4px;
    font-size: 0.75rem;
    white-space: pre-wrap;
    word-break: break-word;
    color: var(--lp-color-text-default);
    max-height: 300px;
    overflow-y: auto;
    font-family: monospace;
  }
</style>
