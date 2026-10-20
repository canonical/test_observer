// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount, flushSync } from "svelte";
import TestResultsSearch from "../src/lib/components/search/TestResultsSearch.svelte";
import { replaceSearchView } from "../src/lib/searchViewNavigation";
export { TestResultsSearchStore } from "../src/lib/stores/test-results-search.svelte";
export { userStore } from "../src/lib/stores/user.svelte";
export * from "../src/lib/testResultsSearch";
export { replaceSearchView } from "../src/lib/searchViewNavigation";
export { encodeView, decodeView } from "../src/lib/gridViewUrl";
export { familyDisplayName } from "../src/lib/types";

/**
 * @param {HTMLElement} target
 * @param {URL} initialUrl
 * @param {import('../src/lib/types').Family[]} families
 */
export function mountSearch(target, initialUrl, families) {
  let url = $state(initialUrl);
  const history = [initialUrl];
  const replacements = [];
  const component = mount(TestResultsSearch, {
    target,
    props: {
      get url() {
        return url;
      },
      families,
      base: "/custom/base",
      /** @param {URL} next */
      navigate(next) {
        history.push(next);
        url = next;
        return Promise.resolve();
      },
      /** @param {string | null} encoded @param {string} sourceHref */
      replaceView(encoded, sourceHref) {
        return replaceSearchView(encoded, sourceHref, {
          currentUrl: () => url,
          replace(next) {
            replacements.push(next);
            history[history.length - 1] = next;
            url = next;
            return Promise.resolve();
          },
        });
      },
    },
  });
  flushSync();
  return {
    history,
    replacements,
    get currentUrl() {
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
