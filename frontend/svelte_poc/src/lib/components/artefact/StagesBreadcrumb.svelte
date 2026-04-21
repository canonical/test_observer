<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import { FAMILY_STAGES, stageDisplayName } from '$lib/types';

  interface Props {
    artefact: Artefact;
    family: Family;
  }

  let { artefact, family }: Props = $props();

  const stages = $derived(FAMILY_STAGES[family]);
  const currentIndex = $derived(stages.indexOf(artefact.stage));
</script>

<nav class="breadcrumb" aria-label="Artefact stages">
  {#each stages as stage, i (stage)}
    {#if i > 0}
      <span class="separator">&gt;</span>
    {/if}
    <span
      class="stage"
      class:past={i < currentIndex}
      class:current={i === currentIndex}
      class:future={i > currentIndex}
    >
      {stageDisplayName(stage)}
    </span>
  {/each}
</nav>

<style>
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
  }

  .separator {
    color: #999;
  }

  .stage {
    font-weight: 400;
  }

  .stage.current {
    color: #E95420;
    font-weight: 500;
  }

  .stage.past {
    color: #999;
  }

  .stage.future {
    color: #ccc;
  }
</style>
