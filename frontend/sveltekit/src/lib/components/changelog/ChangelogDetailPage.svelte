<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import { FetchError } from "$lib/api/client";
  import { fetchChangelogEntry } from "$lib/api/changelog";
  import { getApiRoot } from "$lib/config";
  import { userStore } from "$lib/stores/user.svelte";
  import type { Family } from "$lib/types";
  import type { AuditDetailResponse } from "$lib/types/openapi";
  import {
    changelogPath,
    operationLabel,
    snapshotValue,
  } from "$lib/utils/changelog";
  import AuditJsonButton from "./AuditJsonButton.svelte";

  interface Props {
    family: Family;
    artefactId: number;
    reviewId?: number;
    auditId: number;
  }
  let { family, artefactId, reviewId, auditId }: Props = $props();
  let entry = $state<AuditDetailResponse | null>(null);
  let status = $state<
    "loading" | "ready" | "login" | "forbidden" | "error" | "notFound"
  >("loading");
  let retry = $state(0);
  const back = $derived(
    resolve(changelogPath(family.name, artefactId, reviewId)),
  );
  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(page.url.href)}`,
  );

  $effect(() => {
    const id = artefactId;
    const expectedFamily = family.api_name;
    const review = reviewId;
    const audit = auditId;
    void retry;
    let active = true;
    status = "loading";
    entry = null;
    async function load() {
      try {
        const result = await fetchChangelogEntry(
          id,
          expectedFamily,
          review,
          audit,
        );
        if (active) {
          entry = result;
          status = result ? "ready" : "notFound";
        }
      } catch (error) {
        if (!active) return;
        if (
          error instanceof FetchError &&
          (error.status === 401 || error.status === 403)
        ) {
          const auth = await userStore.refresh(fetch);
          if (active)
            status =
              auth === "unauthenticated"
                ? "login"
                : auth === "authenticated"
                  ? "forbidden"
                  : "error";
        } else if (error instanceof FetchError && error.status === 404) {
          if (active) status = "notFound";
        } else if (active) status = "error";
      }
    }
    void load();
    return () => {
      active = false;
    };
  });
</script>

<section>
  <a href={back}>← Back to changelog</a>
  <h1>Changelog detail</h1>
  {#if status === "loading"}
    <p role="status">Loading changelog detail…</p>
  {:else if status === "login"}
    <p>You need to be logged in to view this changelog detail.</p>
    <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
    <a href={loginUrl}>Log in</a>
  {:else if status === "forbidden"}
    <p role="alert">You don't have permission to view this changelog detail.</p>
  {:else if status === "notFound"}
    <p role="alert">
      Changelog entry, artefact or environment review not found.
    </p>
  {:else if status === "error"}
    <p role="alert">Could not load the changelog detail.</p>
    <button onclick={() => retry++}>Retry</button>
  {:else if entry}
    <p>
      {operationLabel(entry.operation)} ·
      <time datetime={entry.created_at}
        >{new Date(entry.created_at).toLocaleString()}</time
      >
      ·
      {entry.author.name ?? entry.author.automation_name ?? "Unknown"}{entry
        .author.kind
        ? ` (${entry.author.kind})`
        : ""}
    </p>
    <AuditJsonButton {artefactId} {reviewId} {auditId} />
    <div class="table-container">
      <table>
        <thead><tr><th>Field</th><th>Value</th></tr></thead>
        <tbody>
          {#each Object.entries(entry.data) as [key, value] (key)}
            <tr><td>{key}</td><td>{snapshotValue(value)}</td></tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</section>

<style>
  .table-container {
    overflow-x: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
  }
  th,
  td {
    padding: 12px;
    border-bottom: 1px solid var(--lp-color-border-low-contrast);
    overflow-wrap: anywhere;
  }
</style>
