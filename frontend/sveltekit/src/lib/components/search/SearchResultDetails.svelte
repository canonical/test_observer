<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import {
    Button,
    DateTime,
    DescriptionList,
    Modal,
  } from "@canonical/svelte-ds-app-launchpad";
  import type { Family } from "$lib/types";
  import type { SearchPageDetailsResponse } from "$lib/types/test-results-search-page-details";

  let {
    result,
    active,
    loading,
    error,
    families,
    onclose,
    onretry,
  }: {
    result: SearchPageDetailsResponse | null;
    active: boolean;
    loading: boolean;
    error: string | null;
    families: Family[];
    onclose: () => void;
    onretry: () => void;
  } = $props();

  const id = $props.id();
  let open = $derived(active);
  const family = $derived(
    families.find((candidate) => candidate.api_name === result?.artefact.family),
  );
  const metadata = $derived(
    Object.entries(result?.test_execution.execution_metadata ?? {}).sort(
      ([a], [b]) => (a < b ? -1 : a > b ? 1 : 0),
    ),
  );
  const created = $derived(result?.test_execution.created_at);
  const validCreated = $derived(
    Boolean(created && Number.isFinite(new Date(created).getTime())),
  );
  const dateFormatter = new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "long",
  });
  const value = (input: string | number | null | undefined) =>
    input === "" || input === null || input === undefined ? "—" : String(input);
</script>

<Modal
  class="search-result-details"
  aria-labelledby={`${id}-title`}
  bind:open
  onclose={(event) => {
    if (!event.currentTarget.open) onclose();
  }}
>
  {#snippet children(commandfor, close)}
    <Modal.Content class="details-content">
      <Modal.Content.Header>
        <h2 id={`${id}-title`}>Test result details</h2>
        <Modal.Content.Header.CloseButton
          {commandfor}
          command="close"
          aria-label="Close details"
        />
      </Modal.Content.Header>
      <Modal.Content.Body
        class="details-body"
        role="region"
        aria-label="Test result details content"
        tabindex={0}
      >
        {#if result}
          <section aria-labelledby={`${id}-case`}>
            <h3 id={`${id}-case`}>Test Case</h3>
            <DescriptionList layout="list" class="scalar-details">
              <DescriptionList.Item name="Name">{value(result.test_result.name)}</DescriptionList.Item>
              <DescriptionList.Item name="Category">{value(result.test_result.category)}</DescriptionList.Item>
              <DescriptionList.Item name="Template ID">{value(result.test_result.template_id)}</DescriptionList.Item>
              <DescriptionList.Item name="Status">{value(result.test_result.status)}</DescriptionList.Item>
            </DescriptionList>
          </section>
          <section aria-labelledby={`${id}-artefact`}>
            <h3 id={`${id}-artefact`}>Artefact</h3>
            <DescriptionList layout="list" class="scalar-details">
              <DescriptionList.Item name="Family">
                {value(family ? family.friendly_name : result.artefact.family)}
              </DescriptionList.Item>
              <DescriptionList.Item name="Name">{value(result.artefact.name)}</DescriptionList.Item>
              <DescriptionList.Item name="Version">{value(result.artefact.version)}</DescriptionList.Item>
              <DescriptionList.Item name="Track">{value(result.artefact.track)}</DescriptionList.Item>
              <DescriptionList.Item name="Architecture">{value(result.artefact_build.architecture)}</DescriptionList.Item>
            </DescriptionList>
          </section>
          <section aria-labelledby={`${id}-execution`}>
            <h3 id={`${id}-execution`}>Test Execution</h3>
            <DescriptionList layout="list" class="scalar-details">
              <DescriptionList.Item name="Execution ID">{value(result.test_execution.id)}</DescriptionList.Item>
              <DescriptionList.Item name="Test Plan">{value(result.test_execution.test_plan)}</DescriptionList.Item>
              <DescriptionList.Item name="Environment">{value(result.test_execution.environment.name)}</DescriptionList.Item>
              <DescriptionList.Item name="Status">{value(result.test_execution.status)}</DescriptionList.Item>
              <DescriptionList.Item name="Created">
                {#if created && validCreated}
                  <DateTime date={created} formatter={dateFormatter} title={created} />
                {:else}
                  —
                {/if}
              </DescriptionList.Item>
            </DescriptionList>
            <h4 id={`${id}-metadata`}>Execution Metadata</h4>
            {#if metadata.length}
              <table class="execution-metadata" aria-labelledby={`${id}-metadata`}>
                <thead>
                  <tr><th scope="col">Category</th><th scope="col">Values</th></tr>
                </thead>
                <tbody>
                  {#each metadata as [category, values] (category)}
                    <tr>
                      <th scope="row">{value(category)}</th>
                      <td>
                        {#if values.length}
                          <ul>{#each [...values].sort() as item, index (index)}<li>{value(item)}</li>{/each}</ul>
                        {:else}
                          —
                        {/if}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {:else}
              <p>No execution metadata available.</p>
            {/if}
          </section>
          {#if result.test_result.issues.length}
            <section aria-labelledby={`${id}-issues`}>
              <h3 id={`${id}-issues`}>Issues</h3>
              <ul class="issues">
                {#each result.test_result.issues as { issue } (issue.id)}
                  <li>
                    <p>{value(issue.key || String(issue.id))}: {value(issue.title)}</p>
                    <DescriptionList layout="list" class="scalar-details">
                      <DescriptionList.Item name="Source">{value(issue.source)}</DescriptionList.Item>
                      <DescriptionList.Item name="Project">{value(issue.project)}</DescriptionList.Item>
                      <DescriptionList.Item name="Status">{value(issue.status)}</DescriptionList.Item>
                    </DescriptionList>
                  </li>
                {/each}
              </ul>
            </section>
          {/if}
          {#if result.test_result.io_log}
            <section aria-labelledby={`${id}-log`}>
              <h3 id={`${id}-log`}>IO Log</h3>
              <pre class="io-log">{result.test_result.io_log}</pre>
            </section>
          {/if}
        {:else if loading}
          <p role="status">Loading test result details…</p>
        {:else if error}
          <section role="alert">
            <p>{error}</p>
            <Button type="button" density="dense" onclick={onretry}>Retry</Button>
          </section>
        {/if}
      </Modal.Content.Body>
      <Modal.Content.Footer>
        <Button type="button" density="dense" onclick={close}>Close</Button>
      </Modal.Content.Footer>
    </Modal.Content>
  {/snippet}
</Modal>

<style>
  :global(html:has(dialog.search-result-details[open])) {
    overflow: hidden;
  }

  :global(dialog.ds.modal.search-result-details) {
    width: min(900px, calc(100vw - 2rem));
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    padding: 0;
    overflow: hidden;
    color: var(--lp-color-text-default);
    background: var(--lp-color-background-default);
  }

  :global(.search-result-details .details-content) {
    max-height: calc(100dvh - 2rem);
    min-height: 0;
    box-sizing: border-box;
  }

  :global(.search-result-details .dialog-content-header),
  :global(.search-result-details .dialog-content-footer) {
    flex-shrink: 0;
  }

  :global(.search-result-details .details-body) {
    min-height: 0;
    overflow: auto;
    overscroll-behavior: contain;
    overflow-wrap: anywhere;
  }

  .execution-metadata {
    width: 100%;
    border-collapse: collapse;
  }

  .execution-metadata th,
  .execution-metadata td {
    padding: 0.5rem;
    border-bottom: 1px solid var(--lp-color-border-default, #ccc);
    text-align: start;
    vertical-align: top;
  }

  .execution-metadata td ul {
    margin: 0;
    padding-inline-start: 1.25rem;
  }

  .issues {
    display: grid;
    gap: 1rem;
    padding-inline-start: 1.25rem;
  }

  .io-log {
    overflow-wrap: anywhere;
    white-space: pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  }

  @media (max-width: 640px) {
    :global(dialog.ds.modal.search-result-details) {
      width: calc(100vw - 1rem);
      max-width: calc(100vw - 1rem);
      max-height: calc(100dvh - 1rem);
    }
  }
</style>
