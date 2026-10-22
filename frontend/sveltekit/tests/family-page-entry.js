// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { flushSync, mount, unmount } from "svelte";
import FamilyPage from "../src/routes/[family]/+page.svelte";
import { page, setPageUrl } from "./family-page-state.svelte.js";
import { resetRetries, retryCount } from "./family-page-navigation.js";

/** @param {import("svelte").MountOptions["target"]} target @param {Record<string, any>} data */
export function mountFamilyPage(target, data) {
  const component = mount(FamilyPage, { target, props: { data } });
  flushSync();
  return component;
}

/** @param {Record<string, any>} component */
export function unmountFamilyPage(component) {
  return unmount(component);
}

export { flushSync, page, resetRetries, retryCount, setPageUrl };
