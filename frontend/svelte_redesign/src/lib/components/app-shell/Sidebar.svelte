<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { base } from "$app/paths";
  import { page } from "$app/state";
  import { capitalize } from "$lib/utils/formatting.js";

  interface Props {
    tabs: string[];
  }

  const { tabs }: Props = $props();

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

<nav class="ds side-navigation" aria-label="Main navigation">
  <ul class="ds side-navigation__list">
    {#each navItems as item}
      <li class="ds side-navigation__item" class:active={item.active}>
        <a href={item.href} class="ds side-navigation__link" aria-current={item.active ? "page" : undefined}>
          {item.label}
        </a>
      </li>
    {/each}
  </ul>
</nav>

<style>
  .ds.side-navigation {
    padding: var(--spacing-3) 0;
  }

  .ds.side-navigation__list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .ds.side-navigation__item {
    margin: 0;
  }

  .ds.side-navigation__link {
    display: block;
    padding: var(--spacing-2) var(--spacing-4);
    text-decoration: none;
    color: var(--color-text);
  }

  .ds.side-navigation__link:hover {
    background-color: var(--color-background);
  }

  .ds.side-navigation__item.active .ds.side-navigation__link {
    font-weight: 600;
    border-left: 3px solid var(--color-text);
  }
</style>
