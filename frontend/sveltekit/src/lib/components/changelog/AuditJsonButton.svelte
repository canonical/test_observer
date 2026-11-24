<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { onDestroy } from "svelte";
  import { fetchApi } from "$lib/api/client";
  import { auditPath } from "$lib/utils/changelog";

  interface Props {
    artefactId: number;
    reviewId?: number;
    auditId: number;
  }
  let { artefactId, reviewId, auditId }: Props = $props();
  let loading = $state(false);
  let error = $state("");
  let pending: { tab: Window; controller: AbortController } | undefined;

  onDestroy(() => {
    pending?.controller.abort();
    pending?.tab.close();
  });

  async function openJson() {
    error = "";
    let tab: Window | null;
    try {
      tab = window.open("", "_blank");
    } catch {
      error = "Could not open a new tab. Please allow pop-ups and try again.";
      return;
    }
    if (!tab) {
      error = "Could not open a new tab. Please allow pop-ups and try again.";
      return;
    }
    tab.opener = null;
    const controller = new AbortController();
    pending = { tab, controller };
    loading = true;
    let objectUrl: string | undefined;
    try {
      const response = await fetchApi(
        `/audit/${auditPath(artefactId, reviewId)}/${auditId}`,
        { signal: controller.signal },
      );
      if (!response.ok) {
        error =
          response.status === 401 || response.status === 403
            ? "Could not open JSON: login or permission required."
            : "Could not load JSON. Please try again.";
        return;
      }
      const blob = await response.blob();
      if (controller.signal.aborted) return;
      if (tab.closed) {
        error = "The JSON tab was closed. Please try again.";
        return;
      }
      objectUrl = URL.createObjectURL(blob);
      tab.location.replace(objectUrl);
      const url = objectUrl;
      objectUrl = undefined;
      // Give the browser time to consume the URL before releasing it.
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      if (!controller.signal.aborted)
        error = "Could not open JSON. Please try again.";
    } finally {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      if (error || controller.signal.aborted) tab.close();
      pending = undefined;
      loading = false;
    }
  }
</script>

<button type="button" disabled={loading} onclick={openJson}>JSON</button>
{#if loading}<span role="status">Loading JSON…</span>{/if}
{#if error}<span role="alert">{error}</span>{/if}
