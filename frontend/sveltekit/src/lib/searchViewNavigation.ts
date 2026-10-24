// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { VIEW_PARAM } from "$lib/gridViewUrl";

/** A presentation-only history adapter, separate from backend navigation.
 * Read the live route at the point of writing: an outgoing grid must not
 * replace a newer query, restored history entry, or another route's URL.
 */
export async function replaceSearchView(
  encoded: string | null,
  sourceHref: string,
  history: {
    currentUrl: () => URL | null;
    replace: (url: URL) => Promise<unknown>;
  },
): Promise<void> {
  const current = history.currentUrl();
  if (current?.href !== sourceHref) return;
  const next = new URL(current);
  if (encoded === null) next.searchParams.delete(VIEW_PARAM);
  else next.searchParams.set(VIEW_PARAM, encoded);
  if (next.href !== current.href) await history.replace(next);
}
