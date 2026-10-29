<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import { FetchError } from "$lib/api/client";
  import {
    deleteAttachmentRule,
    getIssue,
    issueErrorMessage,
    setAttachmentRuleEnabled,
  } from "$lib/api/issues";
  import {
    attachmentRuleCriteria,
    removeAttachmentRule,
    replaceAttachmentRule,
    viewRuleFiltersUrl,
  } from "$lib/issueDetailModel";
  import type { AttachmentRule, IssueDetail } from "$lib/types/issues";
  import IssueTestResults from "$lib/components/issues/IssueTestResults.svelte";
  import IssueAutoRerun from "$lib/components/issues/IssueAutoRerun.svelte";
  import {
    issueAutoRerunSession,
    issueAutoRerunUpdates as autoRerunUpdates,
  } from "$lib/issueAutoRerunUpdates";

  let { data } = $props();

  let issueId = $derived(page.params.issueId ?? "");
  let issue = $state<IssueDetail | null>(null);
  let loadState = $state<
    "loading" | "invalid" | "not-found" | "error" | "ready"
  >("loading");
  let loadError = $state("");
  let actionError = $state("");
  let busyRuleIds = $state<{ issueId: number; ruleId: number }[]>([]);
  let pendingDelete = $state<AttachmentRule | null>(null);
  let deleteDialog = $state<HTMLDialogElement | undefined>(undefined);
  let requestGeneration = 0;
  const autoRerunSession = $derived(issueAutoRerunSession());

  $effect(() => {
    const rawId = issueId;
    const session = autoRerunSession;
    const generation = ++requestGeneration;
    const current = () =>
      generation === requestGeneration && issueAutoRerunSession() === session;
    const unsubscribe = autoRerunUpdates.subscribe((event) => {
      if (
        event.type === "confirmed" &&
        current() &&
        issue?.id === event.issueId
      )
        issue = { ...issue, auto_rerun_enabled: event.enabled };
    });
    const cleanup = () => {
      ++requestGeneration;
      unsubscribe();
    };
    const id = Number(rawId);
    if (!/^[1-9]\d*$/.test(rawId) || !Number.isSafeInteger(id) || id <= 0) {
      issue = null;
      loadState = "invalid";
      loadError = "";
      actionError = "";
      pendingDelete = null;
      return cleanup;
    }

    issue = null;
    loadState = "loading";
    loadError = "";
    actionError = "";
    pendingDelete = null;
    const read = autoRerunUpdates.read(session, id);
    void getIssue(id)
      .then((response) => {
        if (!current()) return;
        issue = {
          ...response,
          auto_rerun_enabled: autoRerunUpdates.reconcile(
            read,
            response.auto_rerun_enabled,
          ),
        };
        loadState = "ready";
      })
      .catch(async (error: unknown) => {
        if (!current()) return;
        if (error instanceof FetchError && error.status === 404) {
          loadState = "not-found";
          loadError = "Issue not found.";
        } else {
          const message = await issueErrorMessage(error);
          if (!current()) return;
          loadState = "error";
          loadError = message;
        }
      });
    return cleanup;
  });

  function isCurrentIssue(issueId: number, generation: number): boolean {
    return (
      requestGeneration === generation &&
      page.params.issueId === String(issueId) &&
      issue?.id === issueId
    );
  }

  function updateIssueRules(rules: AttachmentRule[]) {
    if (issue) issue = { ...issue, attachment_rules: rules };
  }

  function isRuleBusy(ruleId: number): boolean {
    const currentIssue = issue;
    return (
      !!currentIssue &&
      busyRuleIds.some(
        (entry) => entry.issueId === currentIssue.id && entry.ruleId === ruleId,
      )
    );
  }

  function setBusy(issueId: number, ruleId: number, busy: boolean) {
    busyRuleIds = busy
      ? busyRuleIds.some(
          (entry) => entry.issueId === issueId && entry.ruleId === ruleId,
        )
        ? busyRuleIds
        : [...busyRuleIds, { issueId, ruleId }]
      : busyRuleIds.filter(
          (entry) => entry.issueId !== issueId || entry.ruleId !== ruleId,
        );
  }

  async function toggleRule(rule: AttachmentRule) {
    if (!issue) return;
    const issueIdAtStart = issue.id;
    const generationAtStart = requestGeneration;
    setBusy(issueIdAtStart, rule.id, true);
    actionError = "";
    try {
      const updated = await setAttachmentRuleEnabled(
        issueIdAtStart,
        rule.id,
        !rule.enabled,
      );
      if (isCurrentIssue(issueIdAtStart, generationAtStart) && issue)
        updateIssueRules(
          replaceAttachmentRule(issue.attachment_rules, updated),
        );
    } catch (error) {
      const message = await issueErrorMessage(error);
      if (isCurrentIssue(issueIdAtStart, generationAtStart))
        actionError = message;
    } finally {
      setBusy(issueIdAtStart, rule.id, false);
    }
  }

  function openDeleteConfirmation(rule: AttachmentRule) {
    pendingDelete = rule;
    deleteDialog?.showModal();
  }

  async function confirmDelete() {
    if (!issue || !pendingDelete) return;
    const rule = pendingDelete;
    const issueIdAtStart = issue.id;
    const generationAtStart = requestGeneration;
    setBusy(issueIdAtStart, rule.id, true);
    actionError = "";
    try {
      await deleteAttachmentRule(issueIdAtStart, rule.id);
      if (isCurrentIssue(issueIdAtStart, generationAtStart) && issue) {
        updateIssueRules(removeAttachmentRule(issue.attachment_rules, rule.id));
        pendingDelete = null;
        deleteDialog?.close();
      }
    } catch (error) {
      const message = await issueErrorMessage(error);
      if (isCurrentIssue(issueIdAtStart, generationAtStart))
        actionError = message;
    } finally {
      setBusy(issueIdAtStart, rule.id, false);
    }
  }
</script>

<svelte:head>
  <title
    >{issue
      ? `${issue.source} ${issue.project}/${issue.key} — Test Observer`
      : "Issue — Test Observer"}</title
  >
</svelte:head>

<main class="issue-detail-page" aria-live="polite">
  {#if loadState === "loading"}
    <p class="state-message" role="status">Loading issue…</p>
  {:else if loadState === "invalid"}
    <section class="state-message" role="alert">
      <h1>Invalid issue ID</h1>
      <p>Issue IDs must be positive whole numbers.</p>
      <a href={resolve("issues")}>Back to issues</a>
    </section>
  {:else if loadState === "not-found"}
    <section class="state-message" role="alert">
      <h1>Issue not found</h1>
      <p>{loadError}</p>
      <a href={resolve("issues")}>Back to issues</a>
    </section>
  {:else if loadState === "error"}
    <section class="state-message" role="alert">
      <h1>Unable to load issue</h1>
      <p>{loadError}</p>
      <a href={resolve("issues")}>Back to issues</a>
    </section>
  {:else if issue}
    <a class="back-link" href={resolve("issues")}>← Issues</a>
    <header class="issue-header">
      <div class="issue-identity">
        <span class="source">{issue.source}</span>
        <span class="project">{issue.project}</span>
        <a
          class="external-issue"
          href={issue.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Open external issue ${issue.key} in a new tab`}
        >
          {issue.key}<span aria-hidden="true"> ↗</span>
        </a>
        <span class={`status status-${issue.status}`}>{issue.status}</span>
      </div>
      <h1>{issue.title}</h1>
    </header>

    {#key issue.id}
      <IssueAutoRerun issueId={issue.id} enabled={issue.auto_rerun_enabled} />
    {/key}

    <section class="attachment-rules" aria-labelledby="attachment-rules-title">
      <h2 id="attachment-rules-title">Attachment Rules</h2>
      {#if issue.attachment_rules.length === 0}
        <p>No attachment rules.</p>
      {:else}
        <div class="rules-list">
          {#each issue.attachment_rules as rule (rule.id)}
            {@const criteria = attachmentRuleCriteria(rule)}
            <details class="rule">
              <summary>
                <span>Attachment Rule #{rule.id}</span>
                <span
                  class:enabled={rule.enabled}
                  class:disabled={!rule.enabled}
                  class="rule-state"
                  >{rule.enabled ? "Enabled" : "Disabled"}</span
                >
              </summary>
              <div class="rule-content">
                <div class="rule-actions">
                  <a href={viewRuleFiltersUrl(resolve(""), issue.id, rule)}
                    >View filters</a
                  >
                  <button
                    type="button"
                    disabled={isRuleBusy(rule.id)}
                    onclick={() => void toggleRule(rule)}
                  >
                    {isRuleBusy(rule.id)
                      ? "Saving…"
                      : rule.enabled
                        ? "Disable"
                        : "Enable"}
                  </button>
                  <button
                    class="danger-button"
                    type="button"
                    disabled={isRuleBusy(rule.id)}
                    onclick={() => openDeleteConfirmation(rule)}
                  >
                    Delete
                  </button>
                </div>
                {#if criteria.length}
                  <dl class="criteria-list">
                    {#each criteria as criterion (criterion.label)}
                      <div class="criterion">
                        <dt>{criterion.label}</dt>
                        <dd>
                          {#each criterion.values as value, index (`${criterion.label}-${index}`)}
                            <span class="criterion-value"
                              >{criterion.label === "Artefact Stages" &&
                              value === ""
                                ? "(none)"
                                : criterion.label === "Test Result Statuses"
                                  ? value.charAt(0) +
                                    value.slice(1).toLowerCase()
                                  : value}</span
                            >
                          {/each}
                        </dd>
                      </div>
                    {/each}
                  </dl>
                {:else}
                  <p class="empty-filters">No filters available.</p>
                {/if}
              </div>
            </details>
          {/each}
        </div>
      {/if}
      {#if actionError}
        <p class="action-error" role="alert">{actionError}</p>
      {/if}
    </section>

    {#key issue.id}
      <IssueTestResults
        issueId={issue.id}
        families={data.artefactFamilies}
        base={resolve("").replace(/\/$/, "")}
      />
    {/key}

    <dialog bind:this={deleteDialog} aria-labelledby="delete-dialog-title">
      <h2 id="delete-dialog-title">Delete attachment rule?</h2>
      <p>
        Are you sure you want to delete Attachment Rule #{pendingDelete?.id}?
      </p>
      <div class="dialog-actions">
        <button
          type="button"
          onclick={() => {
            pendingDelete = null;
            deleteDialog?.close();
          }}>Cancel</button
        >
        <button
          class="danger-button"
          type="button"
          disabled={pendingDelete !== null && isRuleBusy(pendingDelete.id)}
          onclick={() => void confirmDelete()}
        >
          {pendingDelete !== null && isRuleBusy(pendingDelete.id)
            ? "Deleting…"
            : "Delete rule"}
        </button>
      </div>
    </dialog>
  {/if}
</main>

<style>
  .issue-detail-page {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem clamp(1rem, 3vw, 2.5rem);
  }

  .state-message {
    padding: 2rem 0;
  }

  .back-link {
    display: inline-block;
    margin-bottom: 1.5rem;
  }

  .issue-header {
    margin-bottom: 2rem;
  }

  .issue-identity {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem 1.25rem;
    text-transform: capitalize;
  }

  .issue-identity .project {
    font-weight: 600;
  }

  .external-issue {
    font-weight: 600;
  }

  .status,
  .rule-state {
    border-radius: 1rem;
    padding: 0.2rem 0.65rem;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .status-open,
  .rule-state.enabled {
    color: #0e8420;
    background: #d9f2dd;
  }

  .status-closed,
  .rule-state.disabled {
    color: #5e5e5e;
    background: #eee;
  }

  .status-unknown {
    color: #8a5d00;
    background: #fff1c2;
  }

  .issue-header h1 {
    margin: 0.75rem 0 0;
  }

  .attachment-rules h2 {
    margin-bottom: 0.75rem;
  }

  .rules-list {
    display: grid;
    gap: 0.75rem;
  }

  .rule {
    border: 1px solid #d9d9d9;
    border-radius: 0.4rem;
  }

  .rule summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.9rem 1rem;
    cursor: pointer;
    font-weight: 600;
  }

  .rule-content {
    padding: 0 1rem 1rem;
  }

  .rule-actions,
  .dialog-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    margin: 0.25rem 0 1rem;
  }

  button,
  .rule-actions a {
    border: 1px solid #777;
    border-radius: 0.25rem;
    background: transparent;
    padding: 0.45rem 0.75rem;
    color: inherit;
    font: inherit;
    text-decoration: none;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.65;
    cursor: wait;
  }

  .danger-button {
    color: #c7162b;
  }

  .criteria-list {
    margin: 0;
  }

  .criterion {
    display: grid;
    grid-template-columns: minmax(10rem, 15rem) 1fr;
    border-top: 1px solid #eee;
    padding: 0.65rem 0;
    gap: 0.75rem;
  }

  .criterion dt {
    font-weight: 600;
  }

  .criterion dd {
    margin: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }

  .criterion-value {
    overflow-wrap: anywhere;
  }

  .criterion-value + .criterion-value::before {
    content: ", ";
    white-space: pre;
  }

  .empty-filters,
  .action-error {
    margin-bottom: 0;
  }

  .action-error {
    color: #c7162b;
  }

  dialog {
    max-width: min(32rem, calc(100vw - 2rem));
    border: 1px solid #999;
    border-radius: 0.4rem;
    padding: 1.5rem;
  }

  dialog::backdrop {
    background: rgb(0 0 0 / 45%);
  }

  @media (max-width: 600px) {
    .criterion {
      grid-template-columns: 1fr;
      gap: 0.25rem;
    }
  }
</style>
