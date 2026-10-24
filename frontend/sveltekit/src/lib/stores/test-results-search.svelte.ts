// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { FetchError, silentApi } from "$lib/api/client";
import { userStore } from "$lib/stores/user.svelte";
import {
  searchParams,
  type AppliedSearch,
  type SearchResponse,
} from "$lib/testResultsSearch";

export type SearchAccessError =
  "requiresLogin" | "forbidden" | "sessionCheckFailed";

/** Each request replaces one page. No append cursor or rows survive a URL change. */
export class TestResultsSearchStore {
  loading = $state(false);
  response = $state<SearchResponse | null>(null);
  responseQuery = $state.raw<AppliedSearch | null>(null);
  error = $state<string | null>(null);
  accessError = $state<SearchAccessError | null>(null);
  private generation = 0;
  private controller: AbortController | null = null;

  cancel() {
    ++this.generation;
    this.controller?.abort();
    this.controller = null;
    this.loading = false;
  }

  async search(query: AppliedSearch): Promise<void> {
    this.cancel();
    const generation = this.generation;
    this.response = null;
    this.responseQuery = null;
    this.error = null;
    this.accessError = null;
    if (!query.hasFilters || query.problems.length > 0) return;
    const controller = new AbortController();
    this.controller = controller;
    const current = () => generation === this.generation;
    this.loading = true;
    try {
      const params = searchParams(query.filters, query.limit, query.offset);
      const response = await silentApi<SearchResponse>(
        `test-results?${params}`,
        { signal: controller.signal },
      );
      if (!current()) return;
      if (!response) throw new Error("Empty response");
      this.response = response;
      this.responseQuery = query;
    } catch (error) {
      if (!current()) return;
      if (
        error instanceof FetchError &&
        (error.status === 401 || error.status === 403)
      ) {
        // Abort and generation-guard /me too: an outgoing query's session check
        // must not change the active search or the shared cached user.
        const auth = await userStore.refresh(fetch, controller.signal);
        if (!current()) return;
        this.accessError =
          auth === "unknown"
            ? "sessionCheckFailed"
            : error.status === 403 && auth === "authenticated"
              ? "forbidden"
              : "requiresLogin";
      } else {
        this.error =
          "Could not load test results. Check your connection and try again.";
      }
    } finally {
      if (current()) this.loading = false;
    }
  }
}
