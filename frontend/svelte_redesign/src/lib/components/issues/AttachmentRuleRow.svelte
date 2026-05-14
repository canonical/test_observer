<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Switch, Chip, Button, DescriptionList } from "@canonical/svelte-ds-app-launchpad";
  import type { AttachmentRule } from "$lib/types/attachment-rule.js";
  import { capitalize } from "$lib/utils/formatting.js";

  interface Props {
    rule: AttachmentRule;
    expanded?: boolean;
    onenabledchange?: (ruleId: number, enabled: boolean) => void;
    onedit?: (ruleId: number) => void;
    ondelete?: (ruleId: number) => void;
  }

  const { rule, expanded = false, onenabledchange, onedit, ondelete }: Props = $props();

  let isExpanded = $state(false);
  let enabled = $state(false);

  $effect(() => {
    isExpanded = expanded;
  });

  $effect(() => {
    enabled = rule.enabled;
  });

  function toggleExpand(): void {
    isExpanded = !isExpanded;
  }

  function handleEnabledChange(): void {
    enabled = !enabled;
    onenabledchange?.(rule.id, enabled);
  }

  const metadataEntries = $derived(
    Object.entries(rule.executionMetadata.data).filter(([, v]) => v.length > 0),
  );
</script>

<div class="ds attachment-rule-row" class:ds-expanded={isExpanded}>
  <div class="ds attachment-rule-row__header">
    <button
      class="ds attachment-rule-row__toggle"
      onclick={toggleExpand}
      aria-expanded={isExpanded}
      aria-label="Toggle rule #{rule.id} details"
    >
      <span class="ds attachment-rule-row__arrow">{isExpanded ? "▼" : "▶"}</span>
      <span class="ds attachment-rule-row__label">Rule #{rule.id}</span>
    </button>

    <div class="ds attachment-rule-row__actions">
      <label class="ds attachment-rule-row__enabled-toggle">
        <Switch checked={enabled} onchange={handleEnabledChange} />
        {enabled ? "Enabled" : "Disabled"}
      </label>
      <Button onclick={() => onedit?.(rule.id)}>Edit</Button>
      <Button severity="negative" onclick={() => ondelete?.(rule.id)}>Delete</Button>
    </div>
  </div>

  {#if isExpanded}
    <div class="ds attachment-rule-row__body">
      <DescriptionList>
        {#if rule.families.length > 0}
          <dt>Families</dt>
          <dd>
            <div class="ds attachment-rule-row__chips">
              {#each rule.families as family (family)}
                <Chip value={capitalize(family)} readonly />
              {/each}
            </div>
          </dd>
        {/if}

        {#if rule.environmentNames.length > 0}
          <dt>Environments</dt>
          <dd>
            <div class="ds attachment-rule-row__chips">
              {#each rule.environmentNames as env (env)}
                <Chip value={env} readonly />
              {/each}
            </div>
          </dd>
        {/if}

        {#if rule.testCaseNames.length > 0}
          <dt>Test Cases</dt>
          <dd>
            <div class="ds attachment-rule-row__chips">
              {#each rule.testCaseNames as tc (tc)}
                <Chip value={tc} readonly />
              {/each}
            </div>
          </dd>
        {/if}

        {#if rule.templateIds.length > 0}
          <dt>Template IDs</dt>
          <dd>
            <div class="ds attachment-rule-row__chips">
              {#each rule.templateIds as tid (tid)}
                <Chip value={tid} readonly />
              {/each}
            </div>
          </dd>
        {/if}

        {#if rule.testResultStatuses.length > 0}
          <dt>Result Statuses</dt>
          <dd>
            <div class="ds attachment-rule-row__chips">
              {#each rule.testResultStatuses as st (st)}
                <Chip value={st} readonly />
              {/each}
            </div>
          </dd>
        {/if}

        {#if metadataEntries.length > 0}
          <dt>Execution Metadata</dt>
          <dd>
            {#each metadataEntries as [key, values] (key)}
              <div class="ds attachment-rule-row__metadata-entry">
                <strong>{key}:</strong> {values.join(", ")}
              </div>
            {/each}
          </dd>
        {/if}
      </DescriptionList>
    </div>
  {/if}
</div>

<style>
  .ds.attachment-rule-row {
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
  }

  .ds.attachment-rule-row__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.75rem;
    gap: 0.5rem;
  }

  .ds.attachment-rule-row__toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font: inherit;
    padding: 0;
  }

  .ds.attachment-rule-row__arrow {
    font-size: 0.75rem;
    width: 1rem;
    text-align: center;
  }

  .ds.attachment-rule-row__label {
    font-weight: 500;
  }

  .ds.attachment-rule-row__actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .ds.attachment-rule-row__enabled-toggle {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.85rem;
    cursor: pointer;
    white-space: nowrap;
  }

  .ds.attachment-rule-row__body {
    padding: 0.75rem;
    border-top: 1px solid var(--color-border, #d9d9d9);
  }

  .ds.attachment-rule-row__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
  }

  .ds.attachment-rule-row__metadata-entry {
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
  }
</style>
