// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { SvelteSet, SvelteURL } from "svelte/reactivity";
import { onMount } from "svelte";

// Only mock SvelteKit's public state contract. Routing/race behavior belongs to
// SvelteKit and must be checked with the real router in a browser.
/** @typedef {{ from: { url: URL } | null; to: { url: URL } | null; type: string | null; complete: Promise<void> | null }} NavigationState */
/** @type {NavigationState} */
export const navigating = $state({
  from: null,
  to: null,
  type: null,
  complete: null,
});
/** @type {{ url: URL; shallow: { url: URL } | null }} */
export const page = $state({
  url: new SvelteURL("http://localhost/alpha"),
  shallow: null,
});

/** @type {Set<(navigation: NavigationState & { shallow: boolean }) => void>} */
const beforeCallbacks = new SvelteSet();
/** @param {(navigation: NavigationState & { shallow: boolean }) => void} callback */
export function beforeNavigate(callback) {
  onMount(() => {
    beforeCallbacks.add(callback);
    return () => beforeCallbacks.delete(callback);
  });
}
/** @param {NavigationState & { shallow: boolean }} navigation */
export function notifyBeforeNavigation(navigation) {
  for (const callback of beforeCallbacks) callback(navigation);
}
