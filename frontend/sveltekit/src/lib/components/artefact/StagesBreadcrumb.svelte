<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import type { Artefact, Family } from '$lib/types';
  import { stageDisplayName } from '$lib/types';

  interface Props {
    artefact: Artefact;
    family: Family;
  }

  let { artefact, family }: Props = $props();

  const stages = $derived(family.stages);
  const currentIndex = $derived(stages.indexOf(artefact.stage));
</script>

<nav class="stages-breadcrumb" aria-label="Artefact stages">
  {#each stages as stage, i (stage)}
    {#if i > 0}
      <span class="separator" aria-hidden="true">&rsaquo;</span>
    {/if}
    <span
      class="stage"
      class:past={i < currentIndex}
      class:current={i === currentIndex}
      class:future={i > currentIndex}
      aria-current={i === currentIndex ? 'step' : undefined}
    >
      {stageDisplayName(stage)}
    </span>
  {/each}
</nav>

<style>
  .stages-breadcrumb {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.875rem;
  }

  .separator {
    color: var(--lp-color-text-muted);
  }

  .stage {
    font-weight: 400;
    color: var(--lp-color-text-muted);
  }

  .stage.current {
    color: var(--lp-color-brand-default);
    font-weight: 600;
  }

  .stage.past {
    color: var(--lp-color-text-muted);
    opacity: 0.6;
  }

  .stage.future {
    color: var(--lp-color-text-muted);
    opacity: 0.4;
  }
</style>
