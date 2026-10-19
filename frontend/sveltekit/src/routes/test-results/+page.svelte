<!--
  Copyright 2026 Canonical Ltd.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License version 3, as
  published by the Free Software Foundation.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.

  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: GPL-3.0-only
-->

<script lang="ts">
  import { page } from "$app/state";
  import { goto } from "$app/navigation";
  import { resolve } from "$app/paths";
  import TestResultsSearch from "$lib/components/search/TestResultsSearch.svelte";
  let { data } = $props();
</script>

<svelte:head><title>Search test results — Test Observer</title></svelte:head>
<TestResultsSearch
  url={new URL(page.url.href)}
  families={data.artefactFamilies}
  base={resolve("").replace(/\/$/, "")}
  navigate={(url) => goto(url)}
/>
