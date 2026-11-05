<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import type { Family } from "$lib/types";
  import SearchOption2 from "./SearchOption2.svelte";

  let {
    url,
    routePath,
    families,
    base,
    navigate,
  }: {
    url: URL;
    routePath: string;
    families: Family[];
    base: string;
    navigate: (url: string | URL) => Promise<unknown>;
  } = $props();
</script>

<SearchOption2 {url} {routePath} {families} {base} {navigate} variant={3} />
