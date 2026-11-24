<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { page } from "$app/state";
  import { resolve } from "$app/paths";
  import { FetchError } from "$lib/api/client";
  import { fetchChangelog } from "$lib/api/changelog";
  import { getApiRoot } from "$lib/config";
  import { userStore } from "$lib/stores/user.svelte";
  import type { Family } from "$lib/types";
  import type { AuditHistoryResponse } from "$lib/types/openapi";
  import { changelogPath, pageOffset } from "$lib/utils/changelog";
  import ChangelogTable from "./ChangelogTable.svelte";

  interface Props {
    family: Family;
    artefactId: number;
    reviewId?: number;
  }
  let { family, artefactId, reviewId }: Props = $props();
  let history = $state<AuditHistoryResponse | null>(null);
  let status = $state<
    "loading" | "ready" | "login" | "forbidden" | "error" | "notFound"
  >("loading");
  let retry = $state(0);
  const offset = $derived(pageOffset(page.url.searchParams.get("page")));
  const back = $derived(resolve(`${family.name}/${artefactId}`));
  const detailBase = $derived(
    resolve(changelogPath(family.name, artefactId, reviewId)),
  );
  const loginUrl = $derived(
    `${getApiRoot()}/v1/auth/saml/login?return_to=${encodeURIComponent(page.url.href)}`,
  );

  $effect(() => {
    const id = artefactId;
    const expectedFamily = family.api_name;
    const review = reviewId;
    const requestedOffset = offset;
    void retry;
    let active = true;
    status = "loading";
    history = null;
    async function load() {
      try {
        const result = await fetchChangelog(
          id,
          expectedFamily,
          review,
          requestedOffset,
        );
        if (active) {
          history = result;
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
  <a href={back}>← Back to artefact</a>
  <h1>
    {reviewId === undefined
      ? "Artefact changelog"
      : "Environment review changelog"}
  </h1>
  {#if status === "loading"}
    <p role="status">Loading changelog…</p>
  {:else if status === "login"}
    <p>You need to be logged in to view this changelog.</p>
    <!-- eslint-disable-next-line svelte/no-navigation-without-resolve -->
    <a href={loginUrl}>Log in</a>
  {:else if status === "forbidden"}
    <p role="alert">You don't have permission to view this changelog.</p>
  {:else if status === "notFound"}
    <p role="alert">Artefact or environment review not found.</p>
  {:else if status === "error"}
    <p role="alert">Could not load the changelog.</p>
    <button onclick={() => retry++}>Retry</button>
  {:else if history}
    <ChangelogTable
      {history}
      url={page.url.href}
      {detailBase}
      {artefactId}
      {reviewId}
    />
  {/if}
</section>
