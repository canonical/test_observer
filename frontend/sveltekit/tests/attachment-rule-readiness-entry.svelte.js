// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import CreateAttachmentRule from "../src/lib/components/search/CreateAttachmentRule.svelte";
import { attachmentRuleFilters } from "../src/lib/testResultsBulk";
import { parseSearch } from "../src/lib/testResultsSearch";

/**
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
        // This fixture mounts the reusable rule action without the Search route.
      },
      onbusy(value) {
        busyChanges.push(value);
      },
      onreview() {
        // Native modal state is asserted from the DOM.
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
