<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy } from "svelte";
  import { Switch } from "@canonical/svelte-ds-app-launchpad";
  import { issueErrorMessage, setIssueAutoRerunEnabled } from "$lib/api/issues";
  import {
    issueAutoRerunSession,
    issueAutoRerunUpdates as updates,
  } from "$lib/issueAutoRerunUpdates";
  import { refreshBulkPermissions } from "$lib/testResultsBulkPermissions";

  let { issueId, enabled }: { issueId: number; enabled: boolean } = $props();
  const owner = $derived(issueAutoRerunSession());
  let busy = $state(false);
  let error = $state("");
  let live = true;
  let preflight: AbortController | null = null;

  $effect(() => {
    const session = owner;
    const id = issueId;
    error = "";
    busy = updates.busy(session, id);
    return updates.subscribe(() => {
      busy = updates.busy(session, id);
    });
  });

  onDestroy(() => {
    live = false;
    preflight?.abort();
  });

  async function toggle() {
    const session = issueAutoRerunSession();
    const id = issueId;
    const requested = !enabled;
    const update = updates.begin(session, id);
    if (!update) return;
    const controller = new AbortController();
    preflight = controller;
    error = "";
    const current = () =>
      live && issueId === id && issueAutoRerunSession() === session;
    try {
      const permissions = await refreshBulkPermissions(
        fetch,
        controller.signal,
      );
      // Navigation/unmount can cancel preflight, but a dispatched PATCH is not
      // cancelled on navigation: its validated confirmation belongs in the journal.
      if (!current() || controller.signal.aborted) return;
      const permission = permissions.check("autoRerun", false);
      if (!permission.ok) throw new Error(permission.reason);
      const confirmed = await setIssueAutoRerunEnabled(id, requested);
      if (issueAutoRerunSession() === session)
        updates.confirm(update, confirmed.auto_rerun_enabled);
    } catch (failure) {
      if (!current()) return;
      const message = await issueErrorMessage(failure);
      if (current()) error = `Update not confirmed. ${message}`;
    } finally {
      updates.finish(update);
      if (preflight === controller) preflight = null;
    }
  }
</script>

<section class="auto-rerun" aria-label="Automatic reruns">
  <label>
    <Switch
      class="auto-rerun-switch"
      checked={enabled}
      disabled={busy}
      aria-describedby={`auto-rerun-help-${issueId} auto-rerun-status-${issueId}`}
      onclick={(event) => {
        // Cancel native checkbox activation (pointer AND Space) so the installed
        // Switch's internal checked binding never presents an unconfirmed value.
        event.preventDefault();
        void toggle();
      }}
    />
    Auto-rerun on new matches
  </label>
  <p id={`auto-rerun-help-${issueId}`}>
    Automatically request reruns when new test results match this issue's
    attachment rules. Permissions are checked before saving.
  </p>
  <p id={`auto-rerun-status-${issueId}`} role="status">
    {busy
      ? "Saving… Showing the last confirmed setting."
      : `Confirmed: ${enabled ? "On" : "Off"}.`}
  </p>
  {#if error}<p role="alert">{error} Try the switch again to retry.</p>{/if}
</section>

<style>
  .auto-rerun {
    margin-block-end: var(--lp-dimension-spacing-block-xxl);
  }
  .auto-rerun :global(.auto-rerun-switch) {
    flex-shrink: 0;
  }
  label {
    display: flex;
    align-items: center;
    gap: var(--lp-dimension-spacing-inline-s);
  }
  p {
    margin-block: var(--lp-dimension-spacing-block-s);
  }
</style>
