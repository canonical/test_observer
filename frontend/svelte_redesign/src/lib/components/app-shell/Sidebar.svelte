<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { base } from "$app/paths";
  import { page } from "$app/state";
  import { capitalize } from "$lib/utils/formatting.js";
  import { SideNavigation } from "$lib/components/SideNavigation/index.js";

  interface Props {
    tabs: string[];
  }

  const { tabs }: Props = $props();

  let expanded = $state(true);
  const currentPath = $derived(page.url.pathname);

  const navItems = $derived([
    ...tabs.map((family) => ({
      href: `${base}/${family}`,
      label: capitalize(family),
      active: currentPath.startsWith(`${base}/${family}`),
    })),
    {
      href: `${base}/test-results`,
      label: "Test Results",
      active: currentPath === `${base}/test-results`,
    },
    {
      href: `${base}/issues`,
      label: "Issues",
      active: currentPath.startsWith(`${base}/issues`),
    },
    {
      href: `${base}/notifications`,
      label: "Notifications",
      active: currentPath === `${base}/notifications`,
    },
  ]);
</script>

<SideNavigation {expanded}>
  {#snippet logo()}
    <a href="{base}/" class="app-logo" aria-label="Test Observer home">
      Test Observer
    </a>
  {/snippet}
  {#snippet expandToggle(toggleProps)}
    <SideNavigation.ExpandToggle
      {...toggleProps}
      onclick={() => (expanded = !expanded)}
    />
  {/snippet}
  {#each navItems as item}
    <SideNavigation.NavigationItem
      href={item.href}
      selected={item.active}
      aria-current={item.active ? "page" : undefined}
    >
      {item.label}
    </SideNavigation.NavigationItem>
  {/each}
</SideNavigation>

<style>
  .app-logo {
    display: block;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--lp-color-text-default);
    text-decoration: none;
    padding: var(--lp-dimension-spacing-block-s) 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .app-logo:hover {
    text-decoration: none;
    color: var(--lp-color-text-default);
  }
</style>
