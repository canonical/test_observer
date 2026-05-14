<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Modal, Button, TextInput, Select, Checkbox } from "@canonical/svelte-ds-app-launchpad";
  import type { AttachmentRule } from "$lib/types/attachment-rule.js";
  import type { TestResultStatus } from "$lib/types/test-result.js";
  import { capitalize } from "$lib/utils/formatting.js";

  interface Props {
    familyOptions: string[];
    existingRule?: AttachmentRule;
    onsave: (data: {
      families: string[];
      environmentNames: string[];
      testCaseNames: string[];
      templateIds: string[];
      testResultStatuses: TestResultStatus[];
      executionMetadata: { data: Record<string, string[]> };
    }) => void;
    oncancel: () => void;
  }

  const { familyOptions, existingRule, onsave, oncancel }: Props = $props();

  const allStatuses: TestResultStatus[] = ["FAILED", "PASSED", "SKIPPED"];

  let selectedFamilies = $state<string[]>([]);
  let environmentNamesRaw = $state("");
  let testCaseNamesRaw = $state("");
  let templateIdsRaw = $state("");
  let selectedStatuses = $state<TestResultStatus[]>([]);
  let metadataRaw = $state("");

  $effect(() => {
    selectedFamilies = existingRule?.families ?? [];
    environmentNamesRaw = existingRule?.environmentNames.join(", ") ?? "";
    testCaseNamesRaw = existingRule?.testCaseNames.join(", ") ?? "";
    templateIdsRaw = existingRule?.templateIds.join(", ") ?? "";
    selectedStatuses = existingRule?.testResultStatuses ?? [];
    metadataRaw = existingRule
      ? Object.entries(existingRule.executionMetadata.data)
          .map(([k, v]) => `${k}=${v.join(",")}`)
          .join("\n")
      : "";
  });

  function parseCommaList(raw: string): string[] {
    return raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function parseMetadata(raw: string): Record<string, string[]> {
    const result: Record<string, string[]> = {};
    for (const line of raw.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      const eqIdx = trimmed.indexOf("=");
      if (eqIdx < 0) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const vals = trimmed
        .slice(eqIdx + 1)
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      if (key && vals.length > 0) {
        result[key] = vals;
      }
    }
    return result;
  }

  function handleFamilyToggle(family: string): void {
    if (selectedFamilies.includes(family)) {
      selectedFamilies = selectedFamilies.filter((f) => f !== family);
    } else {
      selectedFamilies = [...selectedFamilies, family];
    }
  }

  function handleStatusToggle(status: TestResultStatus): void {
    if (selectedStatuses.includes(status)) {
      selectedStatuses = selectedStatuses.filter((s) => s !== status);
    } else {
      selectedStatuses = [...selectedStatuses, status];
    }
  }

  function handleSave(): void {
    onsave({
      families: selectedFamilies,
      environmentNames: parseCommaList(environmentNamesRaw),
      testCaseNames: parseCommaList(testCaseNamesRaw),
      templateIds: parseCommaList(templateIdsRaw),
      testResultStatuses: selectedStatuses,
      executionMetadata: { data: parseMetadata(metadataRaw) },
    });
  }

  const isEditing = $derived(existingRule !== undefined);
  const title = $derived(isEditing ? `Edit Rule #${existingRule?.id}` : "Create Attachment Rule");
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="ds attachment-rule-dialog" role="dialog" aria-label={title} tabindex="-1" onkeydown={(e) => { if (e.key === "Escape") oncancel(); }}>
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="ds attachment-rule-dialog__backdrop" role="presentation" onclick={oncancel}></div>
  <div class="ds attachment-rule-dialog__content">
    <h2 class="ds attachment-rule-dialog__title">{title}</h2>

    <div class="ds attachment-rule-dialog__form">
      <fieldset class="ds attachment-rule-dialog__fieldset">
        <legend>Families</legend>
        <div class="ds attachment-rule-dialog__checkbox-group">
          {#each familyOptions as family (family)}
            <label class="ds attachment-rule-dialog__checkbox-label">
              <Checkbox
                checked={selectedFamilies.includes(family)}
                onchange={() => handleFamilyToggle(family)}
              />
              {capitalize(family)}
            </label>
          {/each}
        </div>
      </fieldset>

      <label class="ds attachment-rule-dialog__field">
        <span>Environment Names (comma-separated)</span>
        <TextInput bind:value={environmentNamesRaw} />
      </label>

      <label class="ds attachment-rule-dialog__field">
        <span>Test Case Names (comma-separated)</span>
        <TextInput bind:value={testCaseNamesRaw} />
      </label>

      <label class="ds attachment-rule-dialog__field">
        <span>Template IDs (comma-separated)</span>
        <TextInput bind:value={templateIdsRaw} />
      </label>

      <fieldset class="ds attachment-rule-dialog__fieldset">
        <legend>Test Result Statuses</legend>
        <div class="ds attachment-rule-dialog__checkbox-group">
          {#each allStatuses as status (status)}
            <label class="ds attachment-rule-dialog__checkbox-label">
              <Checkbox
                checked={selectedStatuses.includes(status)}
                onchange={() => handleStatusToggle(status)}
              />
              {status}
            </label>
          {/each}
        </div>
      </fieldset>

      <label class="ds attachment-rule-dialog__field">
        <span>Execution Metadata (key=val1,val2 per line)</span>
        <textarea class="ds attachment-rule-dialog__textarea" bind:value={metadataRaw} rows="3"
        ></textarea>
      </label>
    </div>

    <div class="ds attachment-rule-dialog__footer">
      <Button onclick={oncancel}>Cancel</Button>
      <Button severity="positive" onclick={handleSave}>
        {isEditing ? "Save" : "Create"}
      </Button>
    </div>
  </div>
</div>

<style>
  .ds.attachment-rule-dialog {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .ds.attachment-rule-dialog__backdrop {
    position: absolute;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.4);
  }

  .ds.attachment-rule-dialog__content {
    position: relative;
    background: var(--color-background, #fff);
    border-radius: 0.5rem;
    padding: 1.5rem;
    max-width: 40rem;
    width: 90vw;
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  }

  .ds.attachment-rule-dialog__title {
    margin: 0 0 1rem;
    font-size: 1.25rem;
  }

  .ds.attachment-rule-dialog__form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .ds.attachment-rule-dialog__fieldset {
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    padding: 0.75rem;
  }

  .ds.attachment-rule-dialog__fieldset legend {
    font-weight: 500;
    padding: 0 0.25rem;
  }

  .ds.attachment-rule-dialog__checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.25rem;
  }

  .ds.attachment-rule-dialog__checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
  }

  .ds.attachment-rule-dialog__field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .ds.attachment-rule-dialog__field span {
    font-weight: 500;
    font-size: 0.85rem;
  }

  .ds.attachment-rule-dialog__textarea {
    font: inherit;
    padding: 0.5rem;
    border: 1px solid var(--color-border, #d9d9d9);
    border-radius: 0.25rem;
    resize: vertical;
  }

  .ds.attachment-rule-dialog__footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1rem;
  }
</style>
