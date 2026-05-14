<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import "@canonical/svelte-ds-app-launchpad/styles.css";
  import "@canonical/launchpad-design-tokens/dist/css/dimension/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/typography/responsive.css";
  import "@canonical/launchpad-design-tokens/dist/css/opacity/opacity.css";
  import "@canonical/launchpad-design-tokens/dist/css/transition/preferred.css";
  import "@canonical/launchpad-design-tokens/dist/css/color/light.css";

  import { AppShell, Sidebar, Header } from "$lib/components/app-shell/index.js";
  import { setUser } from "$lib/stores/auth.svelte.js";
  import { page } from "$app/state";
  import { base } from "$app/paths";

  let { children, data } = $props();

  $effect(() => {
    setUser(data.user);
  });

  const isLoginPage = $derived(page.url.pathname === `${base}/login`);
</script>

{#if isLoginPage}
  {@render children()}
{:else}
  <AppShell>
    {#snippet sidebar()}
      <Sidebar tabs={data.config.tabs} />
    {/snippet}
    {#snippet header()}
      <Header user={data.user} />
    {/snippet}
    {@render children()}
  </AppShell>
{/if}
