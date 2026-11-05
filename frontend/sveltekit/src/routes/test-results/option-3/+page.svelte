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
  import SearchOption3 from "$lib/components/search/SearchOption3.svelte";
  let { data } = $props();
  const url = $derived(page.shallow?.url ?? page.url);
</script>

<SearchOption3
  url={new URL(url.href)}
  routePath={resolve("test-results/option-3")}
  families={data.artefactFamilies}
  base={resolve("").replace(/\/$/, "")}
  navigate={(next) => goto(next)}
/>
