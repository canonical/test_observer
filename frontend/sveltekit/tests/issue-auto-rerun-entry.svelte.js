// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { mount, unmount } from "svelte";
import IssueAutoRerun from "../src/lib/components/issues/IssueAutoRerun.svelte";
export * from "../src/lib/issueAutoRerunUpdates";
export * from "../src/lib/api/issues";
export { userStore } from "../src/lib/stores/user.svelte";
export { refreshBulkPermissions } from "../src/lib/testResultsBulkPermissions";

/** @param {HTMLElement} target @param {number} issueId @param {boolean} enabled */
export function mountSetting(target, issueId, enabled) {
  const props = $state({ issueId, enabled });
  const component = mount(IssueAutoRerun, { target, props });
  return {
    update: (/** @type {Partial<typeof props>} */ next) => {
      Object.assign(props, next);
    },
    destroy: () => unmount(component),
  };
}
