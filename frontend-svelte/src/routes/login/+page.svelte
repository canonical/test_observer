<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { goto } from "$app/navigation";
  import { API_BASE } from "$lib/api/client.js";

  const { data } = $props();

  const returnTo = $derived(data.returnTo);

  $effect(() => {
    if (data.user) {
      goto(returnTo, { replaceState: true });
    }
  });

  const samlUrl = $derived(
    `${API_BASE}/v1/auth/saml?returnTo=${encodeURIComponent(returnTo)}`,
  );
</script>

<div class="login-page">
  <h1>Test Observer</h1>
  <p>Sign in to continue</p>
  <a class="sign-in-button" href={samlUrl} role="button">Sign in with SSO</a>
</div>

<style>
  .login-page {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    gap: var(--spacing-3, 1rem);
  }

  .sign-in-button {
    display: inline-block;
    padding: 0.5rem 1.5rem;
    background-color: var(--color-text, #333);
    color: var(--color-background, #fff);
    text-decoration: none;
    border-radius: 4px;
    font-weight: 600;
  }

  .sign-in-button:hover {
    opacity: 0.9;
  }
</style>
