<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { onDestroy, tick, type Snippet } from "svelte";
  import {
    Button,
    Checkbox,
    TextInput,
  } from "@canonical/svelte-ds-app-launchpad";

  let {
    options,
    selected,
    ontoggle,
    children,
  }: {
    options: string[];
    selected: string[];
    ontoggle: (project: string, checked: boolean) => void | Promise<void>;
    children?: Snippet;
  } = $props();
  let search = $state("");
  let root: HTMLFieldSetElement;
  let focusRevision = 0;
  let cancelFocusRestore: (() => void) | null = null;
  onDestroy(() => cancelFocusRestore?.());
  const matches = $derived(
    options.filter((option) =>
      option.toLowerCase().includes(search.trim().toLowerCase()),
    ),
  );

  async function toggle(
    project: string,
    checked: boolean,
    input: HTMLInputElement | null,
  ) {
    cancelFocusRestore?.();
    const revision = ++focusRevision;
    const document = root.ownerDocument;
    let ownsFocus = document.activeElement === input;
    // Remember intervening intent, not just eventual activeElement: navigation
    // can make a deliberately focused *other* control inert and blur it to body.
    const onFocusIntent = (event: FocusEvent) => {
      if (
        event.target !== input &&
        event.target !== document.body &&
        event.target !== document.documentElement
      )
        cancel();
    };
    const cancel = () => {
      ownsFocus = false;
      document.removeEventListener("focusin", onFocusIntent, true);
      if (cancelFocusRestore === cancel) cancelFocusRestore = null;
    };
    cancelFocusRestore = cancel;
    if (ownsFocus) document.addEventListener("focusin", onFocusIntent, true);
    try {
      await ontoggle(project, checked);
      await tick();
      // Only a navigation-only blur may restore the latest still-owned control.
      if (
        ownsFocus &&
        revision === focusRevision &&
        input?.isConnected &&
        !root.closest("[hidden]") &&
        (document.activeElement === document.body ||
          document.activeElement === input)
      )
        input.focus({ preventScroll: true });
    } finally {
      cancel();
    }
  }

  function remove(project: string) {
    // The removed button disappears after URL navigation. Keep focus on a
    // persistent, useful control rather than letting it fall back to the body.
    const searchInput =
      root.querySelector<HTMLInputElement>('input[type="text"]');
    searchInput?.focus();
    void toggle(project, false, searchInput);
  }
</script>

<fieldset bind:this={root} aria-describedby="project-discovery-help">
  <legend>Project</legend>
  <label for="project-search">Search project options</label>
  <TextInput id="project-search" bind:value={search} autocomplete="off" />
  {#if selected.length}
    <ul class="selected-projects" aria-label="Selected projects">
      {#each selected as project (project)}
        <li>
          <Button
            density="dense"
            aria-label={`Remove project ${project}`}
            onclick={() => remove(project)}>{project} ×</Button
          >
        </li>
      {/each}
    </ul>
  {/if}
  <div class="project-options" role="group" aria-label="Project options">
    {#each matches as project (project)}
      <label class="project-option">
        <Checkbox
          value={project}
          checked={selected.includes(project)}
          onchange={(event) =>
            void toggle(
              project,
              event.currentTarget.checked,
              event.currentTarget,
            )}
        />
        <span>{project}</span>
      </label>
    {/each}
    {#if !matches.length}
      <p>No matching project options loaded.</p>
    {/if}
  </div>
  {@render children?.()}
</fieldset>

<style>
  fieldset {
    min-width: 0;
    margin: 0;
    padding: 0;
    border: 0;
  }
  legend {
    padding: 0;
    margin-bottom: var(--lp-dimension-spacing-inline-s);
    font-weight: 500;
  }
  label[for] {
    display: block;
    margin-bottom: var(--lp-dimension-spacing-inline-xs);
  }
  .selected-projects {
    display: flex;
    flex-wrap: wrap;
    gap: var(--lp-dimension-spacing-inline-xs);
    list-style: none;
    margin: var(--lp-dimension-spacing-inline-s) 0;
    padding: 0;
  }
  .selected-projects li {
    max-width: 100%;
    overflow-wrap: anywhere;
  }
  .project-options {
    max-height: 14rem;
    overflow-y: auto;
    margin-top: var(--lp-dimension-spacing-inline-s);
  }
  .project-option {
    display: flex;
    align-items: start;
    gap: var(--lp-dimension-spacing-inline-s);
    padding-block: var(--lp-dimension-spacing-inline-xs);
    overflow-wrap: anywhere;
  }
  p {
    color: var(--lp-color-text-muted);
  }
</style>
