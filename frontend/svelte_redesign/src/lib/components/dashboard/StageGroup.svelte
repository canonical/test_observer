<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import type { Artefact } from "$lib/types/artefact.js";
  import ArtefactCard from "./ArtefactCard.svelte";

  interface Props {
    stage: string;
    artefacts: Artefact[];
    family: string;
  }

  const { stage, artefacts, family }: Props = $props();
</script>

<section class="ds stage-group" aria-labelledby="stage-{stage}">
  <div class="ds stage-group__header">
    <h2 id="stage-{stage}" class="ds stage-group__title">{stage}</h2>
    <span class="ds stage-group__count">{artefacts.length}</span>
  </div>
  <div class="ds stage-group__list">
    {#each artefacts as artefact (artefact.id)}
      <ArtefactCard {artefact} {family} />
    {/each}
    {#if artefacts.length === 0}
      <p class="ds stage-group__empty">No artefacts in this stage</p>
    {/if}
  </div>
</section>

<style>
  .ds.stage-group {
    min-width: 320px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .ds.stage-group__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    border-bottom: 2px solid var(--color-border, #d9d9d9);
  }

  .ds.stage-group__title {
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .ds.stage-group__count {
    font-size: 0.75rem;
    font-weight: 500;
    background-color: var(--color-background-alt, #f0f0f0);
    padding: 0.125rem 0.5rem;
    border-radius: 1rem;
    color: var(--color-text-muted, #666);
  }

  .ds.stage-group__list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    overflow-y: auto;
  }

  .ds.stage-group__empty {
    font-size: 0.8125rem;
    color: var(--color-text-muted, #666);
    text-align: center;
    padding: 1rem 0;
  }
</style>
