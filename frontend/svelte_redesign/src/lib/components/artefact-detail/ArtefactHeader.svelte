<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { base } from "$app/paths";
  import { StatusBadge } from "$lib/components/common/index.js";
  import VersionHistory from "./VersionHistory.svelte";
  import type { Artefact, ArtefactStatus, ArtefactVersion } from "$lib/types/artefact.js";
  import { patchArtefact } from "$lib/api/artefacts.js";
  import { capitalize } from "$lib/utils/formatting.js";

  interface Props {
    artefact: Artefact;
    family: string;
    versions: ArtefactVersion[];
  }

  const { artefact, family, versions }: Props = $props();

  const statusOptions: ArtefactStatus[] = ["APPROVED", "MARKED_AS_FAILED", "UNDECIDED"];

  let currentStatus = $state<ArtefactStatus>("UNDECIDED");
  let comment = $state("");
  let savingComment = $state(false);
  let savingStatus = $state(false);

  $effect(() => {
    currentStatus = artefact.status;
  });

  $effect(() => {
    comment = artefact.comment ?? "";
  });

  async function handleStatusChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const newStatus = target.value as ArtefactStatus;
    if (newStatus === currentStatus) return;
    savingStatus = true;
    try {
      await patchArtefact(artefact.id, { status: newStatus });
      currentStatus = newStatus;
    } catch {
      target.value = currentStatus;
    } finally {
      savingStatus = false;
    }
  }

  async function saveComment() {
    savingComment = true;
    try {
      await patchArtefact(artefact.id, { comment });
    } finally {
      savingComment = false;
    }
  }

  const breadcrumbs = $derived([
    { label: capitalize(family), href: `${base}/${family}` },
    { label: artefact.name, href: "" },
  ]);

  const metadataEntries = $derived(
    [
      { label: "Stage", value: artefact.stage },
      { label: "Track", value: artefact.track },
      { label: "Store", value: artefact.store },
      { label: "Branch", value: artefact.branch },
      { label: "Series", value: artefact.series },
      { label: "Repo", value: artefact.repo },
      { label: "Source", value: artefact.source },
      { label: "OS", value: artefact.os },
      { label: "Release", value: artefact.release },
      { label: "Owner", value: artefact.owner },
    ].filter((e) => e.value),
  );
</script>

<div class="ds artefact-header">
  <nav class="ds artefact-header__breadcrumbs" aria-label="Breadcrumb">
    <ol>
      {#each breadcrumbs as crumb, i (i)}
        <li>
          {#if crumb.href}
            <a href={crumb.href}>{crumb.label}</a>
          {:else}
            <span>{crumb.label}</span>
          {/if}
        </li>
      {/each}
    </ol>
  </nav>

  <div class="ds artefact-header__title-row">
    <h1 class="ds artefact-header__name">{artefact.name}</h1>
    <StatusBadge status={currentStatus} />
    <select
      class="ds artefact-header__status-select"
      value={currentStatus}
      onchange={handleStatusChange}
      disabled={savingStatus}
      aria-label="Change artefact status"
    >
      {#each statusOptions as opt (opt)}
        <option value={opt}>{opt.replace(/_/g, " ")}</option>
      {/each}
    </select>
  </div>

  <div class="ds artefact-header__meta" role="group" aria-label="Artefact metadata">
    <span class="ds artefact-header__version">v{artefact.version}</span>
    {#if artefact.dueDate}
      <span class="ds artefact-header__due">Due: {artefact.dueDate}</span>
    {/if}
    <span class="ds artefact-header__reviews">
      Reviews: {artefact.completedEnvironmentReviewsCount}/{artefact.allEnvironmentReviewsCount}
    </span>
    {#if artefact.bugLink}
      <a class="ds artefact-header__bug-link" href={artefact.bugLink} target="_blank" rel="noopener noreferrer">
        Bug Link
      </a>
    {/if}
  </div>

  <div class="ds artefact-header__sidebar-section">
    <VersionHistory
      {family}
      currentArtefactId={artefact.id}
      {versions}
    />

    {#if metadataEntries.length > 0}
      <dl class="ds artefact-header__metadata">
        {#each metadataEntries as entry (entry.label)}
          <div class="ds artefact-header__metadata-item">
            <dt>{entry.label}</dt>
            <dd>{entry.value}</dd>
          </div>
        {/each}
      </dl>
    {/if}

    <div class="ds artefact-header__comment">
      <label for="artefact-comment">Comment</label>
      <textarea
        id="artefact-comment"
        bind:value={comment}
        rows="3"
        disabled={savingComment}
      ></textarea>
      <button
        type="button"
        onclick={saveComment}
        disabled={savingComment}
      >
        {savingComment ? "Saving..." : "Save Comment"}
      </button>
    </div>
  </div>
</div>

<style>
  .ds.artefact-header {
    margin-bottom: 1.5rem;
  }

  .ds.artefact-header__breadcrumbs ol {
    display: flex;
    gap: 0.5rem;
    list-style: none;
    padding: 0;
    margin: 0 0 0.75rem;
    font-size: 0.875rem;
  }

  .ds.artefact-header__breadcrumbs li:not(:last-child)::after {
    content: "/";
    margin-left: 0.5rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-header__breadcrumbs a {
    color: var(--color-link, #06c);
    text-decoration: none;
  }

  .ds.artefact-header__title-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }

  .ds.artefact-header__name {
    margin: 0;
    font-size: 1.5rem;
  }

  .ds.artefact-header__status-select {
    padding: 0.25rem 0.5rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    font: inherit;
    font-size: 0.875rem;
  }

  .ds.artefact-header__meta {
    display: flex;
    gap: 1rem;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    font-size: 0.875rem;
    color: var(--color-text-muted, #666);
  }

  .ds.artefact-header__bug-link {
    color: var(--color-link, #06c);
  }

  .ds.artefact-header__sidebar-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .ds.artefact-header__metadata {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 0.5rem;
    margin: 0;
  }

  .ds.artefact-header__metadata-item {
    display: flex;
    flex-direction: column;
  }

  .ds.artefact-header__metadata-item dt {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-muted, #666);
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .ds.artefact-header__metadata-item dd {
    margin: 0;
    font-size: 0.875rem;
  }

  .ds.artefact-header__comment {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }

  .ds.artefact-header__comment label {
    font-size: 0.875rem;
    font-weight: 500;
  }

  .ds.artefact-header__comment textarea {
    padding: 0.375rem 0.5rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    font: inherit;
    resize: vertical;
  }

  .ds.artefact-header__comment button {
    align-self: flex-end;
    padding: 0.375rem 0.75rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    background: var(--color-background, #fff);
    font: inherit;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .ds.artefact-header__comment button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
