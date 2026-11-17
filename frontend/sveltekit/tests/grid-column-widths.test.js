// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { after, before, test } from "node:test";
import { createServer } from "vite";

/** @type {import("vite").ViteDevServer | undefined} */
let vite;
/** @type {typeof import("../src/lib/gridViewUrl").createUserResizeViewHost | undefined} */
let createUserResizeViewHost;
/** @type {typeof import("../src/lib/gridViewUrl").familyViewStorage | undefined} */
let familyViewStorage;
/** @type {typeof import("../src/lib/gridViewUrl").encodeView | undefined} */
let encodeView;
/** @type {typeof import("../src/lib/gridViewUrl").AUTOSAVE_SLOT | undefined} */
let autosaveSlot;
/** @type {typeof import("@svgrid/grid").createNamedViews | undefined} */
let createNamedViews;
/** @type {typeof import("@svgrid/grid").attachAutoSavedView | undefined} */
let attachAutoSavedView;

before(async () => {
  vite = await createServer({
    configFile: "vite.config.ts",
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({ createUserResizeViewHost, familyViewStorage, encodeView } =
    await vite.ssrLoadModule("/src/lib/gridViewUrl.ts"));
  ({ AUTOSAVE_SLOT: autosaveSlot } = await vite.ssrLoadModule(
    "/src/lib/gridViewUrl.ts",
  ));
  ({ createNamedViews, attachAutoSavedView } =
    await vite.ssrLoadModule("@svgrid/grid"));
});

after(async () => {
  await vite?.close();
});

void test("fitColumns autosave stores only user overrides and migrates legacy widths", async () => {
  if (
    !createUserResizeViewHost ||
    !familyViewStorage ||
    !autosaveSlot ||
    !createNamedViews ||
    !attachAutoSavedView
  ) {
    throw new Error("Grid view helpers were not loaded");
  }

  const originalSessionStorage = Object.getOwnPropertyDescriptor(
    globalThis,
    "sessionStorage",
  );
  const sessionStorage = new MemorySessionStorage();
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    value: sessionStorage,
  });

  try {
    // A fitted grid reports effective widths from its raw API, but the autosave
    // host starts with no explicit overrides, so a fresh view stays fitted.
    const first = createFittingGrid(900);
    const firstWidthHost = createUserResizeViewHost(first.api);
    const firstViews = createNamedViews(firstWidthHost.host, {
      storage: familyViewStorage("snaps"),
    });
    assert.deepEqual(first.api.getState().columnWidths, {
      name: 300,
      status: 300,
      updated: 300,
    });
    firstViews.save(autosaveSlot);
    assert.deepEqual(
      firstViews.list()[0]?.state.columnWidths,
      {},
      "fresh autosave must not persist fitted effective widths",
    );

    // The public onColumnResize callback is the durable signal for a user drag.
    first.resizeUserColumn("name", 240);
    firstWidthHost.recordResize("name", 240);
    firstViews.save(autosaveSlot);
    assert.deepEqual(firstViews.list()[0]?.state.columnWidths, { name: 240 });

    // Reload into a wider container: only the dragged column is fixed, and the
    // untouched columns divide the remaining available width.
    const restored = createFittingGrid(1200);
    const restoredWidthHost = createUserResizeViewHost(restored.api);
    const restoredViews = createNamedViews(restoredWidthHost.host, {
      storage: familyViewStorage("snaps"),
    });
    assert.equal(restoredViews.load(autosaveSlot), true);
    assert.deepEqual(restored.api.getState().columnWidths, {
      name: 240,
      status: 480,
      updated: 480,
    });

    // Later container changes re-fit untouched columns without overriding the
    // user's explicit width.
    restored.setContainerWidth(1500);
    assert.deepEqual(restored.api.getState().columnWidths, {
      name: 240,
      status: 630,
      updated: 630,
    });

    // The built-in "Reset columns" menu action clears SvGrid's explicit
    // widths without firing onColumnResize. Clear the autosave-side override
    // map as well, then verify the reloaded grid fits the current container.
    const detachAutosave = attachAutoSavedView(
      restoredWidthHost.host,
      restoredViews,
      { skipRestore: true, intervalMs: 100 },
    );
    try {
      restored.resetColumns();
      restoredWidthHost.resetResizes();
      await new Promise((resolve) => setTimeout(resolve, 125));
    } finally {
      detachAutosave();
    }
    assert.deepEqual(restoredViews.list()[0]?.state.columnWidths, {});

    const resetReload = createFittingGrid(1500);
    const resetWidthHost = createUserResizeViewHost(resetReload.api);
    const resetViews = createNamedViews(resetWidthHost.host, {
      storage: familyViewStorage("snaps"),
    });
    assert.equal(resetViews.load(autosaveSlot), true);
    assert.deepEqual(resetReload.api.getState().columnWidths, {
      name: 500,
      status: 500,
      updated: 500,
    });

    // An old bare-array snapshot has full effective width maps. Migration
    // preserves its filter state but drops widths and immediately rewrites the
    // storage into the versioned format.
    sessionStorage.setItem(
      "test-observer-grid-view:debs",
      JSON.stringify([
        {
          name: autosaveSlot,
          createdAt: 1,
          state: {
            globalFilter: "legacy filter",
            columnWidths: { name: 300, status: 300, updated: 300 },
          },
        },
      ]),
    );
    const legacy = createFittingGrid(1500);
    const legacyWidthHost = createUserResizeViewHost(legacy.api);
    const legacyViews = createNamedViews(legacyWidthHost.host, {
      storage: familyViewStorage("debs"),
    });
    assert.equal(legacyViews.load(autosaveSlot), true);
    assert.equal(legacy.api.getState().globalFilter, "legacy filter");
    assert.deepEqual(legacy.api.getState().columnWidths, {
      name: 500,
      status: 500,
      updated: 500,
    });
    const migratedSnapshot = sessionStorage.getItem(
      "test-observer-grid-view:debs",
    );
    assert.ok(migratedSnapshot);
    const migrated = /** @type {unknown} */ (JSON.parse(migratedSnapshot));
    assert.ok(isRecord(migrated));
    assert.equal(migrated.version, 2);
    assert.ok(Array.isArray(migrated.views));
    const migratedView = /** @type {unknown} */ (migrated.views[0]);
    assert.ok(isRecord(migratedView));
    assert.ok(isRecord(migratedView.state));
    assert.equal("columnWidths" in migratedView.state, false);

    // Widths remain outside shareable URL state.
    const shareStateWithWidth =
      /** @type {import("../src/lib/gridViewUrl").SharedGridView & { columnWidths: Record<string, number> }} */ ({
        columnWidths: { name: 240 },
      });
    assert.equal(encodeView?.(shareStateWithWidth), null);
  } finally {
    if (originalSessionStorage) {
      Object.defineProperty(
        globalThis,
        "sessionStorage",
        originalSessionStorage,
      );
    } else {
      Reflect.deleteProperty(globalThis, "sessionStorage");
    }
  }
});

void test("family grid wires fit and resize events into the autosave policy", async () => {
  const source = await readFile(
    new URL(
      "../src/lib/components/dashboard/ArtefactTable.svelte",
      import.meta.url,
    ),
    "utf8",
  );
  assert.match(source, /fitColumns/);
  assert.match(source, /onColumnResize=\{handleColumnResize\}/);
  assert.match(source, /createUserResizeViewHost\(ready\)/);
  assert.match(source, /attachAutoSavedView\(viewHost/);
  assert.match(source, /action === 'Reset columns'/);
  assert.match(source, /persistence\.resetResizes\(\)/);
  assert.match(source, /use:trackColumnWidthActions/);
});

/**
 * Minimal SvGrid API double: getState reports effective fitColumns widths while
 * setState treats supplied columnWidths as explicit resize overrides.
 * @param {number} initialContainerWidth
 */
function createFittingGrid(initialContainerWidth) {
  const columns = ["name", "status", "updated"];
  let containerWidth = initialContainerWidth;
  let userWidths = /** @type {Record<string, number>} */ ({});
  let globalFilter = "";

  const effectiveWidths = () => {
    const untouched = columns.filter((id) => !Object.hasOwn(userWidths, id));
    const remaining =
      containerWidth - Object.values(userWidths).reduce((a, b) => a + b, 0);
    const fittedWidth = untouched.length > 0 ? remaining / untouched.length : 0;
    return Object.fromEntries(
      columns.map((id) => [id, userWidths[id] ?? fittedWidth]),
    );
  };

  const api = {
    getState() {
      return {
        sorting: [],
        grouping: [],
        pagination: { pageIndex: 0, pageSize: 10 },
        columnWidths: effectiveWidths(),
        columnPinning: { left: [], right: [] },
        columnOrder: [...columns],
        hiddenColumns: [],
        globalFilter,
        columnFilters: {},
        facetFilters: {},
      };
    },
    /** @param {Partial<import("@svgrid/grid").SvGridViewState>} state */
    setState(state) {
      if (state.columnWidths !== undefined) {
        userWidths = { ...state.columnWidths };
      }
      if (state.globalFilter !== undefined) {
        globalFilter = state.globalFilter;
      }
    },
  };

  return {
    api,
    /** @param {string} columnId @param {number} width */
    resizeUserColumn(columnId, width) {
      userWidths = { ...userWidths, [columnId]: width };
    },
    resetColumns() {
      userWidths = {};
    },
    /** @param {number} width */
    setContainerWidth(width) {
      containerWidth = width;
    },
  };
}

/** @param {unknown} value @returns {value is Record<string, unknown>} */
function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

class MemorySessionStorage {
  /** @type {Map<string, string>} */
  #values = new Map();

  /** @param {string} key */
  getItem(key) {
    return this.#values.get(key) ?? null;
  }

  /** @param {string} key @param {string} value */
  setItem(key, value) {
    this.#values.set(key, value);
  }
}
