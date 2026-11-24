// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import { mount, unmount, flushSync } from "svelte";
import { SvelteMap } from "svelte/reactivity";
import ChangelogPage from "../src/lib/components/changelog/ChangelogPage.svelte";
import ChangelogDetailPage from "../src/lib/components/changelog/ChangelogDetailPage.svelte";

export { flushSync, unmount };
/** @param {Element} target */
export function mountPage(target) {
  return mount(ChangelogPage, {
    target,
    props: {
      family: {
        name: "items",
        api_name: "generic",
        friendly_name: "Items",
        stages: [],
        columns: [],
        filters: [],
      },
      artefactId: 3,
    },
  });
}

/** @param {Element} target @param {number | undefined} reviewId */
export function mountDetail(target, reviewId) {
  return mount(ChangelogDetailPage, {
    target,
    props: {
      family: {
        name: "items",
        api_name: "generic",
        friendly_name: "Items",
        stages: [],
        columns: [],
        filters: [],
      },
      artefactId: 3,
      reviewId,
      auditId: 12,
    },
  });
}

/** @param {Element} target */
export function mountReactiveDetail(target) {
  const state = new SvelteMap([["auditId", 12]]);
  const component = mount(ChangelogDetailPage, {
    target,
    props: {
      family: {
        name: "items",
        api_name: "generic",
        friendly_name: "Items",
        stages: [],
        columns: [],
        filters: [],
      },
      artefactId: 3,
      get auditId() {
        return state.get("auditId") ?? 12;
      },
    },
  });
  return {
    component,
    setAuditId: (/** @type {number} */ id) => state.set("auditId", id),
  };
}
