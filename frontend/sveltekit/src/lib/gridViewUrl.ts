// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

// Encodes the parts of a grid's view state that are worth sharing into a single
// URL parameter, so a dashboard link carries its own filtering and sorting.
// Keeping the state in the URL also scopes it to one family route: navigating
// between family dashboards lands on a different URL and therefore a clean grid.
//
// Also provides the storage behind SvGrid's autosaved view, which keeps the
// whole layout per family so leaving a dashboard and coming back restores what
// you were looking at.

import { isValuelessOperator } from "@svgrid/grid";
import type { SavedView, SvGridViewState, ViewStorage } from "@svgrid/grid";

/** Query parameter holding the encoded view. */
export const VIEW_PARAM = "view";

// The parameter arrives from a URL anyone can craft, so cap it before any
// decoding work is done on it. Comfortably above a realistic view: a dozen
// filters over this app's column names encode to a few hundred characters.
const MAX_ENCODED_LENGTH = 8192;

// Deliberately a subset of SvGridViewState: column widths, pinning, ordering
// and chart state are per-session presentation, not something a shared link
// should impose on the recipient. Ordering is also always populated, even
// untouched, which would make every view look non-default.
const SHARED_KEYS = [
  "sorting",
  "globalFilter",
  "columnFilters",
  "facetFilters",
  "hiddenColumns",
  "shownColumns",
] as const;

export type SharedGridView = Partial<
  Pick<
    SvGridViewState,
    "sorting" | "globalFilter" | "columnFilters" | "facetFilters"
  >
> & {
  // Visibility travels as a delta against the columns a family declares
  // hidden, so an untouched dashboard encodes to nothing while either
  // direction of override still survives a shared link.
  /** Columns hidden on top of the family's defaults. */
  hiddenColumns?: string[];
  /** Default-hidden columns the user has revealed. */
  shownColumns?: string[];
};

/**
 * The filtering and sorting a grid should be reset to when the user clears
 * filters. Column visibility is deliberately absent: clearing filters must not
 * reveal the columns a family declares hidden.
 */
export const EMPTY_VIEW: Partial<SvGridViewState> = {
  sorting: [],
  globalFilter: "",
  columnFilters: {},
  facetFilters: {},
};

function isEmptyValue(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === "object") return Object.keys(value).length === 0;
  return false;
}

// The grid keeps a filter entry around while its menu is open but empty, and a
// facet entry with nothing ticked. Those are not a customised view, so they are
// pruned before anything decides whether the view is shareable.
function normaliseView(view: SharedGridView): SharedGridView {
  const normalised = { ...view };
  if (normalised.columnFilters) {
    normalised.columnFilters = Object.fromEntries(
      Object.entries(normalised.columnFilters).filter(
        ([, f]) =>
          isValuelessOperator(f.operator) ||
          f.value !== "" ||
          (f.valueTo ?? "") !== "",
      ),
    );
  }
  if (normalised.facetFilters) {
    normalised.facetFilters = Object.fromEntries(
      Object.entries(normalised.facetFilters).filter(
        ([, values]) => values.length > 0,
      ),
    );
  }
  return normalised;
}

/** True when the view holds no filtering or sorting worth sharing. */
export function isDefaultView(view: SharedGridView): boolean {
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
export function encodeView(state: SharedGridView): string | null {
  const normalised = normaliseView(state);
  const view: SharedGridView = {};
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

function isRecordOf(
  value: unknown,
  entry: (v: unknown) => boolean,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    Object.values(value).every(entry)
  );
}

// The encoded value reaches us from a URL anyone may have hand-edited, so each
// key is shape-checked before it is handed to the grid rather than trusted.
const VALIDATORS: Record<
  (typeof SHARED_KEYS)[number],
  (v: unknown) => boolean
> = {
  sorting: (v) =>
    Array.isArray(v) &&
    v.every(
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as { id?: unknown }).id === "string" &&
        typeof (entry as { desc?: unknown }).desc === "boolean",
    ),
  globalFilter: (v) => typeof v === "string",
  // Mirrors SvGridViewState["columnFilters"], where the grid stores both bounds
  // of a filter as strings whatever the column's data type.
  columnFilters: (v) =>
    isRecordOf(
      v,
      (entry) =>
        typeof entry === "object" &&
        entry !== null &&
        typeof (entry as { operator?: unknown }).operator === "string" &&
        typeof (entry as { value?: unknown }).value === "string" &&
        ["string", "undefined"].includes(
          typeof (entry as { valueTo?: unknown }).valueTo,
        ),
    ),
  facetFilters: (v) => isRecordOf(v, isStringArray),
  hiddenColumns: isStringArray,
  shownColumns: isStringArray,
};

/**
 * Parses a `view` parameter back into grid state. Anything malformed is
 * dropped rather than thrown, so a mangled link still loads a usable grid.
 */
export function decodeView(encoded: string | null): SharedGridView | null {
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
  const view: SharedGridView = {};
  for (const key of SHARED_KEYS) {
    const value = (parsed as Record<string, unknown>)[key];
    if (value === undefined || isEmptyValue(value)) continue;
    if (!VALIDATORS[key](value)) continue;
    Object.assign(view, { [key]: value });
  }
  return isDefaultView(view) ? null : view;
}

function storageKey(family: string): string {
  return `test-observer-grid-view:${family}`;
}

/**
 * The state returned by `SvGridApi.getState()` includes effective column
 * widths, including values calculated by `fitColumns`. For fit-enabled grids,
 * autosave must instead persist only widths the user explicitly resized.
 * `onColumnResize` is the compatible public signal: it fires for user resize
 * gestures, but not for programmatic `setColumnWidth` calls.
 */
export function createUserResizeViewHost(host: {
  getState(): SvGridViewState;
  setState(state: Partial<SvGridViewState>): void;
}): {
  host: {
    getState(): SvGridViewState;
    setState(state: Partial<SvGridViewState>): void;
  };
  recordResize(columnId: string, width: number): void;
  resetResizes(): void;
} {
  let userWidths: Record<string, number> = {};

  return {
    host: {
      getState() {
        return { ...host.getState(), columnWidths: { ...userWidths } };
      },
      setState(state) {
        if (state.columnWidths !== undefined) {
          userWidths = { ...state.columnWidths };
        }
        host.setState(state);
      },
    },
    recordResize(columnId, width) {
      userWidths = { ...userWidths, [columnId]: width };
    },
    resetResizes() {
      userWidths = {};
    },
  };
}

/** Slot the autosaved layout occupies in a family's view store. */
export const AUTOSAVE_SLOT = "__autosave";

/**
 * Per-family storage for SvGrid's named-views manager. Holds the full layout —
 * column widths, order and visibility included — none of which belongs in a
 * shared link, hence a separate channel from the `view` parameter above.
 *
 * The versioned envelope distinguishes new sparse user-resize snapshots from
 * the old array format, whose `columnWidths` maps contained effective widths
 * for every column. Those legacy maps are discarded once during migration so
 * the grid can fit untouched columns to its current container again.
 *
 * sessionStorage rather than localStorage: a view is what you are working on
 * now, not a saved preference, so it should not still be filtering the
 * dashboard when the browser is reopened days later.
 */
const FAMILY_VIEW_STORAGE_VERSION = 2;

interface StoredViews {
  version: typeof FAMILY_VIEW_STORAGE_VERSION;
  views: SavedView[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readSavedViews(value: unknown): SavedView[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (view): view is SavedView =>
      isRecord(view) &&
      typeof view.name === "string" &&
      typeof view.createdAt === "number" &&
      isRecord(view.state),
  );
}

function stripLegacyWidths(view: SavedView): SavedView {
  const state = { ...view.state };
  delete state.columnWidths;
  return { ...view, state };
}

function encodeStoredViews(views: SavedView[]): StoredViews {
  return { version: FAMILY_VIEW_STORAGE_VERSION, views };
}

/**
 * Per-family storage for the autosaved view and its named-view manager.
 */
export function familyViewStorage(family: string): ViewStorage {
  const key = storageKey(family);
  return {
    read() {
      let raw: string | null;
      try {
        raw = sessionStorage.getItem(key);
      } catch {
        // Storage can be blocked outright by browser privacy settings.
        return [];
      }
      if (raw === null) return [];

      let parsed: unknown;
      try {
        parsed = JSON.parse(raw);
      } catch {
        return [];
      }

      if (
        isRecord(parsed) &&
        parsed.version === FAMILY_VIEW_STORAGE_VERSION &&
        Array.isArray(parsed.views)
      ) {
        return readSavedViews(parsed.views);
      }

      // Before version 2 the manager wrote a bare array, and getState() put
      // every effective fitColumns width into that array. Remove those widths
      // rather than restoring them as fixed overrides; other view state remains.
      if (Array.isArray(parsed)) {
        const migrated = readSavedViews(parsed).map(stripLegacyWidths);
        try {
          sessionStorage.setItem(
            key,
            JSON.stringify(encodeStoredViews(migrated)),
          );
        } catch {
          // The migrated snapshot is still safe to use for this mount.
        }
        return migrated;
      }
      return [];
    },
    write(views) {
      try {
        sessionStorage.setItem(key, JSON.stringify(encodeStoredViews(views)));
      } catch {
        // Without storage the view simply does not outlive the page; the URL
        // still carries the shareable part of it.
      }
    },
  };
}

/**
 * Per-session storage for the Search grid's autosaved layout. Its separate
 * namespace keeps Search widths independent from each family dashboard.
 */
function sparseWidths(value: unknown): Record<string, number> {
  if (!isRecord(value)) return {};
  const widths: Record<string, number> = {};
  for (const [columnId, width] of Object.entries(value)) {
    if (typeof width === "number" && Number.isFinite(width)) {
      widths[columnId] = width;
    }
  }
  return widths;
}

function searchSavedViews(views: SavedView[]): SavedView[] {
  return views.map((view) => ({
    ...view,
    // Search only persists widths; filters, visibility, ordering and other
    // grid state remain transient and are never restored from this store.
    state: { columnWidths: sparseWidths(view.state.columnWidths) },
  }));
}

export function searchGridViewStorage(): ViewStorage {
  const key = "test-observer-search-grid-view";
  return {
    read() {
      try {
        const raw = sessionStorage.getItem(key);
        if (raw === null) return [];
        return searchSavedViews(readSavedViews(JSON.parse(raw)));
      } catch {
        // Storage can be blocked outright by browser privacy settings.
        return [];
      }
    },
    write(views) {
      try {
        sessionStorage.setItem(key, JSON.stringify(searchSavedViews(views)));
      } catch {
        // The layout simply does not outlive the page when storage is blocked.
      }
    },
  };
}
