<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import { stageDisplayName } from '$lib/types';
  import ArtefactCard from './ArtefactCard.svelte';

  let { stage, artefacts, family }: {
    stage: string;
    artefacts: Artefact[];
    family: Family;
  } = $props();
</script>

<section class="stage-column">
  <h2 class="stage-title">{stageDisplayName(stage)}</h2>
  <div class="card-list">
    {#each artefacts as artefact (artefact.id)}
      <ArtefactCard {artefact} {family} />
    {/each}
  </div>
</section>

<style>
  .stage-column {
    flex: 1;
    min-width: 200px;
  }

  .stage-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 16px;
    text-transform: capitalize;
  }

  .card-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
</style>
