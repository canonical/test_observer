<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->
<script lang="ts">
  import { onDestroy, untrack } from "svelte";
  import { Button, Modal, TextInput } from "@canonical/svelte-ds-app-launchpad";
  import { createIssue, issueErrorMessage } from "$lib/api/issues";
  import { externalIssueUrlError } from "$lib/issuePageModel";

  let {
    getContext,
    onadded,
  }: {
    getContext: () => string;
    onadded: (id: number) => void;
  } = $props();
  const context = untrack(() => getContext());
  const isCurrent = () => context === getContext();
  const id = $props.id();
  let open = $state(false);
  let issueUrl = $state("");
  let issueUrlError = $state("");
  let createError = $state("");
  let creating = $state(false);
  let live = true;
  let revision = 0;

  onDestroy(() => {
    live = false;
    ++revision;
  });

  function show() {
    if (!live || !isCurrent() || open || creating) return;
    ++revision;
    issueUrl = "";
    issueUrlError = "";
    createError = "";
    open = true;
  }

  function close() {
    if (creating || !live || !isCurrent()) return;
    ++revision;
    open = false;
  }

  async function submit(event: SubmitEvent) {
    event.preventDefault();
    // Lock synchronously: disabled controls alone do not fence rapid Enter or
    // programmatically dispatched submit events before the next render.
    if (!live || !isCurrent() || !open || creating) return;
    const validationError = externalIssueUrlError(issueUrl);
    if (validationError) {
      issueUrlError = validationError;
      return;
    }
    const owner = revision;
    const owns = () => live && isCurrent() && open && owner === revision;
    creating = true;
    issueUrlError = "";
    createError = "";
    try {
      const issue = await createIssue(issueUrl.trim());
      if (!owns()) return;
      // The page checks its loaded main rows before starting either refresh.
      onadded(issue.id);
      creating = false;
      close();
    } catch (error) {
      if (!owns()) return;
      const message = await issueErrorMessage(error);
      if (owns()) createError = message;
    } finally {
      // A late completion must not release another dialog/session's lock.
      if (live && isCurrent() && owner === revision) creating = false;
    }
  }
</script>

<Button severity="brand" aria-haspopup="dialog" onclick={show}>Add issue</Button
>

<Modal
  class="add-issue-dialog"
  bind:open
  closeOnOutsideClick={!creating}
  aria-labelledby={`${id}-title`}
  oncancel={(event) => {
    if (creating) event.preventDefault();
  }}
  onclose={(event) => {
    // Native close is queued; an old event cannot close a newer opening.
    if (!event.currentTarget.open) close();
  }}
>
  <Modal.Content class="add-issue-content">
    <Modal.Content.Header>
      <h2 id={`${id}-title`}>Add issue</h2>
      <Modal.Content.Header.CloseButton
        aria-label="Close Add issue"
        disabled={creating}
        onclick={close}
      />
    </Modal.Content.Header>
    <Modal.Content.Body
      class="add-issue-body"
      role="region"
      aria-label="Add issue content"
      tabindex={0}
    >
      <form
        id={`${id}-form`}
        class="add-issue-form"
        onsubmit={submit}
        novalidate
        aria-busy={creating}
      >
        <p id={`${id}-help`}>Enter a GitHub, Jira, or Launchpad issue URL.</p>
        <label for={`${id}-url`}>External issue URL</label>
        <TextInput
          id={`${id}-url`}
          type="url"
          autocomplete="url"
          bind:value={issueUrl}
          disabled={creating}
          aria-invalid={!!issueUrlError}
          aria-describedby={`${id}-help${issueUrlError ? ` ${id}-url-error` : ""}`}
          oninput={() => {
            issueUrlError = "";
            createError = "";
          }}
        />
        {#if issueUrlError}
          <p id={`${id}-url-error`} class="form-error" role="alert">
            {issueUrlError}
          </p>
        {/if}
        {#if createError}
          <p class="form-error" role="alert">
            Unable to add issue: {createError}
          </p>
        {/if}
      </form>
    </Modal.Content.Body>
    <Modal.Content.Footer>
      <Button type="button" onclick={close} disabled={creating}>Cancel</Button>
      <Button
        type="submit"
        form={`${id}-form`}
        severity="brand"
        disabled={creating}
      >
        {creating ? "Adding…" : "Add issue"}
      </Button>
    </Modal.Content.Footer>
  </Modal.Content>
</Modal>

<style>
  :global(html:has(dialog.add-issue-dialog[open])) {
    overflow: hidden;
  }
  :global(dialog.ds.modal.add-issue-dialog) {
    width: min(32rem, calc(100vw - 2 * var(--lp-dimension-spacing-inline-m)));
    max-width: calc(100vw - 2 * var(--lp-dimension-spacing-inline-m));
    max-height: calc(100dvh - 2 * var(--lp-dimension-spacing-block-m));
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }
  :global(.add-issue-dialog .add-issue-content) {
    max-height: calc(100dvh - 2 * var(--lp-dimension-spacing-block-m));
    min-height: 0;
    box-sizing: border-box;
  }
  :global(.add-issue-dialog .dialog-content-header),
  :global(.add-issue-dialog .dialog-content-footer) {
    flex-shrink: 0;
  }
  :global(.add-issue-dialog .add-issue-body) {
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    overflow-wrap: anywhere;
  }
  h2,
  p {
    margin: 0;
  }
  .add-issue-form {
    display: flex;
    flex-direction: column;
    gap: var(--lp-dimension-spacing-block-s);
  }
  .form-error {
    color: var(--lp-color-negative);
  }
</style>
