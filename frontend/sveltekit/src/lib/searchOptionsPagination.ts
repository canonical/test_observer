// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { silentApi } from "$lib/api/client";
import type { Family } from "$lib/types";
import type { AuthStatus } from "$lib/stores/user.svelte";
import {
  parseSearchPage,
  searchFilterParams,
  type AppliedSearch,
  type SearchFilters,
  type SearchTableResponse,
} from "$lib/testResultsSearch";

export const DEFAULT_SEARCH_PAGE = 1;
export const DEFAULT_SEARCH_PAGE_SIZE = 50;
export const SEARCH_PAGE_SIZES = [25, 50, 100] as const;

export interface SearchPageState {
  page: number;
  pageSize: (typeof SEARCH_PAGE_SIZES)[number];
  problems: string[];
}

export interface PaginatedSearch extends AppliedSearch {
  page: number;
  pageSize: (typeof SEARCH_PAGE_SIZES)[number];
}

export interface SearchPageRange {
  start: number;
  end: number;
  count: number;
}

export type SearchOptionsPageItem = number | "gap";

export type SearchOptionsAccessError =
  "requiresLogin" | "forbidden" | "sessionCheckFailed";

/** Use the same authoritative /me revalidation result as Option 1. */
export function searchOptionsAccessErrorFor(
  status: number,
  auth: AuthStatus,
): SearchOptionsAccessError {
  if (auth === "unknown") return "sessionCheckFailed";
  return status === 403 && auth === "authenticated"
    ? "forbidden"
    : "requiresLogin";
}

export function parseSearchPageState(params: URLSearchParams): SearchPageState {
  const problems: string[] = [];
  const pageValues = params.getAll("page");
  const sizeValues = params.getAll("page_size");
  let page = DEFAULT_SEARCH_PAGE;
  let pageSize: SearchPageState["pageSize"] = DEFAULT_SEARCH_PAGE_SIZE;

  if (pageValues.length > 1) {
    problems.push("Invalid page: provide at most one value.");
  } else if (pageValues.length === 1) {
    if (!/^[1-9]\d*$/.test(pageValues[0])) {
      problems.push("Invalid page: expected a positive whole number.");
    } else {
      const parsed = Number(pageValues[0]);
      if (!Number.isSafeInteger(parsed)) {
        problems.push("Invalid page: expected a positive whole number.");
      } else {
        page = parsed;
      }
    }
  }

  if (sizeValues.length > 1) {
    problems.push("Invalid page_size: provide at most one value.");
  } else if (sizeValues.length === 1) {
    const parsed = Number(sizeValues[0]);
    if (
      !/^(25|50|100)$/.test(sizeValues[0]) ||
      !SEARCH_PAGE_SIZES.includes(parsed as SearchPageState["pageSize"])
    ) {
      problems.push("Invalid page_size: choose 25, 50, or 100.");
    } else {
      pageSize = parsed as SearchPageState["pageSize"];
    }
  }

  if (!Number.isSafeInteger((page - 1) * pageSize)) {
    problems.push(
      "Invalid page: its API offset is outside the safe integer range.",
    );
  }

  return { page, pageSize, problems };
}

/**
 * Parse presentation state separately, leaving the canonical filter model
 * untouched.
 */
export function parseSearchOptions(
  params: URLSearchParams,
  families: Family[],
): PaginatedSearch {
  const pageState = parseSearchPageState(params);
  const filterParams = new URLSearchParams(params);
  filterParams.delete("page");
  filterParams.delete("page_size");
  const search = parseSearchPage(filterParams, families);
  return {
    ...search,
    page: pageState.page,
    pageSize: pageState.pageSize,
    problems: [...pageState.problems, ...search.problems],
  };
}

/** Change only the 1-based page; filters and page size remain shareable. */
export function searchOptionsPageParams(
  source: URLSearchParams,
  page: number,
): URLSearchParams {
  if (!Number.isSafeInteger(page) || page < 1)
    throw new RangeError("Search page must be a positive whole number.");
  const params = new URLSearchParams(source);
  params.set("page", String(page));
  return params;
}

/**
 * A page-size change starts at page one and preserves every filter parameter.
 */
export function searchOptionsPageSizeParams(
  source: URLSearchParams,
  pageSize: number,
): URLSearchParams {
  if (!SEARCH_PAGE_SIZES.includes(pageSize as SearchPageState["pageSize"]))
    throw new RangeError("Search page size must be 25, 50, or 100.");
  const params = new URLSearchParams(source);
  params.set("page", String(DEFAULT_SEARCH_PAGE));
  params.set("page_size", String(pageSize));
  return params;
}

/**
 * Reset presentation paging after a future filter edit, retaining page_size.
 */
export function resetSearchOptionsPage(
  source: URLSearchParams,
): URLSearchParams {
  const params = new URLSearchParams(source);
  params.set("page", String(DEFAULT_SEARCH_PAGE));
  return params;
}

/**
 * All canonical filters are serialized by the shared Search filter contract.
 */
export function searchOptionsPageRequestParams(
  filters: SearchFilters,
  page: number,
  pageSize: number,
): URLSearchParams {
  if (!Number.isSafeInteger(page) || page < 1)
    throw new RangeError("Search page must be a positive whole number.");
  if (!SEARCH_PAGE_SIZES.includes(pageSize as SearchPageState["pageSize"]))
    throw new RangeError("Search page size must be 25, 50, or 100.");
  const offset = (page - 1) * pageSize;
  if (!Number.isSafeInteger(offset))
    throw new RangeError("Search page offset exceeds the safe integer range.");
  const params = searchFilterParams(filters);
  params.set("offset", String(offset));
  params.set("limit", String(pageSize));
  // Page-based options need the exact server total on every navigation.
  params.set("include_count", "true");
  return params;
}

export type SearchPageApiRequest = <T>(
  path: string,
  options?: RequestInit,
) => Promise<T | null>;

/**
 * Fetch one API-backed page without locally filtering or reordering its rows.
 */
export async function loadSearchOptionsPage(
  filters: SearchFilters,
  page: number,
  pageSize: number,
  options: {
    signal?: AbortSignal;
    request?: SearchPageApiRequest;
  } = {},
): Promise<SearchTableResponse> {
  const params = searchOptionsPageRequestParams(filters, page, pageSize);
  const request = options.request ?? silentApi;
  const response = await request<SearchTableResponse>(
    `test-results/search-page?${params}`,
    { signal: options.signal },
  );
  if (
    !response ||
    typeof response.count !== "number" ||
    !Number.isSafeInteger(response.count) ||
    response.count < 0
  ) {
    throw new Error("The search page did not return its exact result count.");
  }
  return response;
}

/** Report the range from the server response, including short final pages. */
export function searchOptionsPageRange(
  response: SearchTableResponse,
): SearchPageRange {
  const count = response.count;
  if (typeof count !== "number" || !Number.isSafeInteger(count) || count < 0)
    throw new Error("The search page did not return its exact result count.");
  if (!response.rows.length || !count) return { start: 0, end: 0, count };
  return {
    start: response.offset + 1,
    end: Math.min(response.offset + response.rows.length, count),
    count,
  };
}

/** Derive the number of pages only from the exact server count. */
export function searchOptionsTotalPages(
  count: number,
  pageSize: number,
): number {
  if (!Number.isSafeInteger(count) || count < 0)
    throw new Error("The search page did not return its exact result count.");
  if (!SEARCH_PAGE_SIZES.includes(pageSize as SearchPageState["pageSize"]))
    throw new RangeError("Search page size must be 25, 50, or 100.");
  return Math.ceil(count / pageSize);
}

/**
 * Count zero has no result pages, but page one remains its canonical URL so the
 * empty result state can retain the ordinary page-size and filter controls.
 */
export function searchOptionsLastPage(count: number, pageSize: number): number {
  return Math.max(
    DEFAULT_SEARCH_PAGE,
    searchOptionsTotalPages(count, pageSize),
  );
}

/** Build the historical compact page window, including gaps for skipped pages. */
export function searchOptionsPageItems(
  currentPage: number,
  totalPages: number,
): SearchOptionsPageItem[] {
  if (!Number.isSafeInteger(totalPages) || totalPages < 0)
    throw new RangeError("Search page count must be a non-negative integer.");
  if (totalPages === 0) return [];
  if (!Number.isSafeInteger(currentPage) || currentPage < 1)
    throw new RangeError("Search page must be a positive whole number.");

  if (totalPages <= 7)
    return Array.from({ length: totalPages }, (_, index) => index + 1);

  const page = Math.min(currentPage, totalPages);
  const items: SearchOptionsPageItem[] = [1];
  const start = Math.max(2, page - 1);
  const end = Math.min(totalPages - 1, page + 1);
  if (start > 2) items.push("gap");
  for (let item = start; item <= end; item += 1) items.push(item);
  if (end < totalPages - 1) items.push("gap");
  items.push(totalPages);
  return items;
}

/** Provide a clear live range string for both populated and empty results. */
export function searchOptionsPageRangeLabel(range: SearchPageRange): string {
  if (range.count === 0) return "Showing 0–0 of 0 results";
  if (range.start === 0)
    return `No results on this page (${range.count} total)`;
  return `Showing ${range.start}–${range.end} of ${range.count} results`;
}
