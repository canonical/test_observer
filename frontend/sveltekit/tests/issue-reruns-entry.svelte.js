// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount, flushSync } from "svelte";
import IssueTestResults from "../src/lib/components/issues/IssueTestResults.svelte";
import BulkRerunReview from "../src/lib/components/search/BulkRerunReview.svelte";
export * from "../src/lib/issueTestResults";
export { rerunPlan } from "../src/lib/testResultsBulk";
export { userStore } from "../src/lib/stores/user.svelte";

/** @param {HTMLElement} target */
export function mountResults(target) {
  const props = $state({ issueId: 73, families: [], base: "/wip" });
  const component = mount(IssueTestResults, { target, props });
  flushSync();
  return {
    changeIssue: (/** @type {number} */ id) => {
      props.issueId = id;
      flushSync();
    },
    destroy: () => unmount(component),
  };
}

/** Default-consumer regression: explicit selections remain opt-in exact groups.
 * @param {HTMLElement} target
 * @param {import('../src/lib/testResultsBulk').BulkTarget} value */
export function mountReview(target, value) {
  const component = mount(BulkRerunReview, {
    target,
    props: {
      scope: () => ({ ok: true, value }),
      reviewKey: "default-consumer",
      loginUrl: "/login",
      onbusy: () => undefined,
      onreview: () => undefined,
      oncomplete: () => Promise.resolve(),
      onrefresh: () => Promise.resolve(),
      onclose: () => undefined,
    },
  });
  flushSync();
  return {
    // Svelte's exported instance methods are untyped in this JS test build.
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    start: component.start,
    destroy: () => unmount(component),
  };
}
