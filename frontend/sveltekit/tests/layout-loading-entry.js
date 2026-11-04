// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { createRawSnippet, flushSync, mount, unmount } from "svelte";
import { SvelteURL } from "svelte/reactivity";
import Layout from "../src/routes/+layout.svelte";
import {
  navigating,
  page,
  notifyBeforeNavigation,
} from "./layout-loading-state.svelte.js";
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

/** @param {string | null} pathname @param {{ type?: string; notify?: boolean; shallow?: boolean }} [options] */
export function setDestination(
  pathname,
  { type = "goto", notify = true, shallow = false } = {},
) {
  const navigation = {
    from: pathname ? { url: page.url } : null,
    to: pathname ? { url: new URL(pathname, "http://localhost") } : null,
    type: pathname ? type : null,
    complete: pathname ? Promise.resolve() : null,
  };
  // The hook receives shallow, but the installed public navigating export does
  // not expose it. Do not copy the hook's extra field into the state fixture.
  if (pathname && notify) notifyBeforeNavigation({ ...navigation, shallow });
  Object.assign(navigating, navigation);
  flushSync();
}

/** @param {string} loaded @param {string | null} [visible] */
export function setPageUrl(loaded, visible = null) {
  page.url = new SvelteURL(loaded, "http://localhost");
  page.shallow = visible
    ? { url: new SvelteURL(visible, "http://localhost") }
    : null;
  flushSync();
}

/** @param {string} message */
export function showError(message) {
  errorStore.set(message);
  flushSync();
}

export { unmount as unmountLayout, flushSync };
