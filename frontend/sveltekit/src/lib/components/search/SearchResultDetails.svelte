<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import {
    Button,
    DateTime,
    DescriptionList,
    Link,
    Modal,
  } from "@canonical/svelte-ds-app-launchpad";
  import { familyDisplayName, type Family } from "$lib/types";
  import { viewRunPath, type SearchResult } from "$lib/testResultsSearch";

  let {
    result,
    families,
    base,
    onclose,
  }: {
    result: SearchResult | null;
    families: Family[];
    base: string;
    onclose: () => void;
  } = $props();
  const id = $props.id();
  let open = $derived(result !== null);
  const family = $derived(
    families.find((family) => family.api_name === result?.artefact.family),
  );
  const runHref = $derived(result ? viewRunPath(result, families, base) : null);
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
  const value = (value: string | number | null | undefined) =>
    value === "" || value === null || value === undefined ? "—" : String(value);
</script>

<Modal
  class="search-result-details"
  aria-labelledby={`${id}-title`}
  bind:open
  onclose={(event) => {
    // A queued close from an invalidated dataset must not close a newer open.
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
              <DescriptionList.Item name="Name"
                >{value(result.test_result.name)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Category"
                >{value(result.test_result.category)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Template ID"
                >{value(result.test_result.template_id)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Status"
                >{value(result.test_result.status)}</DescriptionList.Item
              >
            </DescriptionList>
          </section>
          <section aria-labelledby={`${id}-artefact`}>
            <h3 id={`${id}-artefact`}>Artefact</h3>
            <DescriptionList layout="list" class="scalar-details">
              <DescriptionList.Item name="Family"
                >{value(
                  family ? familyDisplayName(family) : result.artefact.family,
                )}</DescriptionList.Item
              >
              <DescriptionList.Item name="Name"
                >{value(result.artefact.name)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Version"
                >{value(result.artefact.version)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Track"
                >{value(result.artefact.track)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Architecture"
                >{value(
                  result.artefact_build.architecture,
                )}</DescriptionList.Item
              >
            </DescriptionList>
          </section>
          <section aria-labelledby={`${id}-execution`}>
            <h3 id={`${id}-execution`}>Test Execution</h3>
            <DescriptionList layout="list" class="scalar-details">
              <DescriptionList.Item name="Execution ID"
                >{value(result.test_execution.id)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Test Plan"
                >{value(result.test_execution.test_plan)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Environment"
                >{value(
                  result.test_execution.environment?.name,
                )}</DescriptionList.Item
              >
              <DescriptionList.Item name="Status"
                >{value(result.test_execution.status)}</DescriptionList.Item
              >
              <DescriptionList.Item name="Created">
                {#if created && validCreated}<DateTime
                    date={created}
                    formatter={dateFormatter}
                    title={created}
                  />{:else}—{/if}
              </DescriptionList.Item>
            </DescriptionList>
            <h4 id={`${id}-metadata`}>Execution Metadata</h4>
            {#if metadata.length}
              <table
                class="execution-metadata"
                aria-labelledby={`${id}-metadata`}
              >
                <thead>
                  <tr
                    ><th scope="col">Category</th><th scope="col">Values</th
                    ></tr
                  >
                </thead>
                <tbody>
                  {#each metadata as [category, values] (category)}
                    <tr>
                      <th scope="row">{value(category)}</th>
                      <td>
                        {#if values.length}<ul>
                            {#each [...values].sort() as item, index (index)}<li
                              >
                                {value(item)}
                              </li>{/each}
                          </ul>{:else}—{/if}
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            {:else}<p>No execution metadata available.</p>{/if}
          </section>
          {#if result.test_result.issues?.length}
            <section aria-labelledby={`${id}-issues`}>
              <h3 id={`${id}-issues`}>Issues</h3>
              <ul class="issues">
                {#each result.test_result.issues as { issue } (issue.id)}
                  <li>
                    <!-- Future internal route is intentional, even before its page exists. -->
                    <Link
                      href={`${base}/issues/${issue.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label={`View issue ${issue.key || issue.id}`}
                    >
                      {value(issue.key || String(issue.id))}: {value(
                        issue.title,
                      )}
                    </Link>
                    <DescriptionList layout="list" class="scalar-details">
                      <DescriptionList.Item name="Source"
                        >{value(issue.source)}</DescriptionList.Item
                      >
                      <DescriptionList.Item name="Project"
                        >{value(issue.project)}</DescriptionList.Item
                      >
                      <DescriptionList.Item name="Status"
                        >{value(issue.status)}</DescriptionList.Item
                      >
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
        {/if}
      </Modal.Content.Body>
      <Modal.Content.Footer>
        {#if runHref && result}
          <Link
            href={runHref}
            aria-label={`View Run for ${result.test_result.name}`}
            >View Run</Link
          >
        {:else}<span title="No configured route for this artefact family"
            >Run unavailable</span
          >{/if}
        <Button type="button" density="dense" onclick={close}>Close</Button>
      </Modal.Content.Footer>
    </Modal.Content>
  {/snippet}
</Modal>

<style>
  :global(html:has(dialog.search-result-details[open])) {
    overflow: hidden;
  }
  /* Beat the installed .ds.modal width rule, independent of stylesheet order. */
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
  /* Pragma's list semantics/typography, with top-aligned label/value rows
     instead of its dotted leaders and right-aligned values. Modal-local only. */
  :global(dialog.search-result-details .scalar-details .description-list-item) {
    display: grid;
    grid-template-columns: min(11rem, 30%) minmax(0, 1fr);
    align-items: start;
    column-gap: 1rem;
  }
  :global(
    dialog.search-result-details .scalar-details .description-list-item::before
  ) {
    display: none;
  }
  :global(
    dialog.search-result-details .scalar-details .description-list-item dt
  ),
  :global(
    dialog.search-result-details .scalar-details .description-list-item dd
  ) {
    min-width: 0;
    margin: 0;
    text-align: start;
  }
  .execution-metadata {
    width: 100%;
    table-layout: fixed;
    border-collapse: collapse;
    font: var(--ds-typography-text-secondary);
  }
  .execution-metadata th,
  .execution-metadata td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
    text-align: start;
    vertical-align: top;
    overflow-wrap: anywhere;
  }
  .execution-metadata th:first-child {
    width: 35%;
    padding-left: 0;
  }
  .execution-metadata th:last-child,
  .execution-metadata td {
    padding-right: 0;
  }
  .execution-metadata li {
    white-space: pre-wrap;
  }
  .execution-metadata li + li {
    margin-top: 0.25rem;
  }
  h2 {
    font-size: 1.5rem;
    margin: 0;
  }
  h3 {
    font-size: 1.125rem;
    margin: 0 0 0.75rem;
  }
  h4 {
    font-size: 1rem;
    margin: 1rem 0 0.5rem;
  }
  section + section {
    margin-top: 1.5rem;
  }
  ul {
    padding-left: 1.25rem;
    margin: 0;
  }
  .issues > li + li {
    margin-top: 1rem;
  }
  .io-log {
    font-family: monospace;
    font-size: 0.875rem;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    padding: 0.75rem;
    border: 1px solid var(--lp-color-border-low-contrast);
    background: var(--lp-color-background-default);
    user-select: text;
  }
</style>
