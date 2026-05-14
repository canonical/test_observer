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

<style>
  /*
   * Bridge the generic --color-* and --spacing-* variables used throughout
   * custom components to the actual Pragma / Launchpad design tokens.
   * Without this the variables resolve to nothing (no fallback), leaving
   * the UI completely unstyled.
   */
  :global(:root) {
    /* Spacing scale (--spacing-N used in component CSS) */
    --spacing-1: var(--lp-dimension-spacing-block-xxxs);
    --spacing-2: var(--lp-dimension-spacing-block-xxs);
    --spacing-3: var(--lp-dimension-spacing-block-xs);
    --spacing-4: var(--lp-dimension-spacing-block-s);
    --spacing-5: var(--lp-dimension-spacing-block-m);
    --spacing-6: var(--lp-dimension-spacing-block-l);

    /* Colour aliases */
    --color-background: var(--lp-color-background-default);
    --color-background-alt: var(--lp-color-background-alt);
    --color-text: var(--lp-color-text-default);
    --color-text-muted: var(--lp-color-text-muted);
    --color-border: var(--lp-color-border-default);
    --color-brand: var(--lp-color-brand-default);

    --color-positive: var(--lp-color-positive);
    --color-positive-background: var(--lp-color-background-positive-default);
    --color-positive-text: var(--lp-color-text-default);

    --color-negative: var(--lp-color-negative);
    --color-negative-background: var(--lp-color-background-negative-default);
    --color-negative-text: var(--lp-color-text-default);

    --color-caution: var(--lp-color-caution);
    --color-caution-background: var(--lp-color-background-caution-default);
    --color-information: var(--lp-color-information);
    --color-information-background: var(--lp-color-background-information-default);
    /* SideNavigation --tmp-* tokens (upstream pending rename to --lp-*) */
    --tmp-color-background-neutral-active: var(--lp-color-background-neutral-active);
    --tmp-color-border-highlight: var(--lp-color-border-highlight);
  }
</style>
