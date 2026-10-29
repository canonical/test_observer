// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import {
  createServerDataSource,
  type ServerController,
  type ServerState,
  type GridRowModel,
} from "@svgrid/grid";
import { FetchError, silentApi } from "$lib/api/client";
import type { Family } from "$lib/types";
import {
  searchRangeParams,
  toSearchGridRow,
  type AppliedSearch,
  type SearchGridRow,
  type SearchTableResponse,
} from "$lib/testResultsSearch";
import { userStore, type AuthStatus } from "$lib/stores/user.svelte";

export type SearchAccessError =
  "requiresLogin" | "forbidden" | "sessionCheckFailed";

export const SEARCH_BLOCK_SIZE = 50;
export const SEARCH_MAX_BLOCKS = 8;
export const SEARCH_MAX_CONCURRENT_BLOCKS = 2;

/**
 * Owns one filter identity and its SvGrid infinite row model. Replacing the
 * search disposes the old controller (aborting its blocks) and starts a new
 * range cache at row zero.
 */
export class TestResultsSearchStore {
  state = $state.raw<ServerState<SearchGridRow> | null>(null);
  controller = $state.raw<ServerController<SearchGridRow> | null>(null);
  rowModel = $state.raw<GridRowModel<SearchGridRow> | null>(null);
  modelQuery = $state.raw<AppliedSearch | null>(null);
  response = $state.raw<SearchTableResponse | null>(null);
  responseQuery = $state.raw<AppliedSearch | null>(null);
  loading = $state(false);
  error = $state<string | null>(null);
  accessError = $state<SearchAccessError | null>(null);

  private generation = 0;
  private releasePending: (() => void) | null = null;
  private totalCount: number | null = null;

  cancel() {
    ++this.generation;
    this.releasePending?.();
    this.releasePending = null;
    this.controller?.dispose();
    this.controller = null;
    this.rowModel = null;
    this.modelQuery = null;
    this.state = null;
    this.response = null;
    this.responseQuery = null;
    this.totalCount = null;
    this.loading = false;
  }

  async search(
    query: AppliedSearch,
    families: Family[] = [],
    base = "",
  ): Promise<void> {
    this.cancel();
    this.error = null;
    this.accessError = null;
    if (query.problems.length > 0) return;
    this.modelQuery = query;

    const generation = this.generation;
    const current = () => generation === this.generation;
    let firstResponseReceived = false;
    const initialLoad = new Promise<void>((resolve) => {
      this.releasePending = resolve;
    });
    this.loading = true;
    const controller = createServerDataSource<SearchGridRow>(
      {
        getRows: async (request) => {
          const params = searchRangeParams(
            query.filters,
            request.startRow,
            request.endRow,
          );
          const includeCount = this.totalCount === null;
          params.set("include_count", String(includeCount));
          try {
            const response = await silentApi<SearchTableResponse>(
              `test-results/search-page?${params}`,
              { signal: request.signal },
            );
            if (!response || !current() || request.signal?.aborted) {
              throw abortError();
            }
            if (typeof response.count === "number")
              this.totalCount = response.count;
            if (this.totalCount === null) {
              throw new Error(
                "The search page did not return its initial result count.",
              );
            }
            this.responseQuery = query;
            this.response = response;
            return {
              rows: response.rows.map((result) =>
                toSearchGridRow(result, families, base),
              ),
              rowCount: this.totalCount,
            };
          } catch (error) {
            if (!current() || request.signal?.aborted) throw error;
            if (
              error instanceof FetchError &&
              (error.status === 401 || error.status === 403)
            ) {
              const auth = await userStore.refresh(
                globalThis.fetch,
                request.signal,
              );
              if (!current() || request.signal?.aborted) throw error;
              this.accessError = accessErrorFor(error.status, auth);
            } else {
              this.error =
                "Could not load test results. Check your connection and try again.";
            }
            throw error;
          } finally {
            if (request.startRow === 0 && current()) {
              firstResponseReceived = true;
              if (this.state && !this.state.loading) {
                this.releasePending?.();
                this.releasePending = null;
              }
            }
          }
        },
      },
      {
        mode: "infinite",
        blockSize: SEARCH_BLOCK_SIZE,
        maxBlocksInCache: SEARCH_MAX_BLOCKS,
        maxConcurrentRequests: SEARCH_MAX_CONCURRENT_BLOCKS,
        // One placeholder is enough before the first count lands. Avoid
        // inventing a 50-row scrollbar that could queue speculative blocks.
        initialRowCount: 1,
        getRowId: (row) => String(row.id),
        onChange: (state) => {
          if (!current()) return;
          this.state = state;
          this.loading = state.loading;
          if (firstResponseReceived && !state.loading) {
            this.releasePending?.();
            this.releasePending = null;
          }
        },
      },
    );
    // Do not expose the controller's optional setSort/setFilter seams to the
    // grid. Those seams make SvGrid switch into external-sort/filter mode and
    // its initial empty-state callbacks would purge valid server blocks.
    this.rowModel = {
      subscribe: (onChange) => controller.subscribe(onChange),
      getRows: () => controller.getRows(),
      isLoading: () => controller.isLoading(),
      getRowId: (row) => String(row.id),
      setViewport: (start, end) => {
        controller.setViewport(start, end);
      },
      rowPlaceholder: (row, index) =>
        controller.rowPlaceholder?.(row, index) ?? null,
      retryRow: (row, index) => {
        controller.retryRow?.(row, index);
      },
    };
    this.controller = controller;
    // Ensure the initial unfiltered (or filtered) recent range is requested
    // immediately; the grid's own viewport notification is safely deduped.
    controller.setViewport(0, SEARCH_BLOCK_SIZE - 1);
    await initialLoad;
  }

  retry() {
    this.error = null;
    this.accessError = null;
    this.controller?.retryLoads();
  }
}

function abortError(): Error {
  const error = new Error("The test result block request was cancelled.");
  error.name = "AbortError";
  return error;
}

function accessErrorFor(status: number, auth: AuthStatus): SearchAccessError {
  if (auth === "unknown") return "sessionCheckFailed";
  return status === 403 && auth === "authenticated"
    ? "forbidden"
    : "requiresLogin";
}
