<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import SearchOption4 from "$lib/components/search/SearchOption4.svelte";
  let { data } = $props();
  const url = $derived(page.shallow?.url ?? page.url);
</script>

<SearchOption4
  url={new URL(url.href)}
  routePath={resolve("test-results/option-4")}
  families={data.artefactFamilies}
  base={resolve("").replace(/\/$/, "")}
  navigate={(next) => goto(next)}
/>
