<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Button, TextInput } from "@canonical/svelte-ds-app-launchpad";
  import {
    lookupValues,
    suggestionScope,
    type ValueSuggestion,
  } from "$lib/searchFilterSuggestions";
  import { searchFilterLabelCache } from "$lib/searchFilterLabels";
  import {
    issueRequestError,
    parseIssueReference,
    resolveExistingIssue,
    type IssueChoice,
    type IssueOperation,
  } from "$lib/testResultsIssues";
  import type { Capability } from "$lib/testResultsBulk";
  let {
    operation,
    origin,
    base,
    allowed,
    onchoose,
  }: {
    operation: IssueOperation;
    origin: string;
    base: string;
    allowed: () => Capability<true>;
    onchoose: (choice: IssueChoice) => void;
  } = $props();
  const id = $props.id();
  let query = $state("");
  let options = $state<ValueSuggestion[]>([]);
  let status = $state("");
  let error = $state("");
  let resolving = $state(false);
  let retry = $state(0);
  const reference = $derived(parseIssueReference(query, origin, base));
  $effect(() => {
    const text = query.trim();
    const scope = suggestionScope();
    const permission = allowed();
    void retry;
    const controller = new AbortController();
    const current = () =>
      !controller.signal.aborted && scope === suggestionScope() && allowed().ok;
    options = [];
    error = "";
    resolving = false;
    status =
      text.length < 2
        ? "Type at least 2 characters for suggestions, or enter an issue ID/link."
        : "";
    const timer =
      permission.ok && text.length >= 2 && !/^https?:|^\//i.test(text)
        ? setTimeout(() => {
            status = "Loading suggestions…";
            void lookupValues("issues", text, [], controller.signal).then(
              (items) => {
                if (!current()) return;
                options = items;
                status = items.length
                  ? "Choose one existing issue (up to 10 suggestions)."
                  : "No suggestions. Enter an internal ID or supported issue URL.";
              },
              (cause: unknown) => {
                if (current())
                  void issueRequestError(cause).then((message) => {
                    if (current()) error = message;
                  });
              },
            );
          }, 250)
        : undefined;
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  });
  let resolveController: AbortController | undefined;
  $effect(() => {
    void query;
    void suggestionScope();
    return () => resolveController?.abort();
  });
  function choose(item: ValueSuggestion) {
    if (!allowed().ok) return;
    searchFilterLabelCache().prime("issues", Number(item.value), item.label);
    onchoose({
      kind: "existing",
      issue: { id: Number(item.value), label: item.label },
    });
  }
  async function useReference() {
    if (resolving || !reference.ok || !allowed().ok) return;
    const frozen = reference.value;
    if (operation === "attach" && frozen.kind === "external") {
      onchoose({ kind: "external", url: frozen.url });
      return;
    }
    const controller = new AbortController();
    resolveController = controller;
    resolving = true;
    error = "";
    try {
      const issue = await resolveExistingIssue(frozen, controller.signal);
      if (!controller.signal.aborted && allowed().ok) {
        searchFilterLabelCache().prime("issues", issue.id, issue.label);
        onchoose({ kind: "existing", issue });
      }
    } catch (cause) {
      const message = await issueRequestError(cause);
      if (!controller.signal.aborted) error = message;
    } finally {
      if (!controller.signal.aborted) resolving = false;
    }
  }
  function keyboard(event: KeyboardEvent) {
    if (event.key === "Enter" && event.target === document.getElementById(id))
      event.preventDefault();
    if (!["ArrowUp", "ArrowDown"].includes(event.key)) return;
    const root = document.getElementById(`${id}-picker`);
    const targets = [
      document.getElementById(id),
      ...Array.from(
        root?.querySelectorAll<HTMLButtonElement>(".issue-options button") ??
          [],
      ),
    ];
    const index = targets.indexOf(document.activeElement as HTMLElement);
    if (index < 0) return;
    event.preventDefault();
    targets[
      Math.max(
        0,
        Math.min(
          targets.length - 1,
          index + (event.key === "ArrowDown" ? 1 : -1),
        ),
      )
    ]?.focus();
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div id={`${id}-picker`} onkeydown={keyboard}>
  <label for={id}>Find issue or enter ID / URL</label>
  <TextInput
    {id}
    name="bulk-issue"
    type="search"
    bind:value={query}
    disabled={!allowed().ok || resolving}
    aria-describedby={`${id}-hint`}
  />
  <p id={`${id}-hint`}>
    Select one existing issue. Internal links must belong to this site. {operation ===
    "attach"
      ? "A supported tracker URL can create or find an issue only when you submit; this needs change_issue permission."
      : "External URLs must resolve to one exact existing issue. Detach never creates issues."}
  </p>
  <p role="status">{status}</p>
  <ul class="issue-options" aria-label="Issue suggestions">
    {#each options as item (item.value)}<li>
        <Button
          type="button"
          density="dense"
          onclick={() => choose(item)}
          disabled={!allowed().ok}>{item.label}</Button
        >
      </li>{/each}
  </ul>
  <Button
    type="button"
    density="dense"
    disabled={!reference.ok || !allowed().ok || resolving}
    onclick={useReference}
    >{resolving ? "Resolving issue…" : "Use issue reference"}</Button
  >
  {#if query && !reference.ok}<p>{reference.reason}</p>{/if}
  {#if error}<p role="alert">{error}</p>
    <Button type="button" density="dense" onclick={() => retry++}
      >Retry suggestions</Button
    >{/if}
</div>

<style>
  label {
    display: block;
    margin-bottom: 0.5rem;
  }
  p {
    font-size: 0.875rem;
  }
  :global(.bulk-issue-review .text-input) {
    width: 100%;
    box-sizing: border-box;
  }
  ul {
    list-style: none;
    padding: 0;
    overflow-wrap: anywhere;
  }
  li {
    margin: 0.4rem 0;
  }
  .issue-options :global(button) {
    width: 100%;
    justify-content: flex-start;
    white-space: normal;
    text-align: left;
    overflow-wrap: anywhere;
  }
</style>
