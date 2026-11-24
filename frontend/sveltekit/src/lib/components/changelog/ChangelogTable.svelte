<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import type { AuditHistoryResponse } from "$lib/types/openapi";
  import { operationLabel, pageHref, PAGE_SIZE } from "$lib/utils/changelog";
  import AuditJsonButton from "./AuditJsonButton.svelte";

  interface Props {
    history: AuditHistoryResponse;
    url: string;
    detailBase: string;
    artefactId: number;
    reviewId?: number;
  }
  let { history, url, detailBase, artefactId, reviewId }: Props = $props();
  const currentPage = $derived(Math.floor(history.offset / PAGE_SIZE) + 1);
</script>

{#if history.count === 0}
  <p>No changelog entries found.</p>
{:else}
  {#if history.entries.length === 0}
    <p>No entries on this page.</p>
  {:else}
    <div class="table-container">
      <table>
        <thead
          ><tr
            ><th>Date</th><th>Operation</th><th>Author</th><th>Actions</th></tr
          ></thead
        >
        <tbody>
          {#each history.entries as entry (entry.id)}
            <tr>
              <td
                ><time datetime={entry.created_at}
                  >{new Date(entry.created_at).toLocaleString()}</time
                ></td
              >
              <td>{operationLabel(entry.operation)}</td>
              <td
                >{entry.author.name ??
                  entry.author.automation_name ??
                  "Unknown"}{entry.author.kind
                  ? ` (${entry.author.kind})`
                  : ""}</td
              >
              <td>
                <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
                <a href={`${detailBase}/${entry.id}`}>Detail</a>
                <AuditJsonButton {artefactId} {reviewId} auditId={entry.id} />
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
  <nav aria-label="Changelog pagination">
    {#if currentPage > 1}<a href={pageHref(url, currentPage - 1)}>Previous</a
      >{/if}
    <span>Page {currentPage}</span>
    {#if history.offset + history.entries.length < history.count && history.entries.length > 0}
      <a href={pageHref(url, currentPage + 1)}>Next</a>
    {/if}
  </nav>
{/if}

<style>
  .table-container {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
  }
  th,
  td {
    padding: 12px;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
  }
  nav {
    display: flex;
    gap: 16px;
    align-items: center;
    margin-top: 16px;
  }
</style>
