<!-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { SvelteURLSearchParams } from "svelte/reactivity";
  import { silentApi } from "$lib/api/client";

  type LookupField =
    | "artefacts"
    | "environments"
    | "test_plans"
    | "test_cases"
    | "issues"
    | "reviewer_ids";
  interface Suggestion {
    value: string;
    label: string;
  }
  let {
    field,
    families = [],
    onselect,
  }: {
    field: LookupField;
    families?: string[];
    onselect: (values: string[]) => void;
  } = $props();
  const id = $props.id();
  let query = $state("");
  let suggestions = $state<Suggestion[]>([]);
  let status = $state<"idle" | "loading" | "ready" | "error">("idle");
  let retry = $state(0);
  let generation = 0;
  const isId = $derived(field === "issues" || field === "reviewer_ids");
  const invalidIdQuery = $derived(
    isId &&
      query.trim() !== "" &&
      query.split(",").some((part) => {
        const value = part.trim();
        const idValue = Number(value);
        return (
          !/^[1-9]\d*$/.test(value) ||
          !Number.isSafeInteger(idValue) ||
          idValue > 2_147_483_647
        );
      }),
  );
  const helper = $derived(
    status === "error"
      ? "Suggestions unavailable. You can still add an exact value or ID."
      : status === "loading"
        ? "Loading suggestions…"
        : query.trim().length < 2
          ? "Type at least two characters for suggestions; exact entry is always available."
          : status === "ready" && suggestions.length === 0
            ? "No suggestions found; exact entry is still available."
            : "Choose a suggestion or add an exact value.",
  );

  $effect(() => {
    const text = query.trim();
    const familyValues = [...new Set(families)].sort();
    void retry;
    const current = ++generation;
    const controller = new AbortController();
    suggestions = [];
    status = text.length < 2 ? "idle" : "loading";
    if (text.length < 2) return () => controller.abort();

    const timer = setTimeout(() => {
      void loadSuggestions(text, familyValues, controller.signal).then(
        (items) => {
          if (controller.signal.aborted || current !== generation) return;
          suggestions = items;
          status = "ready";
        },
        () => {
          if (controller.signal.aborted || current !== generation) return;
          suggestions = [];
          status = "error";
        },
      );
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  });

  async function loadSuggestions(
    text: string,
    familyValues: string[],
    signal: AbortSignal,
  ): Promise<Suggestion[]> {
    const endpoint: { path: string; key: string; limit: number } =
      field === "artefacts"
        ? { path: "artefacts/search", key: "artefacts", limit: 50 }
        : field === "environments"
          ? { path: "environments", key: "environments", limit: 50 }
          : field === "test_plans"
            ? { path: "test-plans", key: "test_plans", limit: 50 }
            : field === "test_cases"
              ? { path: "test-cases", key: "test_cases", limit: 50 }
              : field === "issues"
                ? { path: "issues", key: "issues", limit: 10 }
                : { path: "users", key: "users", limit: 10 };
    const { path, key, limit } = endpoint;
    const params = new SvelteURLSearchParams({ q: text, limit: String(limit) });
    if (!isId)
      for (const family of familyValues) params.append("families", family);
    const result = await silentApi<unknown>(`${path}?${params}`, { signal });
    if (!result || typeof result !== "object" || Array.isArray(result))
      return [];
    const values = (result as Record<string, unknown>)[key];
    if (!Array.isArray(values)) return [];
    const items: Suggestion[] = [];
    for (const raw of values.slice(0, limit)) {
      if (isId) {
        if (!raw || typeof raw !== "object" || Array.isArray(raw)) continue;
        const detail = raw as Record<string, unknown>;
        const value = detail.id;
        if (
          typeof value !== "number" ||
          !Number.isSafeInteger(value) ||
          value <= 0 ||
          value > 2_147_483_647
        )
          continue;
        const idValue = String(value);
        let label = `#${idValue}`;
        if (field === "reviewer_ids") {
          // Names/handles are useful, but never render user email addresses.
          const name =
            typeof detail.name === "string" ? detail.name.trim() : "";
          const handle =
            typeof detail.launchpad_handle === "string"
              ? detail.launchpad_handle.trim()
              : "";
          if (name || handle)
            label += ` ${[name, handle ? `@${handle}` : ""].filter(Boolean).join(" ")}`;
        } else {
          const project = [detail.project, detail.key]
            .filter((part) => typeof part === "string" && part)
            .join("/");
          const title = typeof detail.title === "string" ? detail.title : "";
          if (project || title)
            label += ` ${[project, title].filter(Boolean).join(" — ")}`;
        }
        items.push({ value: idValue, label });
      } else {
        const value =
          field === "test_cases" &&
          raw &&
          typeof raw === "object" &&
          !Array.isArray(raw)
            ? (raw as Record<string, unknown>).test_case
            : raw;
        if (typeof value === "string") items.push({ value, label: value });
      }
    }
    return [...new Map(items.map((item) => [item.value, item])).values()];
  }

  function selectExact(value: string) {
    if (isId) {
      if (
        !/^[1-9]\d*$/.test(value) ||
        !Number.isSafeInteger(Number(value)) ||
        Number(value) > 2_147_483_647
      )
        return;
    } else if (value.trim() === "") return;
    onselect([value]);
    query = "";
  }

  function addExact() {
    if (!query.trim()) return;
    if (isId) {
      const ids = query.split(",").map((value) => value.trim());
      if (
        ids.some(
          (value) =>
            !/^[1-9]\d*$/.test(value) ||
            !Number.isSafeInteger(Number(value)) ||
            Number(value) > 2_147_483_647,
        )
      )
        return;
      onselect([...new Set(ids)]);
      query = "";
      return;
    }
    selectExact(query);
  }
</script>

<div class="suggestion-picker" data-suggestion-field={field}>
  <label for={id}
    >Find {field === "reviewer_ids"
      ? "reviewers"
      : field === "issues"
        ? "issues"
        : field.replaceAll("_", " ")}</label
  >
  <input
    {id}
    type="search"
    autocomplete="off"
    bind:value={query}
    onkeydown={(event) => {
      if (event.key === "Enter") event.preventDefault();
    }}
  />
  <p class="hint" role="status">{helper}</p>
  {#if status === "error"}
    <button type="button" onclick={() => retry++}>Retry suggestions</button>
  {/if}
  {#if suggestions.length}
    <ul aria-label={`${field.replaceAll("_", " ")} suggestions`}>
      {#each suggestions as item (item.value)}
        <li>
          <button type="button" onclick={() => selectExact(item.value)}
            >{item.label}</button
          >
        </li>
      {/each}
    </ul>
  {/if}
  <button type="button" onclick={addExact} disabled={!query.trim()}>
    {isId ? "Add exact ID" : "Add exact value"}
  </button>
  {#if invalidIdQuery}
    <p class="hint" role="alert">
      Use positive supported integer IDs; comma-separated IDs are allowed.
    </p>
  {/if}
</div>

<style>
  .suggestion-picker {
    display: grid;
    gap: 0.25rem;
  }
  label {
    font-size: 0.8125rem;
  }
  input {
    box-sizing: border-box;
    width: 100%;
    min-height: 2rem;
    padding: 0.25rem 0.5rem;
    font: inherit;
  }
  ul {
    max-height: 10rem;
    overflow: auto;
    margin: 0.25rem 0;
    padding: 0;
    list-style: none;
  }
  li {
    margin: 0.25rem 0;
  }
  li button {
    width: 100%;
    text-align: left;
    overflow-wrap: anywhere;
  }
  .hint {
    margin: 0.25rem 0;
    color: var(--lp-color-text-muted, #666);
    font-size: 0.8rem;
  }
</style>
