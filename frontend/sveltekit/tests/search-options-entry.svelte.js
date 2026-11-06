// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import { SvelteURL } from "svelte/reactivity";
import SearchOption2 from "../src/lib/components/search/SearchOption2.svelte";
import SearchOption3 from "../src/lib/components/search/SearchOption3.svelte";
import SearchOption4 from "../src/lib/components/search/SearchOption4.svelte";

export * from "../src/lib/searchOptionsPagination";
export { emptyFilters } from "../src/lib/testResultsSearch";
export { userStore } from "../src/lib/stores/user.svelte";

/** @param {HTMLElement} target @param {URL} initialUrl
 * @param {import("../src/lib/types").Family[]} families
 * @param {2 | 2.5 | 3 | 4} [option]
 */
export function mountSearchOption(target, initialUrl, families, option = 2) {
  let url = $state(initialUrl);
  const navigations = [];
  const component = mount(
    option === 2 || option === 2.5
      ? SearchOption2
      : option === 3
        ? SearchOption3
        : SearchOption4,
    {
      target,
      props: {
        get url() {
          return url;
        },
        routePath: `/custom/base/test-results/option-${option === 2.5 ? "2-5" : option}`,
        variant: option === 2.5 ? 2.5 : undefined,
        families,
        base: "/custom/base",
        /** @param {string | URL} next */
        navigate(next) {
          const nextUrl = new SvelteURL(next, url.origin);
          navigations.push(nextUrl);
          url = nextUrl;
          return Promise.resolve();
        },
      },
    },
  );
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
