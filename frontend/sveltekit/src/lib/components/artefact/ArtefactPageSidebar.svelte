<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import type { Artefact } from "$lib/types";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import ArtefactInfoSection from "./ArtefactInfoSection.svelte";
  import ArtefactSideFilters from "./ArtefactSideFilters.svelte";

  interface Props {
    artefact: Artefact;
    store: ArtefactPageStore;
  }

  let { artefact, store }: Props = $props();
</script>

<aside class="sidebar">
  <div class="sidebar-scroll">
    <ArtefactInfoSection {artefact} {store} />
    <hr class="divider" />
    <ArtefactSideFilters {store} />
  </div>
</aside>

<style>
  .sidebar {
    width: 280px;
    flex-shrink: 0;
    border-right: 1px solid var(--lp-color-border-low-contrast);
    background: var(--lp-color-background-default);
    overflow: hidden;
  }

  .sidebar-scroll {
    height: 100%;
    overflow-y: auto;
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .divider {
    border: none;
    border-top: 1px solid var(--lp-color-border-low-contrast);
    margin: 16px 0;
  }
</style>
