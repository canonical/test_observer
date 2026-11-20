// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { SvelteURL } from "svelte/reactivity";

let entries = [new SvelteURL("http://localhost/test-results")];
let index = 0;

export const page = $state({ url: entries[0] });

export function testResolve(path = "") {
  const base = "/custom/base";
  return path ? `${base}/${path}` : `${base}/`;
}

/**
 * @param {string | URL} target
 * @param {{ replace?: boolean }} [options]
 */
export function testGoto(target, options = {}) {
  const next = new SvelteURL(target, page.url);
  if (options.replace) {
    entries[index] = next;
  } else {
    entries = [...entries.slice(0, index + 1), next];
    index += 1;
  }
  page.url = next;
  return Promise.resolve();
}

export function resetSearchUrl(target = "http://localhost/test-results") {
  const next = new SvelteURL(target, page.url);
  entries = [next];
  index = 0;
  page.url = next;
}

export function searchHistoryBack() {
  if (index > 0) {
    index -= 1;
    page.url = entries[index];
  }
}

export function searchHistoryForward() {
  if (index < entries.length - 1) {
    index += 1;
    page.url = entries[index];
  }
}

export function currentSearchUrl() {
  return page.url.href;
}
