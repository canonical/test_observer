// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import { SvelteURL } from "svelte/reactivity";
import SearchOptionPlaceholder from "../src/lib/components/search/SearchOptionPlaceholder.svelte";

export * from "../src/lib/searchOptionsPagination";
export { emptyFilters } from "../src/lib/testResultsSearch";

/** @param {HTMLElement} target @param {URL} initialUrl
 * @param {import("../src/lib/types").Family[]} families
 * @param {2 | 3 | 4} [option]
 */
export function mountSearchOption(target, initialUrl, families, option = 2) {
  let url = $state(initialUrl);
  const navigations = [];
  const component = mount(SearchOptionPlaceholder, {
    target,
    props: {
      option,
      get url() {
        return url;
      },
      routePath: `/custom/base/test-results/option-${option}`,
      families,
      /** @param {string | URL} next */
      navigate(next) {
        const nextUrl = new SvelteURL(next, url.origin);
        navigations.push(nextUrl);
        url = nextUrl;
        return Promise.resolve();
      },
    },
  });
  flushSync();
  return {
    navigations,
    get url() {
      return url;
    },
    /** @param {URL} next */
    restore(next) {
      url = next;
      flushSync();
    },
    destroy: () => unmount(component),
  };
}
