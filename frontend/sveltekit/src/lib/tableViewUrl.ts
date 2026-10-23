// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

// Encodes the parts of the table's view state that are worth sharing into a
// single URL parameter, so a dashboard link carries its own filtering and
// sorting. Keeping the state in the URL also scopes it to one family route:
// navigating from /snaps to /debs lands on a different URL and therefore a
// clean table.
//
// Also provides the storage that keeps the column layout per family so leaving
// a dashboard and coming back restores what you were looking at.

import type { SortState, TableView } from "$lib/tableView";

/** Query parameter holding the encoded view. */
export const VIEW_PARAM = "view";

// The parameter arrives from a URL anyone can craft, so cap it before any
// decoding work is done on it.
const MAX_ENCODED_LENGTH = 8192;

export type SharedTableView = Partial<TableView> & {
  // Visibility travels as a delta against the columns a family declares
  // hidden, so an untouched dashboard encodes to nothing while either
  // direction of override still survives a shared link.
  /** Columns hidden on top of the family's defaults. */
  hiddenColumns?: string[];
  /** Default-hidden columns the user has revealed. */
  shownColumns?: string[];
};

const SHARED_KEYS = [
  "sorting",
  "globalFilter",
  "columnFilters",
  "hiddenColumns",
  "shownColumns",
] as const;

function isEmptyValue(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === "object") return Object.keys(value).length === 0;
  return false;
}

// A filter box that was opened and emptied again is not a customised view.
function normaliseView(view: SharedTableView): SharedTableView {
  const normalised = { ...view };
  if (normalised.columnFilters) {
    normalised.columnFilters = Object.fromEntries(
      Object.entries(normalised.columnFilters).filter(
        ([, value]) => value.trim() !== "",
      ),
    );
  }
  if (normalised.globalFilter?.trim() === "") delete normalised.globalFilter;
  return normalised;
}

/** True when the view holds no filtering or sorting worth sharing. */
export function isDefaultView(view: SharedTableView): boolean {
  const normalised = normaliseView(view);
  return SHARED_KEYS.every((key) => isEmptyValue(normalised[key]));
}

function toBase64Url(json: string): string {
  // btoa is latin1-only, so widen to bytes first to survive non-ASCII filters.
  const bytes = new TextEncoder().encode(json);
  // Chunked rather than concatenated byte by byte, which is quadratic, and
  // rather than spread in one go, which overflows the argument limit.
  const CHUNK_SIZE = 0x8000;
  const chunks: string[] = [];
  for (let i = 0; i < bytes.length; i += CHUNK_SIZE) {
    chunks.push(String.fromCharCode(...bytes.subarray(i, i + CHUNK_SIZE)));
  }
  return btoa(chunks.join(""))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function fromBase64Url(encoded: string): string {
  const padded = encoded
    .replace(/-/g, "+")
    .replace(/_/g, "/")
    .padEnd(Math.ceil(encoded.length / 4) * 4, "=");
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

/** Serialises a shared view into a URL-safe string, or null if it is default. */
export function encodeView(state: SharedTableView): string | null {
  const normalised = normaliseView(state);
  const view: SharedTableView = {};
  for (const key of SHARED_KEYS) {
    const value = normalised[key];
    if (!isEmptyValue(value)) {
      Object.assign(view, { [key]: value });
    }
  }
  if (isDefaultView(view)) return null;
  return toBase64Url(JSON.stringify(view));
}

function isStringArray(value: unknown): boolean {
  return Array.isArray(value) && value.every((v) => typeof v === "string");
}

function isSortState(value: unknown): value is SortState {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { id?: unknown }).id === "string" &&
    typeof (value as { desc?: unknown }).desc === "boolean"
  );
}

// The encoded value reaches us from a URL anyone may have hand-edited, so each
// key is shape-checked before it is used rather than trusted.
const VALIDATORS: Record<
  (typeof SHARED_KEYS)[number],
  (v: unknown) => boolean
> = {
  sorting: isSortState,
  globalFilter: (v) => typeof v === "string",
  columnFilters: (v) =>
    typeof v === "object" &&
    v !== null &&
    !Array.isArray(v) &&
    Object.values(v).every((entry) => typeof entry === "string"),
  hiddenColumns: isStringArray,
  shownColumns: isStringArray,
};

/**
 * Parses a `view` parameter back into table state. Anything malformed is
 * dropped rather than thrown, so a mangled link still loads a usable table.
 */
export function decodeView(encoded: string | null): SharedTableView | null {
  if (!encoded || encoded.length > MAX_ENCODED_LENGTH) return null;
  let parsed: unknown;
  try {
    parsed = JSON.parse(fromBase64Url(encoded));
  } catch {
    return null;
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return null;
  }
  const view: SharedTableView = {};
  for (const key of SHARED_KEYS) {
    const value = (parsed as Record<string, unknown>)[key];
    if (value === undefined || isEmptyValue(value)) continue;
    if (!VALIDATORS[key](value)) continue;
    Object.assign(view, { [key]: value });
  }
  return isDefaultView(view) ? null : view;
}

function storageKey(family: string): string {
  return `test-observer-table-view:${family}`;
}

/** Presentation state kept per tab, and kept out of shared links. */
export interface StoredLayout {
  hiddenColumns: string[];
}

/**
 * Reads the layout last used on a family's dashboard.
 *
 * sessionStorage rather than localStorage: a view is what you are working on
 * now, not a saved preference, so it should not still be applied when the
 * browser is reopened days later.
 */
export function loadLayout(family: string): StoredLayout | null {
  try {
    const raw = sessionStorage.getItem(storageKey(family));
    const parsed: unknown = raw === null ? null : JSON.parse(raw);
    const hidden = (parsed as { hiddenColumns?: unknown } | null)
      ?.hiddenColumns;
    return isStringArray(hidden) ? { hiddenColumns: hidden as string[] } : null;
  } catch {
    // Storage can be blocked outright by browser privacy settings.
    return null;
  }
}

export function saveLayout(family: string, layout: StoredLayout): void {
  try {
    sessionStorage.setItem(storageKey(family), JSON.stringify(layout));
  } catch {
    // Without storage the layout simply does not outlive the page.
  }
}
