// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { TestResultSearchPageResponse } from "$lib/types/test-results-search-page";

export const DEFAULT_SEARCH_PAGE = 1;
export const DEFAULT_SEARCH_PAGE_SIZE = 50;
export const SEARCH_PAGE_SIZES = [25, 50, 100] as const;

export type SearchPageSize = (typeof SEARCH_PAGE_SIZES)[number];
export type SearchPageItem = number | "gap";

export interface SearchPageState {
  page: number;
  pageSize: SearchPageSize;
  problems: string[];
}

export interface SearchPageRange {
  start: number;
  end: number;
  count: number;
}

export function parseSearchPageState(
  params: Pick<URLSearchParams, "getAll">,
): SearchPageState {
  const problems: string[] = [];
  const pageValues = params.getAll("page");
  const sizeValues = params.getAll("page_size");
  let page = DEFAULT_SEARCH_PAGE;
  let pageSize: SearchPageSize = DEFAULT_SEARCH_PAGE_SIZE;

  if (pageValues.length > 1) {
    problems.push("Invalid page: provide at most one value.");
  } else if (pageValues.length === 1) {
    if (!/^[1-9]\d*$/.test(pageValues[0] ?? "")) {
      problems.push("Invalid page: expected a positive whole number.");
    } else {
      const parsed = Number(pageValues[0]);
      if (!Number.isSafeInteger(parsed)) {
        problems.push("Invalid page: expected a positive safe whole number.");
      } else {
        page = parsed;
      }
    }
  }

  if (sizeValues.length > 1) {
    problems.push("Invalid page_size: provide at most one value.");
  } else if (sizeValues.length === 1) {
    const value = sizeValues[0] ?? "";
    const parsed = Number(value);
    if (
      !/^(25|50|100)$/.test(value) ||
      !SEARCH_PAGE_SIZES.includes(parsed as SearchPageSize)
    ) {
      problems.push("Invalid page_size: choose 25, 50, or 100.");
    } else {
      pageSize = parsed as SearchPageSize;
    }
  }

  if (!Number.isSafeInteger((page - 1) * pageSize)) {
    problems.push(
      "Invalid page: its API offset is outside the safe integer range.",
    );
  }

  return { page, pageSize, problems };
}

/** Change only the 1-based page, retaining unrelated URL parameters. */
export function searchPageParams(
  source: URLSearchParams,
  page: number,
): URLSearchParams {
  if (!Number.isSafeInteger(page) || page < 1)
    throw new RangeError("Search page must be a positive safe whole number.");
  const params = new URLSearchParams(source);
  params.set("page", String(page));
  return params;
}

/** A page-size change resets to page one and preserves unrelated parameters. */
export function searchPageSizeParams(
  source: URLSearchParams,
  pageSize: number,
): URLSearchParams {
  if (!SEARCH_PAGE_SIZES.includes(pageSize as SearchPageSize))
    throw new RangeError("Search page size must be 25, 50, or 100.");
  const params = new URLSearchParams(source);
  params.set("page", String(DEFAULT_SEARCH_PAGE));
  params.set("page_size", String(pageSize));
  return params;
}

/** Build only the API paging parameters; URL extras are not filters. */
export function searchPageRequestParams(
  page: number,
  pageSize: number,
): URLSearchParams {
  if (!Number.isSafeInteger(page) || page < 1)
    throw new RangeError("Search page must be a positive safe whole number.");
  if (!SEARCH_PAGE_SIZES.includes(pageSize as SearchPageSize))
    throw new RangeError("Search page size must be 25, 50, or 100.");
  const offset = (page - 1) * pageSize;
  if (!Number.isSafeInteger(offset))
    throw new RangeError("Search page offset exceeds the safe integer range.");
  return new URLSearchParams({
    limit: String(pageSize),
    offset: String(offset),
    include_count: "true",
  });
}

export function hasValidSearchPageCount(
  response: TestResultSearchPageResponse | null,
): response is TestResultSearchPageResponse & { count: number } {
  return (
    response !== null &&
    typeof response.count === "number" &&
    Number.isSafeInteger(response.count) &&
    response.count >= 0
  );
}

/** Report the result range from server metadata and the returned rows. */
export function searchPageRange(
  response: TestResultSearchPageResponse,
): SearchPageRange {
  if (!hasValidSearchPageCount(response))
    throw new Error("The search page did not return its exact result count.");
  if (response.count === 0 || response.test_results.length === 0)
    return { start: 0, end: 0, count: response.count };
  return {
    start: response.offset + 1,
    end: Math.min(
      response.offset + response.test_results.length,
      response.count,
    ),
    count: response.count,
  };
}

export function searchTotalPages(count: number, pageSize: number): number {
  if (!Number.isSafeInteger(count) || count < 0)
    throw new Error("The search page did not return its exact result count.");
  if (!SEARCH_PAGE_SIZES.includes(pageSize as SearchPageSize))
    throw new RangeError("Search page size must be 25, 50, or 100.");
  return Math.ceil(count / pageSize);
}

/** An empty result set still has the canonical page-one URL. */
export function searchLastPage(count: number, pageSize: number): number {
  return Math.max(DEFAULT_SEARCH_PAGE, searchTotalPages(count, pageSize));
}

/** Build the compact page window with first/last links and ellipses. */
export function searchPageItems(
  currentPage: number,
  totalPages: number,
): SearchPageItem[] {
  if (!Number.isSafeInteger(totalPages) || totalPages < 0)
    throw new RangeError("Search page count must be a non-negative integer.");
  if (totalPages === 0) return [];
  if (!Number.isSafeInteger(currentPage) || currentPage < 1)
    throw new RangeError("Search page must be a positive whole number.");
  if (totalPages <= 7)
    return Array.from({ length: totalPages }, (_, index) => index + 1);

  const page = Math.min(currentPage, totalPages);
  const items: SearchPageItem[] = [1];
  const start = Math.max(2, page - 1);
  const end = Math.min(totalPages - 1, page + 1);
  if (start > 2) items.push("gap");
  for (let item = start; item <= end; item += 1) items.push(item);
  if (end < totalPages - 1) items.push("gap");
  items.push(totalPages);
  return items;
}

export function searchPageRangeLabel(range: SearchPageRange): string {
  return `Showing ${range.start}–${range.end} of ${range.count} results`;
}
