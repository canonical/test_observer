// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import ArtefactTable from "../src/lib/components/dashboard/ArtefactTable.svelte";

/** @param {import("svelte").MountOptions["target"]} target
 * @param {string} family
 */
export function mountTable(target, family) {
  const component = mount(ArtefactTable, {
    target,
    props: { family: { name: family }, artefacts: [] },
  });
  flushSync();
  return component;
}

export { flushSync, unmount };
