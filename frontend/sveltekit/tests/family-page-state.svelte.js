// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { SvelteURL } from "svelte/reactivity";

export const page = $state({
  url: new SvelteURL("http://localhost/snaps"),
});

/** @param {string} path */
export function setPageUrl(path) {
  page.url = new SvelteURL(path, "http://localhost");
}
