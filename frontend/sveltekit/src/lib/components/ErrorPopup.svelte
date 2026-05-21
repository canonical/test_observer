<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Button } from '@canonical/svelte-ds-app-launchpad';
  import { errorStore } from '$lib/stores/error.svelte';
</script>

{#if errorStore.hasError}
  <div class="overlay" role="presentation" onclick={() => errorStore.clear()}>
    <dialog class="error-dialog" open aria-modal="true" role="alertdialog">
      <h2>Error</h2>
      <p>{errorStore.message}</p>
      <Button severity="negative" onclick={(e: MouseEvent) => { e.stopPropagation(); errorStore.clear(); }}>
        Dismiss
      </Button>
    </dialog>
  </div>
{/if}

<style>
  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: grid;
    place-items: center;
    z-index: 1000;
  }

  .error-dialog {
    background: white;
    border: none;
    border-radius: 8px;
    padding: 24px;
    max-width: 480px;
    width: 90%;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .error-dialog h2 {
    margin: 0 0 12px;
    color: #c7162b;
  }
</style>
