// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { createRawSnippet, flushSync, mount, unmount } from "svelte";
import Layout from "../src/routes/+layout.svelte";
import { navigating } from "./layout-loading-state.svelte.js";
import { errorStore } from "../src/lib/stores/error.svelte";

/**
 * @param {import("svelte").MountOptions["target"]} target
 * @param {string} [content]
 */
export function mountLayout(
  target,
  content = '<button id="page-action">Page action</button>',
) {
  const component = mount(Layout, {
    target,
    props: {
      data: {
        artefactFamilies: [{ name: "alpha" }, { name: "beta" }],
        artefactFamiliesUnauthorized: false,
      },
      children: createRawSnippet(() => ({
        render: () => content,
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
export { load as loadLayout } from "../src/routes/+layout";
export { load as loadRoot } from "../src/routes/+page";
export { load as loadFamily } from "../src/routes/family/[family]/+page";
export { load as loadArtefact } from "../src/routes/family/[family]/[artefactId]/+page";
