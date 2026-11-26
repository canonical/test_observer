<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import type { Artefact } from '$lib/types';
  import { stageDisplayName } from '$lib/types';

  interface Props {
    artefact: Artefact;
  }

  let { artefact }: Props = $props();
</script>

<nav class="stages-breadcrumb" aria-label="Artefact stages">
  <span class="stage current" aria-current="step">
    {stageDisplayName(artefact.stage)}
  </span>
</nav>

<style>
  .stages-breadcrumb {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.875rem;
  }

  .stage {
    font-weight: 400;
    color: var(--lp-color-text-muted);
  }

  .stage.current {
    color: var(--lp-color-brand-default);
    font-weight: 600;
  }
</style>
