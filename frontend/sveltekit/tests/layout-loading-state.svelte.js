// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { SvelteURL } from "svelte/reactivity";

// Only mock SvelteKit's public state contract. Routing/race behavior belongs to
// SvelteKit and must be checked with the real router in a browser.
/** @type {{ to: { url: URL } | null }} */
export const navigating = $state({ to: null });
export const page = { url: new SvelteURL("http://localhost/alpha") };
