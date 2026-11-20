<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Link } from "@canonical/svelte-ds-app-launchpad";

  let { href, name }: { href: string | null; name: string } = $props();
</script>

{#if href}
  <Link {href} aria-label={`View Run for ${name}`}>View Run</Link>
{:else}
  <span title="No configured route for this artefact family">
    Run unavailable
  </span>
{/if}
