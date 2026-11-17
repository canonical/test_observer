// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import Page from "../src/routes/test-results/+page.svelte";
import { requests, resetApi, setHandler } from "./test-results-api.js";

/** @param {import("svelte").MountOptions["target"]} target */
export function mountPage(target) {
  const component = mount(Page, { target });
  flushSync();
  return component;
}

export { flushSync, requests, resetApi, setHandler, unmount as unmountPage };
