<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import ExpandableSection from "./ExpandableSection.svelte";
  import EnvironmentSection from "./EnvironmentSection.svelte";
  import type { ArtefactBuild } from "$lib/types/build.js";
  import type { EnvironmentReview, Environment } from "$lib/types/environment.js";

  interface Props {
    build: ArtefactBuild;
    reviews: EnvironmentReview[];
    artefactId: number;
    activeTestExecutionId?: number;
    selectedEnvironments: Set<number>;
    onEnvironmentSelect: (environmentId: number, selected: boolean) => void;
  }

  const { build, reviews, artefactId, activeTestExecutionId, selectedEnvironments, onEnvironmentSelect }: Props = $props();

  const buildLabel = $derived(
    build.revision != null
      ? `${build.architecture} (rev ${build.revision})`
      : build.architecture,
  );

  /** Group test executions by environment */
  const environmentGroups = $derived(() => {
    const groups = new Map<number, { environment: Environment; review: EnvironmentReview | undefined }>();
    for (const exec of build.testExecutions) {
      if (!groups.has(exec.environment.id)) {
        const review = reviews.find(
          (r) => r.environment.id === exec.environment.id && r.artefactBuild.id === build.id,
        );
        groups.set(exec.environment.id, {
          environment: exec.environment,
          review,
        });
      }
    }
    return groups;
  });

  function executionsForEnvironment(environmentId: number) {
    return build.testExecutions
      .filter((e) => e.environment.id === environmentId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }
</script>

{#snippet header()}
  <span class="ds build-section__label">{buildLabel}</span>
  <span class="ds build-section__count">
    ({build.testExecutions.length} test execution{build.testExecutions.length !== 1 ? "s" : ""})
  </span>
{/snippet}

<ExpandableSection {header} open={build.testExecutions.some((e) => e.id === activeTestExecutionId)}>
  {#each [...environmentGroups().entries()] as [envId, { environment, review }] (envId)}
    <EnvironmentSection
      {environment}
      {review}
      executions={executionsForEnvironment(envId)}
      {artefactId}
      {activeTestExecutionId}
      selected={selectedEnvironments.has(envId)}
      onselect={onEnvironmentSelect}
    />
  {/each}
  {#if build.testExecutions.length === 0}
    <p class="ds build-section__empty">No test executions for this build</p>
  {/if}
</ExpandableSection>

<style>
  .ds.build-section__label {
    font-weight: 600;
  }

  .ds.build-section__count {
    color: var(--color-text-muted, #666);
    font-size: 0.875rem;
  }

  .ds.build-section__empty {
    color: var(--color-text-muted, #666);
    font-size: 0.875rem;
    font-style: italic;
    padding: 0.5rem;
  }
</style>
