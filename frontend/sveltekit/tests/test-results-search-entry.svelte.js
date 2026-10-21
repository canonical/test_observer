// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount, flushSync } from "svelte";
import TestResultsSearch from "../src/lib/components/search/TestResultsSearch.svelte";
import ValueSuggestions from "../src/lib/components/search/ValueSuggestions.svelte";
import { replaceSearchView } from "../src/lib/searchViewNavigation";
export { TestResultsSearchStore } from "../src/lib/stores/test-results-search.svelte";
export {
  selectionQuery,
  TestResultsSelection,
} from "../src/lib/testResultsSelection.svelte";
export { userStore } from "../src/lib/stores/user.svelte";
export * from "../src/lib/testResultsSearch";
export * from "../src/lib/testResultsBulk";
export { replaceSearchView } from "../src/lib/searchViewNavigation";
export { encodeView, decodeView } from "../src/lib/gridViewUrl";
export { familyDisplayName } from "../src/lib/types";
export {
  SearchFilterLabelCache,
  searchFilterLabelCache,
} from "../src/lib/searchFilterLabels";
export { errorStore } from "../src/lib/stores/error.svelte";
export {
  lookupValues,
  suggestionScope,
  metadataSuggestions,
} from "../src/lib/searchFilterSuggestions";

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

/** Mount the actual lookup child to exercise a family-context change without
 * remounting the editor. The page normally changes family chips between opens.
 * @param {HTMLElement} target
 */
export function mountSuggestions(target) {
  let families = $state(["old-family"]);
  let selected = $state(["retained"]);
  const component = mount(ValueSuggestions, {
    target,
    props: {
      field: "artefacts",
      get draftFamilies() {
        return families;
      },
      get selected() {
        return selected;
      },
      set selected(value) {
        selected = value;
      },
    },
  });
  flushSync();
  return {
    /** @param {string[]} value */
    setFamilies(value) {
      families = value;
      flushSync();
    },
    get selected() {
      return [...selected];
    },
    destroy: () => unmount(component),
  };
}
