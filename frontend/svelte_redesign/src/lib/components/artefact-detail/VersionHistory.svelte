<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";
  import type { ArtefactVersion } from "$lib/types/artefact.js";

  interface Props {
    family: string;
    currentArtefactId: number;
    versions: ArtefactVersion[];
  }

  const { family, currentArtefactId, versions }: Props = $props();

  function handleVersionChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const artefactId = Number(target.value);
    if (artefactId && artefactId !== currentArtefactId) {
      void goto(`${base}/${family}/${artefactId}`);
    }
  }
</script>

<div class="ds version-history">
  <label class="ds version-history__label" for="version-select">Version</label>
  <select
    id="version-select"
    class="ds version-history__select"
    value={String(currentArtefactId)}
    onchange={handleVersionChange}
  >
    {#each versions as version (version.artefactId)}
      <option value={String(version.artefactId)}>
        {version.version}
      </option>
    {/each}
  </select>
</div>

<style>
  .ds.version-history {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .ds.version-history__label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-muted, #666);
  }

  .ds.version-history__select {
    padding: 0.375rem 0.5rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    font: inherit;
    background: var(--color-background, #fff);
  }
</style>
