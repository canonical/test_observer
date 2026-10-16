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
  import { page } from '$app/state';
  import { invalidateAll } from '$app/navigation';
  import { getApiRoot } from '$lib/config';
  import DashboardHeader from '$lib/components/dashboard/DashboardHeader.svelte';
  import ArtefactTable from '$lib/components/dashboard/ArtefactTable.svelte';

  let { data } = $props();

  let table = $state<ReturnType<typeof ArtefactTable> | null>(null);
  let filtered = $state(false);
  let exportAvailable = $state(false);

  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(page.url.href)}`
  );
</script>

<div class="dashboard">
  <DashboardHeader
    family={data.family}
    count={data.artefacts.length}
    {filtered}
    {exportAvailable}
    onClear={() => table?.clearView()}
    onShare={() => table?.shareUrl() ?? page.url.href}
    onExport={() => table?.exportCsv() ?? 'unavailable'}
  />

  {#if data.requiresLogin}
    <div class="login-required" role="status">
      <p class="login-message">You need to be logged in to view these test results.</p>
      <!-- Absolute URL to the backend SAML endpoint, not an app route. -->
      <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
      <a class="login-button" href={loginUrl}>Log in</a>
    </div>
  {:else if data.forbidden}
    <div class="access-denied" role="alert">
      <p class="login-message">
        You don't have permission to view these test results. Contact an administrator if
        you believe this is a mistake.
      </p>
    </div>
  {:else if data.sessionCheckFailed}
    <div class="session-check-failed" role="alert">
      <p class="login-message">
        We couldn't verify your session just now. Please check your connection and try
        again.
      </p>
      <button class="login-button" onclick={() => invalidateAll()}>Retry</button>
    </div>
  {:else}
    <div class="content-row">
      <ArtefactTable
        bind:this={table}
        bind:filtered
        bind:exportAvailable
        artefacts={data.artefacts}
        family={data.family}
      />
    </div>
  {/if}
</div>

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    /* The grid virtualizes against a bounded height, so fill the viewport less
       the app shell's vertical padding rather than growing with the row count. */
    height: calc(100vh - 3rem);
    padding-left: 0;
  }

  .login-required {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding: 2rem 0;
  }

  .access-denied,
  .session-check-failed {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
    padding: 2rem 0;
  }

  .login-message {
    margin: 0;
    font-size: 1rem;
    color: var(--lp-color-text-default);
  }

  .login-button {
    display: inline-block;
    padding: 0.5rem 1.25rem;
    background: var(--lp-color-brand-default);
    color: var(--lp-color-text-on-brand, #fff);
    border: none;
    border-radius: 4px;
    text-decoration: none;
    font: inherit;
    font-weight: 500;
    cursor: pointer;
  }

  .login-button:hover {
    background: var(--lp-color-brand-hover, var(--lp-color-brand-default));
  }

  .content-row {
    display: flex;
    flex: 1;
    min-height: 0;
  }
</style>
