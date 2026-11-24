// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
import { mount, unmount, flushSync } from "svelte";
import ChangelogPage from "../src/lib/components/changelog/ChangelogPage.svelte";

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
