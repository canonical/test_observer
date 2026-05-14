<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { ArtefactList } from "$lib/components/dashboard/index.js";
  import { capitalize } from "$lib/utils/formatting.js";

  let { data } = $props();
</script>

<svelte:head>
  <title>{capitalize(data.family)} — Test Observer</title>
</svelte:head>

<div class="ds dashboard-page">
  <h1 class="ds dashboard-page__title">{capitalize(data.family)} Update Verification</h1>
  <ArtefactList artefacts={data.artefacts} family={data.family} />
</div>

<style>
  .ds.dashboard-page {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    height: 100%;
  }

  .ds.dashboard-page__title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
  }
</style>
