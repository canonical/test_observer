<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, tick } from "svelte";
  import { Button, Link, Modal } from "@canonical/svelte-ds-app-launchpad";
  import { silentApi } from "$lib/api/client";
  import { userStore } from "$lib/stores/user.svelte";
  import type { AttachmentRuleFilters, Capability } from "$lib/testResultsBulk";
  import {
    refreshBulkPermissions,
    type BulkPermissions,
  } from "$lib/testResultsBulkPermissions";
  import {
    ambiguousMutationError,
    issueRequestError,
    pickedIssue,
    type IssueChoice,
    type PickedIssue,
  } from "$lib/testResultsIssues";
  import {
    confirmRuleIssue,
    createdRule,
    ruleCriteria,
  } from "$lib/testResultsAttachmentRules";
  import BulkIssuePicker from "./BulkIssuePicker.svelte";

  let {
    scope,
    reviewKey,
    origin,
    base,
    loginUrl,
    blocked,
    beforeOpen,
    onbusy,
    onreview,
    oncomplete,
  }: {
    scope: (ownSubmission?: boolean) => Capability<AttachmentRuleFilters>;
    reviewKey: string;
    origin: string;
    base: string;
    loginUrl: string;
    blocked: boolean;
    beforeOpen: () => void;
    onbusy: (busy: boolean) => void;
    onreview: (open: boolean) => void;
    oncomplete: (message: string) => void;
  } = $props();
  const id = $props.id();
  let trigger = $state<HTMLButtonElement>();
  let live = true;
  let open = $state(false);
  let busy = $state(false);
  let checking = $state(false);
  let invalidated = $state(false);
  let terminal = $state(false);
  let message = $state("");
  let target = $state.raw<AttachmentRuleFilters | null>(null);
  let openedKey = $state("");
  let reviewedUser = $state<number | null | undefined>(undefined);
  let authorizationVersion = $state(userStore.authorizationVersion);
  let permissions = $state.raw<BulkPermissions | null>(null);
  let authController: AbortController | undefined;
  let choice = $state.raw<IssueChoice | null>(null);
  // Keep a known partial issue even across a renewed query review. It is never
  // silently replaced with another creation PUT after a rejected rule POST.
  let retainedIssue = $state.raw<PickedIssue | null>(null);
  const capability = $derived(scope());
  const reason = $derived(
    blocked
      ? "Close the other action review first."
      : !capability.ok
        ? capability.reason
        : "",
  );
  function gate(
    action: "attachmentRule" | "lookupIssue" | "createIssue",
  ): Capability<true> {
    return checking
      ? { ok: false, reason: "Checking permissions…" }
      : (permissions?.check(action) ?? {
          ok: false,
          reason: "Refresh permissions before submitting.",
        });
  }
  const rulePermission = $derived(gate("attachmentRule"));
  const lookupPermission = $derived(gate("lookupIssue"));
  const creationPermission = $derived(gate("createIssue"));
  const canSubmit = $derived(
    open &&
      !busy &&
      !checking &&
      !invalidated &&
      !terminal &&
      rulePermission.ok &&
      lookupPermission.ok &&
      Boolean(retainedIssue || choice) &&
      (retainedIssue || choice?.kind !== "external" || creationPermission.ok),
  );

  function currentScope() {
    if (!live || !open || invalidated) return false;
    const fresh = scope(true);
    if (
      openedKey !== reviewKey ||
      !fresh.ok ||
      JSON.stringify(fresh.value) !== JSON.stringify(target) ||
      (reviewedUser !== undefined &&
        reviewedUser !== (userStore.current?.id ?? null)) ||
      authorizationVersion !== userStore.authorizationVersion
    ) {
      invalidated = true;
      return false;
    }
    return true;
  }
  // Observe readiness as well as identity: changed-then-restored drafts/loading,
  // queries and sessions permanently revoke this review, even during a PUT/POST.
  $effect(() => {
    void reviewKey;
    void scope(true);
    void userStore.current?.id;
    void userStore.authorizationVersion;
    if (open) currentScope();
  });

  async function refreshPermissions() {
    if (!currentScope()) return;
    authController?.abort();
    const controller = new AbortController();
    authController = controller;
    checking = true;
    permissions = null;
    const pending = refreshBulkPermissions(fetch, controller.signal);
    // Only our own synchronous refresh is expected. ANY subsequent refresh,
    // including one leaving the cached profile unchanged, durably revokes us.
    authorizationVersion = userStore.authorizationVersion;
    const result = await pending;
    if (!live || controller.signal.aborted) return;
    checking = false;
    if (!currentScope()) return;
    reviewedUser = userStore.current?.id ?? null;
    permissions = result;
  }
  async function start() {
    if (open || busy || blocked) return;
    const fresh = scope();
    if (!fresh.ok) return;
    beforeOpen();
    trigger?.focus({ preventScroll: true });
    target = fresh.value;
    openedKey = reviewKey;
    reviewedUser = userStore.current?.id;
    authorizationVersion = userStore.authorizationVersion;
    invalidated = false;
    terminal = false;
    message = "";
    choice = null;
    open = true;
    onreview(true);
    await refreshPermissions();
  }
  async function restoreFocus() {
    await tick();
    if (!live || open) return;
    if (trigger?.isConnected && !trigger.disabled)
      trigger.focus({ preventScroll: true });
    else
      trigger?.closest<HTMLElement>(".results")?.focus({ preventScroll: true });
  }
  function close() {
    if (busy) return;
    open = false;
    checking = false;
    authController?.abort();
    onreview(false);
    void restoreFocus();
  }
  function pickerAllowed(): Capability<true> {
    return currentScope() && !busy && !terminal
      ? gate("lookupIssue")
      : { ok: false, reason: "This review is no longer available." };
  }
  async function submit() {
    if (!canSubmit || busy || !target || !currentScope()) return;
    const filters = target;
    const chosen = retainedIssue
      ? { kind: "existing" as const, issue: retainedIssue }
      : choice;
    busy = true;
    onbusy(true);
    message = "";
    let sent = false;
    let postAccepted = false;
    try {
      await refreshPermissions();
      if (!currentScope()) return;
      for (const permission of [
        gate("attachmentRule"),
        gate("lookupIssue"),
        ...(chosen?.kind === "external" ? [gate("createIssue")] : []),
      ]) {
        if (!permission.ok) {
          message = permission.reason;
          return;
        }
      }
      let issue = chosen?.kind === "existing" ? chosen.issue : null;
      if (!issue && chosen?.kind === "external") {
        sent = true;
        issue = pickedIssue(
          await silentApi("issues", {
            method: "PUT",
            body: JSON.stringify({ url: chosen.url }),
          }),
        );
        if (!live) return;
        retainedIssue = issue;
        if (!currentScope()) return;
        await refreshPermissions();
        if (!currentScope()) return;
      }
      for (const permission of [gate("attachmentRule"), gate("lookupIssue")]) {
        if (!permission.ok) {
          message = permission.reason;
          return;
        }
      }
      if (!issue) throw new Error("Choose one issue first.");
      // No result IDs, attach endpoint, count request or result refresh belongs
      // to this workflow. The predicate is independent of row selection.
      sent = true;
      const body: unknown = await silentApi(
        `issues/${issue.id}/attachment-rules`,
        { method: "POST", body: JSON.stringify({ enabled: true, ...filters }) },
      );
      postAccepted = true;
      if (!live || !currentScope()) return;
      const ruleId = createdRule(body);
      // POST's actual response has no issue_id; confirm issue membership using
      // its existing read API rather than inventing one or claiming success.
      const issueBody: unknown = await silentApi(`issues/${issue.id}`);
      if (!live || !currentScope()) return;
      confirmRuleIssue(issueBody, issue.id, ruleId);
      oncomplete(
        `Enabled attachment rule #${ruleId} created for issue #${issue.id}. This persistent rule uses the applied search for ongoing matching. No one-off attachment was requested; current results and selection were not refreshed or changed by this action.`,
      );
      retainedIssue = null;
      busy = false;
      onbusy(false);
      close();
    } catch (cause) {
      const detail = await issueRequestError(cause);
      if (!live) return;
      currentScope();
      // A failed verification read is also unknown after a successful POST:
      // even an authoritative read denial must not enable duplicate rule POSTs.
      if ((sent && ambiguousMutationError(cause)) || postAccepted) {
        terminal = true;
        message = `Outcome unknown or unconfirmed. The server may have created the rule or issue. No automatic retry or same-review resubmission will be made. Inspect the issue, then close and start a new review if needed. ${detail}`;
      } else message = detail;
      // Definite PUT/POST rejections require fresh authorization for an explicit
      // retry. Keep a known issue ID; unknown outcomes remain terminal.
      if (!postAccepted && sent && !ambiguousMutationError(cause)) {
        permissions = null;
      }
    } finally {
      busy = false;
      checking = false;
      if (live) onbusy(false);
    }
  }
  onDestroy(() => {
    live = false;
    authController?.abort();
    onbusy(false);
    onreview(false);
  });
</script>

<div class="query-rule-action">
  <Button
    bind:ref={trigger}
    type="button"
    density="dense"
    disabled={Boolean(reason) || open || busy}
    aria-describedby={`${id}-reason`}
    onpointerdown={beforeOpen}
    onkeydown={(event) => {
      if (["Enter", " "].includes(event.key)) beforeOpen();
    }}
    onclick={start}>Create Attachment Rule…</Button
  >
  {#if reason}<p id={`${id}-reason`} role="status">{reason}</p>{:else}<span
      id={`${id}-reason`}
      class="hint"
      >Persistent rule from the applied search, not selected rows.</span
    >{/if}
</div>

{#if open}
  <Modal
    class="attachment-rule-review"
    bind:open
    closeOnOutsideClick={false}
    aria-labelledby={`${id}-title`}
    oncancel={(event) => {
      if (busy) event.preventDefault();
    }}
    onkeydown={(event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        close();
      }
    }}
    onclose={(event) => {
      if (!event.currentTarget.open) close();
    }}
  >
    <Modal.Content class="attachment-rule-content">
      <Modal.Content.Header
        ><h2 id={`${id}-title`}>Create Attachment Rule</h2>
        <Button
          type="button"
          density="dense"
          aria-label="Close attachment rule review"
          disabled={busy}
          onclick={close}>Close</Button
        ></Modal.Content.Header
      >
      <Modal.Content.Body class="attachment-rule-body">
        <p>
          <strong>Persistent ENABLED rule based on the APPLIED SEARCH.</strong> This
          is not a one-off attachment to current results. It remains enabled for ongoing
          server-side matching, including newly submitted results and end-test processing.
        </p>
        <p>
          <strong
            >Row selection, all-matches exclusions and local grid filtering are
            ignored.</strong
          > They do not narrow this rule. Zero current matches does not limit its
          future effect.
        </p>
        <h3>Frozen applied search criteria</h3>
        <p>
          Read only. Close this review and adjust the search chips to change the
          criteria.
        </p>
        {#if target}<dl>
            {#each ruleCriteria(target) as criterion (criterion.label)}<dt>
                {criterion.label}
              </dt>
              <dd>{criterion.value}</dd>{/each}
          </dl>{/if}
        {#if !rulePermission.ok}<p role={checking ? "status" : "alert"}>
            {rulePermission.reason}
          </p>{/if}
        {#if !checking && !lookupPermission.ok}<p role="alert">
            Issue lookup: {lookupPermission.reason}
          </p>{/if}
        {#if !checking && !userStore.current}<Link href={loginUrl}>Log in</Link
          >{/if}
        {#if !busy && !terminal && !invalidated}<Button
            type="button"
            density="dense"
            disabled={checking}
            onclick={refreshPermissions}>Refresh permissions</Button
          >{/if}
        {#if retainedIssue}<p role="status">
            <strong>Issue #{retainedIssue.id} was created or found.</strong>
            {retainedIssue.label} It exists independently of the rule; these operations
            are not atomic. An explicit retry uses this same issue ID, not another
            creation PUT.
          </p>{/if}
        {#if choice || retainedIssue}
          <p>
            <strong>Issue:</strong>
            {retainedIssue?.label ??
              (choice?.kind === "existing" ? choice.issue.label : choice?.url)}
          </p>
          {#if choice?.kind === "external" && !retainedIssue}<p>
              Submitting first creates or finds the issue, then creates its
              enabled rule. These are separate operations.
            </p>
            {#if !creationPermission.ok}<p role="alert">
                {creationPermission.reason}
              </p>{/if}{/if}
          {#if !retainedIssue && !busy && !terminal && !invalidated}<Button
              type="button"
              density="dense"
              onclick={() => {
                choice = null;
                message = "";
              }}>Choose another issue</Button
            >{/if}
        {:else if !busy && !checking && !terminal && !invalidated && lookupPermission.ok}
          <BulkIssuePicker
            operation="attach"
            {origin}
            {base}
            allowed={pickerAllowed}
            onchoose={async (value) => {
              if (!currentScope()) return;
              choice = value;
              message = "";
              await tick();
              if (currentScope())
                document
                  .getElementById(`${id}-submit`)
                  ?.focus({ preventScroll: true });
            }}
          />
        {/if}
        {#if invalidated}<p role="alert">
            The applied query, readiness or session changed. Close this review
            and open Create Attachment Rule again. Restoring the old values does
            not renew this review. Nothing further will be submitted; any
            in-flight request may already have completed.
          </p>{/if}
        {#if message}<p role="alert">{message}</p>{/if}
        {#if busy}<p role="status">
            Submitting… Closing and navigation are disabled while the request is
            in flight.
          </p>{/if}
      </Modal.Content.Body>
      <Modal.Content.Footer
        ><Button
          id={`${id}-submit`}
          type="button"
          severity="brand"
          disabled={!canSubmit}
          onclick={submit}
          >{busy ? "Submitting…" : "Create enabled rule"}</Button
        ><Button type="button" disabled={busy} onclick={close}>Cancel</Button
        ></Modal.Content.Footer
      >
    </Modal.Content>
  </Modal>
{/if}

<style>
  .query-rule-action {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.25rem 0.75rem;
    min-width: 0;
  }
  .query-rule-action p,
  .hint {
    margin: 0;
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }
  :global(html:has(dialog.attachment-rule-review[open])) {
    overflow: hidden;
  }
  :global(dialog.ds.modal.attachment-rule-review) {
    width: min(48rem, calc(100vw - 2rem));
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }
  :global(.attachment-rule-content) {
    display: flex;
    flex-direction: column;
    max-height: calc(100dvh - 2rem);
    min-height: 0;
    box-sizing: border-box;
  }
  :global(.attachment-rule-body) {
    min-height: 0;
    overflow: auto;
    overflow-wrap: anywhere;
    overscroll-behavior: contain;
  }
  :global(.attachment-rule-content .dialog-content-header),
  :global(.attachment-rule-content .dialog-content-footer) {
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  :global(.attachment-rule-review .text-input) {
    width: 100%;
    box-sizing: border-box;
  }
  h2 {
    font-size: 1.25rem;
    margin: 0;
  }
  h3 {
    font-size: 1rem;
  }
  dt {
    font-weight: 550;
  }
  dd {
    margin: 0 0 0.5rem;
  }
</style>
