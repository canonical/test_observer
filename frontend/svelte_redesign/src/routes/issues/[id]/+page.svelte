<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { invalidateAll } from "$app/navigation";
  import { base } from "$app/paths";
  import { Breadcrumbs, Chip, Link, Switch, Button } from "@canonical/svelte-ds-app-launchpad";
  import { AttachmentRuleRow, AttachmentRuleDialog } from "$lib/components/issues/index.js";
  import {
    patchIssue,
    createAttachmentRule,
    patchAttachmentRule,
    deleteAttachmentRule,
  } from "$lib/api/issues.js";
  import type { AttachmentRule } from "$lib/types/attachment-rule.js";
  import type { IssueSource, IssueStatus } from "$lib/types/issue.js";
  import type { TestResultStatus } from "$lib/types/test-result.js";
  import { capitalize } from "$lib/utils/formatting.js";

  let { data } = $props();

  let autoRerun = $state(false);
  let showRuleDialog = $state(false);
  let editingRule = $state<AttachmentRule | undefined>(undefined);
  let deleteConfirmRuleId = $state<number | null>(null);

  $effect(() => {
    autoRerun = data.issue.autoRerunEnabled;
  });

  function sourceSeverity(source: IssueSource): "positive" | "caution" | "information" {
    switch (source) {
      case "github":
        return "positive";
      case "jira":
        return "caution";
      case "launchpad":
        return "information";
    }
  }

  function statusSeverity(status: IssueStatus): "positive" | "negative" | "caution" {
    switch (status) {
      case "open":
        return "positive";
      case "closed":
        return "negative";
      case "unknown":
        return "caution";
    }
  }

  async function handleAutoRerunToggle(): Promise<void> {
    const newVal = !autoRerun;
    autoRerun = newVal;
    try {
      await patchIssue(data.issue.id, { autoRerunEnabled: newVal });
    } catch {
      autoRerun = !newVal;
    }
  }

  async function handleRuleEnabledChange(ruleId: number, enabled: boolean): Promise<void> {
    try {
      await patchAttachmentRule(data.issue.id, ruleId, { enabled });
      await invalidateAll();
    } catch {
      await invalidateAll();
    }
  }

  function handleEditRule(ruleId: number): void {
    editingRule = data.issue.attachmentRules.find((r) => r.id === ruleId);
    showRuleDialog = true;
  }

  function handleDeleteRuleConfirm(ruleId: number): void {
    deleteConfirmRuleId = ruleId;
  }

  async function handleDeleteRule(): Promise<void> {
    if (deleteConfirmRuleId === null) return;
    try {
      await deleteAttachmentRule(data.issue.id, deleteConfirmRuleId);
      await invalidateAll();
    } catch {
      // Silently handle - invalidate will refresh state
      await invalidateAll();
    }
    deleteConfirmRuleId = null;
  }

  function handleCancelDelete(): void {
    deleteConfirmRuleId = null;
  }

  function handleNewRule(): void {
    editingRule = undefined;
    showRuleDialog = true;
  }

  function handleCancelRuleDialog(): void {
    showRuleDialog = false;
    editingRule = undefined;
  }

  async function handleSaveRule(ruleData: {
    families: string[];
    environmentNames: string[];
    testCaseNames: string[];
    templateIds: string[];
    testResultStatuses: TestResultStatus[];
    executionMetadata: { data: Record<string, string[]> };
  }): Promise<void> {
    try {
      if (editingRule) {
        await patchAttachmentRule(data.issue.id, editingRule.id, ruleData);
      } else {
        await createAttachmentRule(data.issue.id, ruleData);
      }
      await invalidateAll();
    } catch {
      await invalidateAll();
    }
    showRuleDialog = false;
    editingRule = undefined;
  }

  const breadcrumbSegments = $derived([
    { label: "Issues", href: `${base}/issues` },
    { label: `${data.issue.project} / ${data.issue.key}` },
  ]);
</script>

<svelte:head>
  <title>Issue #{data.issue.id} — Test Observer</title>
</svelte:head>

<div class="ds issue-detail-page">
  <Breadcrumbs segments={breadcrumbSegments} />

  <div class="ds issue-detail-page__header">
    <div class="ds issue-detail-page__meta">
      <Chip
        value={capitalize(data.issue.source)}
        severity={sourceSeverity(data.issue.source)}
        readonly
      />
      <span class="ds issue-detail-page__project">{data.issue.project}</span>
      <Link href={data.issue.url} target="_blank" rel="noopener noreferrer">
        {data.issue.key}
      </Link>
    </div>

    <h1 class="ds issue-detail-page__title">{data.issue.title}</h1>

    <div class="ds issue-detail-page__status-row">
      <Chip
        value={capitalize(data.issue.status)}
        severity={statusSeverity(data.issue.status)}
        readonly
      />
      <label class="ds issue-detail-page__auto-rerun">
        <Switch checked={autoRerun} onchange={handleAutoRerunToggle} />
        Auto-rerun
      </label>
    </div>
  </div>

  <section class="ds issue-detail-page__rules">
    <div class="ds issue-detail-page__rules-header">
      <h2>Attachment Rules</h2>
      <Button onclick={handleNewRule}>Add Attachment Rule</Button>
    </div>

    {#if data.issue.attachmentRules.length === 0}
      <p class="ds issue-detail-page__empty">No attachment rules configured.</p>
    {:else}
      <div class="ds issue-detail-page__rules-list">
        {#each data.issue.attachmentRules as rule (rule.id)}
          <AttachmentRuleRow
            {rule}
            expanded={data.activeAttachmentRuleId === rule.id}
            onenabledchange={handleRuleEnabledChange}
            onedit={handleEditRule}
            ondelete={handleDeleteRuleConfirm}
          />
        {/each}
      </div>
    {/if}
  </section>
</div>

{#if showRuleDialog}
  <AttachmentRuleDialog
    familyOptions={data.familyOptions}
    existingRule={editingRule}
    onsave={handleSaveRule}
    oncancel={handleCancelRuleDialog}
  />
{/if}

{#if deleteConfirmRuleId !== null}
  <div class="ds issue-detail-page__confirm-overlay" role="dialog" aria-label="Confirm deletion">
    <div
      class="ds issue-detail-page__confirm-backdrop"
      role="presentation"
      onclick={handleCancelDelete}
    ></div>
    <div class="ds issue-detail-page__confirm-content">
      <h3>Delete Attachment Rule</h3>
      <p>Are you sure you want to delete rule #{deleteConfirmRuleId}?</p>
      <div class="ds issue-detail-page__confirm-actions">
        <Button onclick={handleCancelDelete}>Cancel</Button>
        <Button severity="negative" onclick={handleDeleteRule}>Delete</Button>
      </div>
    </div>
  </div>
{/if}

<style>
  .ds.issue-detail-page {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 1rem;
  }

  .ds.issue-detail-page__header {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ds.issue-detail-page__meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .ds.issue-detail-page__project {
    font-weight: 500;
  }

  .ds.issue-detail-page__title {
    margin: 0;
  }

  .ds.issue-detail-page__status-row {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .ds.issue-detail-page__auto-rerun {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .ds.issue-detail-page__rules {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .ds.issue-detail-page__rules-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .ds.issue-detail-page__rules-header h2 {
    margin: 0;
  }

  .ds.issue-detail-page__rules-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ds.issue-detail-page__empty {
    color: var(--color-text-muted, #666);
    text-align: center;
    padding: 1rem;
  }

  .ds.issue-detail-page__confirm-overlay {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ds.issue-detail-page__confirm-backdrop {
    position: absolute;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.4);
  }

  .ds.issue-detail-page__confirm-content {
    position: relative;
    background: var(--color-background, #fff);
    border-radius: 0.5rem;
    padding: 1.5rem;
    max-width: 28rem;
    width: 90vw;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  }

  .ds.issue-detail-page__confirm-content h3 {
    margin: 0 0 0.5rem;
  }

  .ds.issue-detail-page__confirm-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1rem;
  }
</style>
