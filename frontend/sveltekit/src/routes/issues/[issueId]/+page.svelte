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
  import { tick } from "svelte";
  import {
    Button,
    Chip,
    Link,
    Modal,
    Spinner,
  } from "@canonical/svelte-ds-app-launchpad";
  import {
    ArrowLeftIcon,
    DeleteIcon,
    ExternalLinkIcon,
  } from "@canonical/svelte-icons";
  import { page, navigating } from "$app/state";
  import { resolve } from "$app/paths";
  import { afterNavigate, beforeNavigate } from "$app/navigation";
  import { FetchError } from "$lib/api/client";
  import {
    deleteAttachmentRule,
    getIssue,
    issueErrorMessage,
    setAttachmentRuleEnabled,
  } from "$lib/api/issues";
  import {
    attachmentRuleCriteria,
    attachmentRuleTarget,
    removeAttachmentRule,
    replaceAttachmentRule,
    viewRuleFiltersUrl,
  } from "$lib/issueDetailModel";
  import { attachmentRuleAttention } from "$lib/attachmentRuleAttention";
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
  let pendingDelete = $state<{
    rule: AttachmentRule;
    issueId: number;
    generation: number;
    trigger: HTMLButtonElement;
  } | null>(null);
  let rulesHeading = $state<HTMLHeadingElement>();
  let requestGeneration = 0;
  let rerunBusy = $state(false);
  // SPA navigation is blocked during dispatch. A hard leave can only request
  // native browser confirmation; it cannot cancel an already dispatched write.
  beforeNavigate((navigation) => {
    if (rerunBusy) navigation.cancel();
  });
  const autoRerunSession = $derived(issueAutoRerunSession());
  const url = $derived(page.shallow?.url ?? page.url);
  // Shallow history can show a different pathname without loading that issue.
  // Never attend a same-ID rule in the still-mounted, different issue.
  const targetRuleId = $derived(
    url.pathname === page.url.pathname
      ? attachmentRuleTarget(url.searchParams)
      : null,
  );
  // Preserve this event's identity through rule mutations, auto-rerun
  // confirmations and unrelated query changes. A/B/A is a fresh event.
  const ruleTarget = $derived({
    issueId,
    ruleId: targetRuleId,
    session: autoRerunSession,
  });
  let navigationMounted = $state(false);
  afterNavigate(() => (navigationMounted = true));
  const ruleAttentionReady = $derived(
    navigationMounted &&
      !navigating.to &&
      loadState === "ready" &&
      issue?.id === Number(issueId),
  );

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
    if (!issue || isRuleBusy(rule.id)) return;
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

  function openDeleteConfirmation(
    rule: AttachmentRule,
    trigger: HTMLButtonElement,
  ) {
    if (!issue || pendingDelete || isRuleBusy(rule.id)) return;
    actionError = "";
    pendingDelete = {
      rule,
      issueId: issue.id,
      generation: requestGeneration,
      trigger,
    };
  }

  async function closeDelete(owner: NonNullable<typeof pendingDelete>) {
    if (pendingDelete !== owner || isRuleBusy(owner.rule.id)) return;
    pendingDelete = null;
    await tick();
    if (pendingDelete || !isCurrentIssue(owner.issueId, owner.generation))
      return;
    // Native return handles a surviving invoker. A deleted rule needs a current,
    // persistent destination; never focus into another issue/session owner.
    if (owner.trigger.isConnected && !owner.trigger.disabled)
      owner.trigger.focus({ preventScroll: true });
    else rulesHeading?.focus({ preventScroll: true });
  }

  async function confirmDelete() {
    if (!issue || !pendingDelete) return;
    const owner = pendingDelete;
    const rule = owner.rule;
    if (isRuleBusy(rule.id)) return;
    const issueIdAtStart = issue.id;
    const generationAtStart = requestGeneration;
    setBusy(issueIdAtStart, rule.id, true);
    actionError = "";
    try {
      await deleteAttachmentRule(issueIdAtStart, rule.id);
      if (isCurrentIssue(issueIdAtStart, generationAtStart) && issue) {
        updateIssueRules(removeAttachmentRule(issue.attachment_rules, rule.id));
        setBusy(issueIdAtStart, rule.id, false);
        void closeDelete(owner);
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
    <p class="state-message loading" role="status">
      <Spinner /> Loading issue…
    </p>
  {:else if loadState === "invalid"}
    <section class="state-message" role="alert">
      <h1>Invalid issue ID</h1>
      <p>Issue IDs must be positive whole numbers.</p>
      <Link href={resolve("issues")}>Back to issues</Link>
    </section>
  {:else if loadState === "not-found"}
    <section class="state-message" role="alert">
      <h1>Issue not found</h1>
      <p>{loadError}</p>
      <Link href={resolve("issues")}>Back to issues</Link>
    </section>
  {:else if loadState === "error"}
    <section class="state-message" role="alert">
      <h1>Unable to load issue</h1>
      <p>{loadError}</p>
      <Link href={resolve("issues")}>Back to issues</Link>
    </section>
  {:else if issue}
    <Link class="back-link" href={resolve("issues")}
      ><ArrowLeftIcon /> Issues</Link
    >
    <header class="issue-header">
      <div class="issue-identity">
        <span class="source">{issue.source}</span>
        <span class="project">{issue.project}</span>
        <Link
          class="external-issue"
          href={issue.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Open external issue ${issue.key} in a new tab`}
        >
          {issue.key}<ExternalLinkIcon />
        </Link>
        <Chip
          class="status"
          readonly
          density="dense"
          value={issue.status}
          severity={issue.status === "open"
            ? "positive"
            : issue.status === "unknown"
              ? "caution"
              : "neutral"}
        />
      </div>
      <h1>{issue.title}</h1>
    </header>

    {#key issue.id}
      <IssueAutoRerun issueId={issue.id} enabled={issue.auto_rerun_enabled} />
    {/key}

    <section class="attachment-rules" aria-labelledby="attachment-rules-title">
      <h2 id="attachment-rules-title" tabindex="-1" bind:this={rulesHeading}>
        Attachment Rules
      </h2>
      {#if issue.attachment_rules.length === 0}
        <p>No attachment rules.</p>
      {:else}
        <div class="rules-list">
          {#each issue.attachment_rules as rule (rule.id)}
            {@const criteria = attachmentRuleCriteria(rule)}
            <details
              class="rule"
              class:rule-targeted={rule.id === targetRuleId}
              use:attachmentRuleAttention={{
                target: rule.id === targetRuleId ? ruleTarget : null,
                ready: ruleAttentionReady,
              }}
            >
              <summary>
                <span>Attachment Rule #{rule.id}</span>
                <Chip
                  class="rule-state"
                  readonly
                  density="dense"
                  severity={rule.enabled ? "positive" : "neutral"}
                  value={rule.enabled ? "Enabled" : "Disabled"}
                />
              </summary>
              <div class="rule-content">
                <div class="rule-actions">
                  <Link href={viewRuleFiltersUrl(resolve(""), issue.id, rule)}
                    >View filters</Link
                  >
                  <Button
                    type="button"
                    disabled={isRuleBusy(rule.id)}
                    loading={isRuleBusy(rule.id)}
                    aria-busy={isRuleBusy(rule.id)}
                    aria-label={isRuleBusy(rule.id)
                      ? "Saving…"
                      : rule.enabled
                        ? "Disable"
                        : "Enable"}
                    onclick={() => void toggleRule(rule)}
                  >
                    {isRuleBusy(rule.id)
                      ? "Saving…"
                      : rule.enabled
                        ? "Disable"
                        : "Enable"}
                  </Button>
                  <Button
                    severity="negative"
                    type="button"
                    disabled={isRuleBusy(rule.id)}
                    aria-haspopup="dialog"
                    onclick={(event) =>
                      openDeleteConfirmation(rule, event.currentTarget)}
                  >
                    {#snippet iconLeft()}<DeleteIcon />{/snippet}
                    Delete
                  </Button>
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
      {#if actionError && !pendingDelete}
        <p class="action-error" role="alert">{actionError}</p>
      {/if}
    </section>

    {#key issue.id}
      <IssueTestResults
        issueId={issue.id}
        families={data.artefactFamilies}
        base={resolve("").replace(/\/$/, "")}
        onbusy={(busy) => (rerunBusy = busy)}
      />
    {/key}

    {#if pendingDelete}
      {#key pendingDelete}
        {@const owner = pendingDelete}
        {@const deleting = isRuleBusy(owner.rule.id)}
        <Modal
          open={true}
          class="delete-rule-dialog"
          closeOnOutsideClick={!deleting}
          aria-labelledby="delete-dialog-title"
          oncancel={(event) => {
            if (deleting) event.preventDefault();
            else void closeDelete(owner);
          }}
          onclose={(event) => {
            if (!event.currentTarget.open) void closeDelete(owner);
          }}
        >
          <Modal.Content class="delete-rule-content">
            <Modal.Content.Header>
              <h2 id="delete-dialog-title">Delete attachment rule?</h2>
              <Modal.Content.Header.CloseButton
                aria-label="Close delete confirmation"
                disabled={deleting}
                onclick={() => void closeDelete(owner)}
              />
            </Modal.Content.Header>
            <Modal.Content.Body
              class="delete-rule-body"
              role="region"
              aria-label="Delete attachment rule content"
              tabindex={0}
              aria-busy={deleting}
            >
              <p>
                Are you sure you want to delete Attachment Rule #{owner.rule
                  .id}?
              </p>
              {#if actionError}<p class="action-error" role="alert">
                  {actionError}
                </p>{/if}
            </Modal.Content.Body>
            <Modal.Content.Footer>
              <Button
                type="button"
                disabled={deleting}
                onclick={() => void closeDelete(owner)}>Cancel</Button
              >
              <Button
                severity="negative"
                type="button"
                loading={deleting}
                aria-busy={deleting}
                aria-label={deleting ? "Deleting…" : "Delete rule"}
                disabled={deleting}
                onclick={() => void confirmDelete()}
                >{deleting ? "Deleting…" : "Delete rule"}</Button
              >
            </Modal.Content.Footer>
          </Modal.Content>
        </Modal>
      {/key}
    {/if}
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

  :global(.issue-detail-page .back-link) {
    display: inline-flex;
    align-items: center;
    gap: var(--lp-dimension-spacing-inline-xs);
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

  :global(.issue-detail-page .external-issue) {
    display: inline-flex;
    align-items: center;
    gap: var(--lp-dimension-spacing-inline-xs);
    font-weight: 600;
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
    border: 1px solid var(--lp-color-border-default);
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
    scroll-margin-block: var(--lp-dimension-spacing-block-l);
  }

  .rule-targeted {
    border-color: var(--lp-color-border-highlight);
    box-shadow: 0 0 0 var(--lp-dimension-stroke-thickness-default)
      var(--lp-color-border-highlight);
  }

  .rule summary:focus {
    outline: var(--lp-dimension-stroke-thickness-large) solid
      var(--lp-color-border-focus);
    outline-offset: var(--lp-dimension-spacing-inline-xxs);
  }

  .rule-content {
    padding: 0 1rem 1rem;
  }

  .rule-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    align-items: center;
    margin: 0.25rem 0 1rem;
  }

  .criteria-list {
    margin: 0;
  }

  .criterion {
    display: grid;
    grid-template-columns: minmax(10rem, 15rem) 1fr;
    border-top: 1px solid var(--lp-color-border-default);
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
    color: var(--lp-color-negative);
  }
  .loading {
    display: flex;
    align-items: center;
    gap: var(--lp-dimension-spacing-inline-s);
  }
  :global(html:has(dialog.delete-rule-dialog[open])) {
    overflow: hidden;
  }
  :global(dialog.ds.modal.delete-rule-dialog) {
    width: min(32rem, calc(100vw - 2 * var(--lp-dimension-spacing-inline-m)));
    max-width: calc(100vw - 2 * var(--lp-dimension-spacing-inline-m));
    max-height: calc(100dvh - 2 * var(--lp-dimension-spacing-block-m));
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }
  :global(.delete-rule-dialog .delete-rule-content) {
    max-height: calc(100dvh - 2 * var(--lp-dimension-spacing-block-m));
    min-height: 0;
    box-sizing: border-box;
  }
  :global(.delete-rule-dialog .dialog-content-header),
  :global(.delete-rule-dialog .dialog-content-footer) {
    flex-shrink: 0;
  }
  :global(.delete-rule-dialog .delete-rule-body) {
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    overflow-wrap: anywhere;
  }

  @media (max-width: 600px) {
    .criterion {
      grid-template-columns: 1fr;
      gap: 0.25rem;
    }
  }
</style>
