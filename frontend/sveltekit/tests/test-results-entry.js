// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import Page from "../src/routes/test-results/+page.svelte";
import { requests, resetApi, setHandler } from "./test-results-api.js";
import { pageProps } from "./test-results-runtime.svelte.js";

/**
 * @param {import("svelte").MountOptions["target"]} target
 * @param {import("../src/routes/test-results/$types").PageData} data
 */
export function mountPage(target, data) {
  pageProps.data = data;
  const component = mount(Page, {
    target,
    props: {
      get data() {
        return pageProps.data ?? data;
      },
      params: {},
    },
  });
  flushSync();
  return component;
}

export { flushSync, requests, resetApi, setHandler, unmount as unmountPage };

export {
  currentSearchUrl,
  invalidations,
  resetSearchUrl,
  searchHistoryBack,
  searchHistoryForward,
} from "./test-results-runtime.svelte.js";
export {
  DEFAULT_SEARCH_PAGE,
  DEFAULT_SEARCH_PAGE_SIZE,
  parseSearchPageState,
  searchLastPage,
  searchPageItems,
  searchPageParams,
  searchPageRange,
  searchPageRangeLabel,
  searchPageRequestParams,
  searchPageSizeParams,
  searchTotalPages,
} from "../src/lib/searchPagination.ts";

export {
  emptySearchFilters,
  parseSearchFilters,
  searchFilterRequestParams,
  searchFiltersEqual,
  serializeSearchFilters,
  validateSearchFilters,
  encodeMetadataPart,
} from "../src/lib/searchPageFilters.ts";
export { load as loadTestResultsPage } from "../src/routes/test-results/+page.ts";
export { searchRunPath } from "../src/lib/searchRunPath.ts";
