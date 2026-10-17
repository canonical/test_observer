// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { createRawSnippet, flushSync, mount, unmount } from "svelte";
import Layout from "../src/routes/+layout.svelte";
import { navigating } from "./layout-loading-state.svelte.js";
import { errorStore } from "../src/lib/stores/error.svelte";

/** @param {import("svelte").MountOptions["target"]} target */
export function mountLayout(target) {
  const component = mount(Layout, {
    target,
    props: {
      data: { artefactFamilies: [{ name: "alpha" }, { name: "beta" }] },
      children: createRawSnippet(() => ({
        render: () => '<button id="page-action">Page action</button>',
      })),
    },
  });
  flushSync();
  return component;
}

/** @param {string | null} pathname */
export function setDestination(pathname) {
  navigating.to = pathname
    ? { url: new URL(pathname, "http://localhost") }
    : null;
  flushSync();
}

/** @param {string} message */
export function showError(message) {
  errorStore.set(message);
  flushSync();
}

export { unmount as unmountLayout, flushSync };
