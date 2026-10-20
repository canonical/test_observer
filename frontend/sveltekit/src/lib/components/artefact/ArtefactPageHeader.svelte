<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Breadcrumbs, Select } from "@canonical/svelte-ds-app-launchpad";
  import { resolve } from "$app/paths";
  import { goto } from "$app/navigation";
  import type { Artefact, Family } from "$lib/types";
  import { familyDisplayName, formatDueDate } from "$lib/types";
  import type { ArtefactVersion } from "$lib/types/artefact-page";
  import type { ArtefactPageStore } from "$lib/stores/artefact-page.svelte";
  import StagesBreadcrumb from "./StagesBreadcrumb.svelte";
  import ArtefactSignoffButton from "./ArtefactSignoffButton.svelte";
  import ReviewersAvatars from "$lib/components/dashboard/ReviewersAvatars.svelte";

  interface Props {
    artefact: Artefact;
    family: Family;
    versions: ArtefactVersion[];
    store: ArtefactPageStore;
  }

  let { artefact, family, versions, store }: Props = $props();

  const dueDate = $derived(formatDueDate(artefact.due_date));

  const breadcrumbSegments = $derived([
    { label: familyDisplayName(family), href: resolve(family.name) },
    { label: artefact.name },
  ]);

  // $derived so it updates reactively when artefact changes (e.g. on version navigation)
  let selectedVersion = $derived(artefact.id.toString());

  function handleVersionChange(e: Event) {
    const id = (e.target as HTMLSelectElement).value;
    if (id) goto(resolve(`${family.name}/${id}`));
  }

  async function handleStatusChange(
    status: Parameters<typeof store.updateArtefactStatus>[1],
  ) {
    if (!store.canChangeArtefact) return;
    try {
      await store.updateArtefactStatus(artefact.id, status);
    } catch {
      // The API client reports request failures through the global error UI.
    }
  }
</script>

<header class="artefact-header">
  <Breadcrumbs segments={breadcrumbSegments} />

  <div class="header-top">
    <h1 class="artefact-name">{artefact.name}</h1>
    <ArtefactSignoffButton
      {artefact}
      canChangeStatus={store.canChangeArtefact}
      onstatuschange={handleStatusChange}
    />
    <ReviewersAvatars
      reviewers={artefact.reviewers}
      allEnvironmentReviewsCount={artefact.all_environment_reviews_count}
      completedEnvironmentReviewsCount={artefact.completed_environment_reviews_count}
    />
    {#if dueDate}
      <span class="due-date">Due {dueDate}</span>
    {/if}
  </div>

  <div class="header-stage">
    <StagesBreadcrumb {artefact} {family} />
  </div>

  {#if versions.length > 0}
    <div class="header-version">
      <span class="version-label">version</span>
      <Select value={selectedVersion} onchange={handleVersionChange}>
        {#each versions as v (v.artefact_id)}
          <option value={v.artefact_id.toString()}>{v.version}</option>
        {/each}
      </Select>
    </div>
  {:else}
    <div class="header-version">
      <span class="version-label">version</span>
      <span class="version-value">{artefact.version}</span>
    </div>
  {/if}
</header>

<style>
  .artefact-header {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
    margin-bottom: 16px;
  }

  .header-top {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .artefact-name {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 400;
    color: var(--lp-color-text-default);
  }

  .due-date {
    font-size: 0.875rem;
    color: var(--lp-color-text-muted);
  }

  .header-version {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
  }

  .version-label {
    color: var(--lp-color-text-muted);
    font-weight: 500;
  }

  .version-value {
    color: var(--lp-color-text-default);
    font-family: monospace;
  }
</style>
