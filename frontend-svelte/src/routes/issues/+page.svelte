<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";
  import { Breadcrumbs, SearchBox, Spinner } from "@canonical/svelte-ds-app-launchpad";
  import { IssueCard } from "$lib/components/issues/index.js";
  import { patchIssue } from "$lib/api/issues.js";

  let { data } = $props();

  let searchQuery = $state("");

  $effect(() => {
    searchQuery = data.searchQuery ?? "";
  });

  const filteredIssues = $derived(
    searchQuery.trim()
      ? data.issues.filter((issue) => {
          const q = searchQuery.toLowerCase();
          return (
            issue.title.toLowerCase().includes(q) ||
            issue.key.toLowerCase().includes(q) ||
            issue.project.toLowerCase().includes(q)
          );
        })
      : data.issues,
  );

  async function handleAutoRerunChange(issueId: number, enabled: boolean): Promise<void> {
    try {
      await patchIssue(issueId, { autoRerunEnabled: enabled });
    } catch {
      // Revert optimistic update on failure by reloading
      goto(`${base}/issues`);
    }
  }

  const breadcrumbSegments = [{ label: "Issues", href: `${base}/issues` }];
</script>

<svelte:head>
  <title>Issues — Test Observer</title>
</svelte:head>

<div class="ds issues-page">
  <Breadcrumbs segments={breadcrumbSegments} />

  <h1>Linked External Issues</h1>

  <div class="ds issues-page__toolbar">
    <SearchBox
      aria-label="Search issues by title, key, or project"
      bind:value={searchQuery}
      placeholder="Search issues..."
    />
    <span class="ds issues-page__count">
      {filteredIssues.length} issue{filteredIssues.length !== 1 ? "s" : ""}
    </span>
  </div>

  {#if data.issues.length === 0}
    <div class="ds issues-page__empty">
      <p>No issues found.</p>
    </div>
  {:else if filteredIssues.length === 0}
    <div class="ds issues-page__empty">
      <p>No issues match your search.</p>
    </div>
  {:else}
    <div class="ds issues-page__list">
      {#each filteredIssues as issue (issue.id)}
        <IssueCard {issue} onautorerunchange={handleAutoRerunChange} />
      {/each}
    </div>
  {/if}
</div>

<style>
  .ds.issues-page {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .ds.issues-page__toolbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .ds.issues-page__count {
    font-size: 0.85rem;
    color: var(--color-text-muted, #666);
    white-space: nowrap;
  }

  .ds.issues-page__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ds.issues-page__empty {
    text-align: center;
    padding: 2rem;
    color: var(--color-text-muted, #666);
  }
</style>
