<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  let { family, count } = $props<{
    family: { name: string };
    count: number | null;
  }>();
</script>

<header class="dashboard-header">
  <h1>{family.name}</h1>
  {#if count !== null}<span class="count">{count} artifacts</span>{/if}
</header>
