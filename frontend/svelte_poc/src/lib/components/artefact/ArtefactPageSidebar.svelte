<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import ArtefactInfoSection from './ArtefactInfoSection.svelte';
  import ArtefactSideFilters from './ArtefactSideFilters.svelte';

  interface Props {
    artefact: Artefact;
    family: Family;
    artefactId: number;
    store: ArtefactPageStore;
  }

  let { artefact, family, artefactId, store }: Props = $props();
</script>

<aside class="sidebar">
  <div class="sidebar-scroll">
    <ArtefactInfoSection {artefact} {family} {store} />
    <hr class="divider" />
    <ArtefactSideFilters {store} {family} {artefactId} />
  </div>
</aside>

<style>
  .sidebar {
    width: 300px;
    flex-shrink: 0;
    border-right: 1px solid #e0e0e0;
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
    border-top: 1px solid #e0e0e0;
    margin: 16px 0;
  }
</style>
