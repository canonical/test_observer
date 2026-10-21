<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, tick } from "svelte";
  import {
    Button,
    Link,
    Modal,
    Popover,
  } from "@canonical/svelte-ds-app-launchpad";
  import { ChevronDownIcon } from "@canonical/svelte-icons";
  import { silentApi } from "$lib/api/client";
  import {
    issueAttachmentPayload,
    executionIds,
    type BulkTarget,
    type Capability,
  } from "$lib/testResultsBulk";
  import {
    refreshBulkPermissions,
    type BulkPermissions,
  } from "$lib/testResultsBulkPermissions";
  import { userStore } from "$lib/stores/user.svelte";
  import {
    ambiguousMutationError,
    attachmentIsBulk,
    bulkTargetCount,
    bulkTargetIdentity,
    issueRequestError,
    pickedIssue,
    type IssueChoice,
    type IssueOperation,
    type IssueReviewStatus,
    type PickedIssue,
  } from "$lib/testResultsIssues";
  import BulkIssuePicker from "./BulkIssuePicker.svelte";
  import BulkRerunReview from "./BulkRerunReview.svelte";
  import { rerunIsBulk, type RerunOperation } from "$lib/testResultsReruns";

  let {
    scope,
    reviewKey,
    origin,
    base,
    loginUrl,
    beforeOpen,
    onbusy,
    onreview,
    oncomplete,
    onrefresh,
    blocked = false,
  }: {
    scope: (ownSubmission?: boolean) => Capability<BulkTarget>;
    reviewKey: string;
    origin: string;
    base: string;
    loginUrl: string;
    beforeOpen: () => void;
    onbusy: (busy: boolean) => void;
    onreview: (open: boolean) => void;
    oncomplete: (key: string, message: string) => Promise<void>;
    onrefresh: () => Promise<void>;
    blocked?: boolean;
  } = $props();
  const id = $props.id();
  let menu: ReturnType<typeof Popover>;
  let menuButton = $state<HTMLButtonElement>();
  let permissions = $state.raw<BulkPermissions | null>(null);
  let checking = $state(false);
  let authController: AbortController | undefined;
  let live = true;
  let open = $state(false);
  let rerunReview: ReturnType<typeof BulkRerunReview>;
  let rerunBusy = $state(false);
  let rerunOpen = $state(false);
  let target = $state.raw<BulkTarget | null>(null);
  let operation = $state<IssueOperation>("attach");
  let status = $state<IssueReviewStatus>("review");
  let choice = $state.raw<IssueChoice | null>(null);
  let retainedIssue = $state.raw<PickedIssue | null>(null);
  let acknowledged = $state(false);
  let message = $state("");
  let openedKey = $state("");
  // Revocation belongs to this review, not just the current scope/session value.
  // Once an observed change occurs, restoring the old values cannot authorize
  // a later continuation of a slow request. Reset only on a new user review.
  let reviewInvalidated = $state(false);
  const invalidReviewMessage =
    "The selection, applied query or session changed. Close this review and open Bulk actions again to review the current scope. Nothing further will be submitted from this review.";
  let reviewedUser: number | null = null;
  let submitted = false;
  const busy = $derived(status === "submitting");
  const invalid = $derived(
    reviewInvalidated || status === "invalidated" || openedKey !== reviewKey,
  );
  const count = $derived(target ? bulkTargetCount(target) : 0);
  const capability = $derived(scope());

  function attachmentPermission(
    frozen = open ? target : capability.ok ? capability.value : null,
  ): Capability<true> {
    if (checking) return { ok: false, reason: "Checking permissions…" };
    return (
      permissions?.check(
        "issueAttachment",
        frozen
          ? attachmentIsBulk(frozen)
          : capability.ok
            ? attachmentIsBulk(capability.value)
            : true,
      ) ?? {
        ok: false,
        reason: "Refresh permissions before using this action.",
      }
    );
  }
  function lookupPermission(): Capability<true> {
    if (checking) return { ok: false, reason: "Checking permissions…" };
    return (
      permissions?.check("lookupIssue") ?? {
        ok: false,
        reason: "Refresh permissions to look up issues.",
      }
    );
  }
  const permission = $derived(attachmentPermission());
  const lookup = $derived(lookupPermission());
  const creation = $derived(
    permissions?.check("createIssue") ?? {
      ok: false as const,
      reason: "Refresh permissions to create an issue.",
    },
  );
  const menuReason = $derived(
    !capability.ok
      ? capability.reason
      : !permission.ok
        ? permission.reason
        : "",
  );
  const rerunReason = $derived.by(() => {
    if (!capability.ok) return capability.reason;
    if (checking) return "Checking permissions…";
    if (capability.value.kind === "explicit") {
      const ids = executionIds(capability.value);
      if (!ids.ok) return ids.reason;
    }
    const gate = permissions?.check("rerun", rerunIsBulk(capability.value));
    return gate?.ok
      ? ""
      : gate
        ? gate.reason
        : "Refresh permissions before using this action.";
  });
  const canSubmit = $derived(
    open &&
      !busy &&
      !checking &&
      !invalid &&
      status !== "unknown" &&
      permission.ok &&
      lookup.ok &&
      Boolean(choice || retainedIssue) &&
      (retainedIssue || choice?.kind !== "external" || creation.ok) &&
      (count <= 50 || acknowledged),
  );

  async function refreshPermissions() {
    authController?.abort();
    const controller = new AbortController();
    authController = controller;
    permissions = null;
    checking = true;
    const result = await refreshBulkPermissions(fetch, controller.signal);
    if (!live || controller.signal.aborted) return;
    permissions = result;
    checking = false;
    if (open && status === "checking")
      status = retainedIssue ? "partial" : "review";
    await tick();
    const panel = document.getElementById(`${id}-menu`);
    if (
      !open &&
      panel?.matches(":popover-open") &&
      (document.activeElement === menuButton ||
        panel.contains(document.activeElement))
    )
      panel.querySelector<HTMLButtonElement>("button:not(:disabled)")?.focus();
  }

  $effect(() => {
    const currentUser = userStore.current?.id ?? null;
    if (
      open &&
      (openedKey !== reviewKey ||
        (reviewedUser !== null && currentUser !== reviewedUser))
    ) {
      reviewInvalidated = true;
    }
    // Keep busy/close/navigation protection until the in-flight request settles,
    // but remember revocation immediately, including logout then same-user login.
    if (open && reviewInvalidated && !busy && status !== "unknown") {
      status = "invalidated";
      authController?.abort();
    }
  });
  $effect(() => {
    onbusy(busy || rerunBusy);
  });
  $effect(() => {
    onreview(open || rerunOpen);
  });
  onDestroy(() => {
    live = false;
    authController?.abort();
    onbusy(false);
    onreview(false);
  });

  function currentScope() {
    if (!open || !live || reviewInvalidated) return false;
    const fresh = scope(true);
    const current = Boolean(
      target &&
      openedKey === reviewKey &&
      fresh.ok &&
      bulkTargetIdentity(fresh.value) === bulkTargetIdentity(target) &&
      (reviewedUser === null || reviewedUser === userStore.current?.id),
    );
    if (!current) reviewInvalidated = true;
    return current;
  }
  async function start(action: IssueOperation) {
    if (blocked || open || rerunOpen || busy || rerunBusy) return;
    const fresh = scope();
    if (!fresh.ok || !attachmentPermission(fresh.value).ok) return;
    beforeOpen();
    menu.hidePopover();
    menuButton?.focus({ preventScroll: true });
    operation = action;
    target = fresh.value;
    openedKey = reviewKey;
    reviewedUser = userStore.current?.id ?? null;
    reviewInvalidated = false;
    choice = null;
    retainedIssue = null;
    acknowledged = false;
    submitted = false;
    message = "";
    status = "checking";
    open = true;
    onreview(true);
    await refreshPermissions();
  }
  function startRerun(action: RerunOperation) {
    if (blocked || open || rerunOpen || busy || rerunBusy || rerunReason)
      return;
    beforeOpen();
    menu.hidePopover();
    menuButton?.focus({ preventScroll: true });
    void rerunReview.start(action);
  }
  function close() {
    if (busy) return;
    open = false;
    authController?.abort();
    void restoreTriggerFocus();
  }
  async function restoreTriggerFocus() {
    await tick();
    if (live && !open && !rerunOpen && menuButton?.isConnected)
      menuButton.focus({ preventScroll: true });
  }
  async function submit() {
    if (!canSubmit || submitted || !target) return;
    submitted = true;
    status = "submitting";
    message = "";
    // Mark busy synchronously, before any await or second click/navigation.
    onbusy(true);
    let mutationStarted = false;
    try {
      await refreshPermissions();
      if (!currentScope()) {
        status = "invalidated";
        message =
          "Scope or session changed. Close and review the current selection again before submitting.";
        return;
      }
      for (const gate of [
        attachmentPermission(),
        lookupPermission(),
        ...(!retainedIssue && choice?.kind === "external"
          ? [
              permissions?.check("createIssue") ?? {
                ok: false as const,
                reason: "Refresh permissions to create an issue.",
              },
            ]
          : []),
      ]) {
        if (!gate.ok) {
          status = retainedIssue ? "partial" : "error";
          message = gate.reason;
          return;
        }
      }
      let issue =
        retainedIssue ?? (choice?.kind === "existing" ? choice.issue : null);
      if (!issue && choice?.kind === "external") {
        mutationStarted = true;
        issue = pickedIssue(
          await silentApi("issues", {
            method: "PUT",
            body: JSON.stringify({ url: choice.url }),
          }),
        );
        if (!live) return;
        retainedIssue = issue;
        if (!currentScope()) {
          status = "invalidated";
          return;
        }
        // PUT and attachment are separate requests. A slow creation response
        // is not fresh permission evidence for the subsequent POST.
        await refreshPermissions();
      }
      // Creation may have taken time. Never attach an old scope after navigation,
      // logout, an unrelated /me refresh or selection change during that request.
      if (!currentScope()) {
        status = "invalidated";
        message =
          "Scope or authorization changed before attachment. Close and review again. Any issue already created is retained below; attachment was not sent.";
        return;
      }
      for (const gate of [attachmentPermission(), lookupPermission()]) {
        if (!gate.ok) {
          status = retainedIssue ? "partial" : "error";
          message = gate.reason;
          return;
        }
      }
      if (!issue) throw new Error("Choose one issue first.");
      mutationStarted = true;
      await silentApi(`issues/${issue.id}/${operation}`, {
        method: "POST",
        body: JSON.stringify(issueAttachmentPayload(target)),
      });
      if (!live) return;
      if (!currentScope()) {
        status = "invalidated";
        message =
          "The submitted request completed, but its review was revoked while it was in flight. Refresh results to inspect the outcome; the current selection has not been cleared.";
        return;
      }
      const key = openedKey;
      status = "review";
      open = false;
      onbusy(rerunBusy);
      await oncomplete(
        key,
        `${operation === "attach" ? "Attach" : "Detach"} request completed for issue #${issue.id}. Refreshing current results. The API does not report a changed count; already-${operation === "attach" ? "attached" : "detached"} results may be unchanged.`,
      );
      if (menuButton?.isConnected) menuButton.focus({ preventScroll: true });
    } catch (cause) {
      const detail = await issueRequestError(cause);
      if (!live) return;
      if (mutationStarted && ambiguousMutationError(cause)) {
        status = "unknown";
        message = `Outcome unknown. The server may have completed the request even though its response failed. No automatic retry will be made. Refresh results and inspect the issue before starting a new review. ${detail}`;
      } else if (reviewInvalidated || !currentScope()) {
        status = "invalidated";
        message = detail;
      } else {
        status = retainedIssue ? "partial" : "error";
        message = `${retainedIssue ? "The issue was created or found, but attachment did not complete. Retrying explicitly uses this same issue ID, never creates it again. " : ""}${detail}`;
      }
    } finally {
      submitted = false;
      if (live && status === "submitting")
        status = retainedIssue ? "partial" : "error";
      if (live) onbusy(rerunBusy);
    }
  }

  async function menuToggle(event: ToggleEvent) {
    if (event.newState !== "open") return;
    await tick();
    const panel = document.getElementById(`${id}-menu`);
    if (!panel?.matches(":popover-open")) return;
    (
      panel.querySelector<HTMLButtonElement>("button:not(:disabled)") ?? panel
    ).focus();
  }
  function menuKeys(event: KeyboardEvent) {
    const root = document.getElementById(`${id}-menu`);
    const items = Array.from(
      root?.querySelectorAll<HTMLButtonElement>(
        "[role=menuitem]:not(:disabled)",
      ) ?? [],
    );
    if (event.key === "Escape" || event.key === "Tab") {
      menu.hidePopover();
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        menuButton?.focus();
      }
      return;
    }
    if (
      !["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key) ||
      !items.length
    )
      return;
    event.preventDefault();
    const index = items.indexOf(document.activeElement as HTMLButtonElement);
    items[
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? items.length - 1
          : (index + (event.key === "ArrowDown" ? 1 : items.length - 1)) %
            items.length
    ]?.focus();
  }
</script>

<Popover
  bind:this={menu}
  id={`${id}-menu`}
  class="bulk-actions-menu"
  role="menu"
  tabindex={-1}
  aria-label="Bulk actions"
  aria-describedby={`${id}-menu-reason`}
  positionTryFallbacks="flip-block"
  onbeforetoggle={(event) => {
    if (event.newState === "open") {
      beforeOpen();
      void refreshPermissions();
    }
  }}
  ontoggle={menuToggle}
  onkeydown={menuKeys}
>
  {#snippet trigger(triggerProps, expanded)}
    <Button
      {...triggerProps}
      bind:ref={menuButton}
      type="button"
      density="dense"
      disabled={blocked || busy || rerunBusy || open || rerunOpen}
      aria-haspopup="menu"
      aria-expanded={expanded}
      onpointerdown={beforeOpen}
      onkeydown={(event) => {
        if (["Enter", " ", "ArrowDown", "ArrowUp"].includes(event.key))
          beforeOpen();
        if (["ArrowDown", "ArrowUp"].includes(event.key)) {
          event.preventDefault();
          menu.showPopover();
        }
      }}>Bulk actions{#snippet iconRight()}<ChevronDownIcon />{/snippet}</Button
    >
  {/snippet}
  <Button
    type="button"
    role="menuitem"
    density="dense"
    disabled={Boolean(menuReason)}
    aria-describedby={`${id}-menu-reason`}
    onclick={() => start("attach")}>Attach Issue…</Button
  >
  <Button
    type="button"
    role="menuitem"
    density="dense"
    disabled={Boolean(menuReason)}
    aria-describedby={`${id}-menu-reason`}
    onclick={() => start("detach")}>Detach Issue…</Button
  >
  <p id={`${id}-menu-reason`} role="status">
    {menuReason || "Review the selected scope and one issue before submitting."}
  </p>
  <hr />
  <Button
    type="button"
    role="menuitem"
    density="dense"
    disabled={Boolean(rerunReason)}
    aria-describedby={`${id}-rerun-reason`}
    onclick={() => startRerun("create")}>Create Rerun Requests…</Button
  >
  <Button
    type="button"
    role="menuitem"
    density="dense"
    disabled={Boolean(rerunReason)}
    aria-describedby={`${id}-rerun-reason`}
    onclick={() => startRerun("delete")}>Delete Rerun Requests…</Button
  >
  <p id={`${id}-rerun-reason`} role="status">
    {rerunReason ||
      "Review query eligibility or explicitly opt into exact execution groups."}
  </p>
</Popover>
{#if !capability.ok}<p class="bulk-disabled" role="status">
    {capability.reason}
  </p>{/if}

<BulkRerunReview
  bind:this={rerunReview}
  {scope}
  {reviewKey}
  {loginUrl}
  {oncomplete}
  {onrefresh}
  onbusy={(value) => {
    rerunBusy = value;
    onbusy(busy || value);
  }}
  onreview={(value) => {
    rerunOpen = value;
    onreview(open || value);
  }}
  onclose={restoreTriggerFocus}
/>

<Modal
  class="bulk-issue-review"
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
  <Modal.Content class="bulk-issue-content">
    <Modal.Content.Header
      ><h2 id={`${id}-title`}>
        {operation === "attach" ? "Attach Issue" : "Detach Issue"}
      </h2>
      <Button
        type="button"
        density="dense"
        aria-label="Close issue review"
        disabled={busy}
        onclick={close}>Close</Button
      ></Modal.Content.Header
    >
    <Modal.Content.Body class="bulk-issue-body">
      {#if target}
        <p>
          <strong>{count} test results</strong>
          {target.kind === "query"
            ? "across all matches of the applied query"
            : "selected explicitly by result ID, including other pages"}.
        </p>
        {#if target.kind === "explicit"}<p class="scope-ids">
            Result IDs: {target.resultIds.join(", ")}
          </p>{:else}<h3>Applied query conditions</h3>
          <dl>
            {#each Object.entries(target.filters) as [name, value] (name)}<dt>
                {name}
              </dt>
              <dd>{JSON.stringify(value)}</dd>{/each}
          </dl>{/if}
        <p>
          This review excludes local grid filters, sorting and pagination. The
          count is a frozen preview, not a server transaction or changed count.
          Server data can change before submission{target.kind === "query"
            ? "; the query is evaluated by the server when submitted, not frozen IDs"
            : ""}.
        </p>
      {/if}
      {#if checking}<p role="status">
          Checking permissions…
        </p>{:else if !permission.ok}<p role="alert">
          {permission.reason}
        </p>{/if}
      {#if !checking && !lookup.ok}<p role="alert">
          Issue lookup: {lookup.reason}
        </p>{/if}
      {#if !userStore.current && !checking}<Link href={loginUrl}>Log in</Link
        >{/if}
      {#if !busy && !invalid && status !== "unknown"}<Button
          type="button"
          density="dense"
          disabled={checking}
          onclick={refreshPermissions}>Refresh permissions</Button
        >{/if}
      {#if retainedIssue}<p role="status">
          <strong>Issue #{retainedIssue.id} was created or found.</strong>
          {retainedIssue.label} It exists independently of attachment; this workflow
          is not atomic.
        </p>{/if}
      {#if choice || retainedIssue}
        <p class="chosen-issue">
          <strong>Issue:</strong>
          {retainedIssue?.label ??
            (choice?.kind === "existing" ? choice.issue.label : choice?.url)}
        </p>
        {#if choice?.kind === "external" && !retainedIssue}<p>
            Submitting first creates or finds the issue through the existing
            issue API, then attaches it. These are separate operations, not an
            atomic transaction.
          </p>
          {#if !creation.ok}<p role="alert">{creation.reason}</p>{/if}{/if}
        {#if !retainedIssue && !busy && !invalid && status !== "unknown"}<Button
            type="button"
            density="dense"
            onclick={() => {
              choice = null;
              message = "";
              status = "review";
            }}>Choose another issue</Button
          >{/if}
      {:else if open && !busy && !invalid && status !== "unknown" && !checking && lookup.ok}
        <BulkIssuePicker
          {operation}
          {origin}
          {base}
          allowed={lookupPermission}
          onchoose={async (value) => {
            choice = value;
            message = "";
            await tick();
            const submitButton = document.getElementById(
              `${id}-submit`,
            ) as HTMLButtonElement | null;
            if (open && live && submitButton && !submitButton.disabled)
              submitButton.focus();
          }}
        />
      {/if}
      {#if count > 50}<label class="acknowledgment"
          ><input
            type="checkbox"
            bind:checked={acknowledged}
            disabled={busy || invalid || status === "unknown"}
          />I have reviewed the scope of {count} results and want to {operation} this
          issue.</label
        >{/if}
      {#if reviewInvalidated}<p role="alert">{invalidReviewMessage}</p>{/if}
      {#if message}<p role="alert">{message}</p>{/if}
      {#if busy}<p role="status">
          Submitting… Please wait. Closing and navigation are disabled while the
          request is in flight.
        </p>{/if}
    </Modal.Content.Body>
    <Modal.Content.Footer>
      <Button
        id={`${id}-submit`}
        type="button"
        severity="brand"
        disabled={!canSubmit}
        onclick={submit}
        >{busy
          ? "Submitting…"
          : retainedIssue
            ? "Retry attachment with this issue"
            : operation === "attach"
              ? "Attach issue"
              : "Detach issue"}</Button
      >
      {#if status === "unknown" || status === "partial" || status === "invalidated"}<Button
          type="button"
          disabled={busy}
          onclick={async () => {
            close();
            await onrefresh();
          }}>Close and refresh results</Button
        >{/if}
      <Button type="button" disabled={busy} onclick={close}>Cancel</Button>
    </Modal.Content.Footer>
  </Modal.Content>
</Modal>

<style>
  /* Pragma's bare Popover is transparent; the complete menu owns its surface. */
  :global(.ds.popover.bulk-actions-menu) {
    width: min(24rem, calc(100vw - 2rem));
    max-height: calc(100dvh - 2rem);
    overflow: auto;
    padding: 0.5rem;
    box-sizing: border-box;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
    border: 1px solid var(--lp-color-border-default);
    border-radius: 0.25rem;
    box-shadow: 0 4px 16px rgb(0 0 0 / 20%);
  }
  :global(.ds.popover.bulk-actions-menu > button) {
    display: flex;
    width: 100%;
    justify-content: flex-start;
  }
  :global(.bulk-actions-menu p) {
    padding: 0.5rem;
    margin: 0;
    font-size: 0.875rem;
  }
  .bulk-disabled {
    flex-basis: 100%;
    font-size: 0.875rem;
  }
  :global(html:has(dialog.bulk-issue-review[open])) {
    overflow: hidden;
  }
  :global(dialog.ds.modal.bulk-issue-review) {
    width: min(48rem, calc(100vw - 2rem));
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }
  :global(.bulk-issue-content) {
    display: flex;
    flex-direction: column;
    max-height: calc(100dvh - 2rem);
    min-height: 0;
    box-sizing: border-box;
  }
  :global(.bulk-issue-body) {
    min-height: 0;
    overflow: auto;
    overflow-wrap: anywhere;
    overscroll-behavior: contain;
  }
  :global(.bulk-issue-content .dialog-content-header),
  :global(.bulk-issue-content .dialog-content-footer) {
    flex-shrink: 0;
    flex-wrap: wrap;
  }
  h2 {
    font-size: 1.25rem;
    margin: 0;
  }
  h3 {
    font-size: 1rem;
  }
  dl,
  .scope-ids,
  .chosen-issue {
    overflow-wrap: anywhere;
  }
  dt {
    font-weight: 550;
  }
  dd {
    margin: 0 0 0.5rem;
  }
  .acknowledgment {
    display: flex;
    align-items: start;
    gap: 0.5rem;
    margin-block: 1rem;
  }
</style>
