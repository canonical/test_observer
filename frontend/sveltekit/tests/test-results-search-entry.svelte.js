// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount, flushSync } from "svelte";
import TestResultsSearch from "../src/lib/components/search/TestResultsSearch.svelte";
import ValueSuggestions from "../src/lib/components/search/ValueSuggestions.svelte";
import CreateAttachmentRule from "../src/lib/components/search/CreateAttachmentRule.svelte";
import { attachmentRuleFilters } from "../src/lib/testResultsBulk";
import { parseSearch } from "../src/lib/testResultsSearch";
import { replaceSearchView } from "../src/lib/searchViewNavigation";
export { TestResultsSearchStore } from "../src/lib/stores/test-results-search.svelte";
export {
  selectionQuery,
  TestResultsSelection,
} from "../src/lib/testResultsSelection.svelte";
export { userStore } from "../src/lib/stores/user.svelte";
export * from "../src/lib/testResultsSearch";
export * from "../src/lib/testResultsBulk";
export * from "../src/lib/testResultsIssues";
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
  const busyChanges = [];
  const component = mount(TestResultsSearch, {
    target,
    props: {
      get url() {
        return url;
      },
      families,
      base: "/custom/base",
      onBusyChange(value) {
        busyChanges.push(value);
      },
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
    busyChanges,
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

/** Mount the actual query-rule action with reactive readiness. This exercises
 * transient readiness revocation at each await without bypassing disabled page
 * controls or adding a production test hook.
 * @param {HTMLElement} target
 * @param {import('../src/lib/types').Family[]} families
 */
export function mountRule(target, families) {
  let readiness = $state({
    available: true,
    loading: false,
    moving: false,
    accessError: false,
    unapplied: false,
    mutating: false,
  });
  // eslint-disable-next-line svelte/prefer-svelte-reactivity -- Immutable parse input, not component state.
  const applied = parseSearch(new URLSearchParams("artefacts=one"), families);
  const messages = [];
  const busyChanges = [];
  const component = mount(CreateAttachmentRule, {
    target,
    props: {
      scope: () => attachmentRuleFilters(applied, readiness),
      reviewKey: "frozen-rule-source",
      origin: "https://observer.example",
      base: "/custom/base",
      loginUrl: "/login",
      blocked: false,
      beforeOpen() {
        /* No page editor in the standalone fixture. */
      },
      onbusy(value) {
        busyChanges.push(value);
      },
      onreview() {
        /* Native modal state is asserted from the DOM. */
      },
      oncomplete(message) {
        messages.push(message);
      },
    },
  });
  flushSync();
  return {
    messages,
    busyChanges,
    /** @param {keyof typeof readiness} key @param {boolean} value */
    setReadiness(key, value) {
      readiness[key] = value;
      flushSync();
    },
    destroy: () => unmount(component),
  };
}
