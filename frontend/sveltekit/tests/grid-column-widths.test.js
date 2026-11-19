// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { after, before, test } from "node:test";
import { createServer } from "vite";
import { Window } from "happy-dom";

/** @type {import("vite").ViteDevServer | undefined} */
let vite;
/** @type {typeof import("../src/lib/gridViewUrl").createUserResizeViewHost | undefined} */
let createUserResizeViewHost;
/** @type {typeof import("../src/lib/gridViewUrl").familyViewStorage | undefined} */
let familyViewStorage;
/** @type {typeof import("../src/lib/gridViewUrl").searchGridViewStorage | undefined} */
let searchGridViewStorage;
/** @type {typeof import("../src/lib/gridViewUrl").encodeView | undefined} */
let encodeView;
/** @type {typeof import("../src/lib/gridViewUrl").AUTOSAVE_SLOT | undefined} */
let autosaveSlot;
/** @type {typeof import("@svgrid/grid").createNamedViews | undefined} */
let createNamedViews;
/** @type {typeof import("@svgrid/grid").attachAutoSavedView | undefined} */
let attachAutoSavedView;
/** @type {typeof import("../src/lib/components/dashboard/trackColumnWidthActions").createTrackColumnWidthActions | undefined} */
let createTrackColumnWidthActions;

before(async () => {
  vite = await createServer({
    configFile: "vite.config.ts",
    appType: "custom",
    logLevel: "silent",
    server: { middlewareMode: true },
  });
  ({
    createUserResizeViewHost,
    familyViewStorage,
    searchGridViewStorage,
    encodeView,
  } = await vite.ssrLoadModule("/src/lib/gridViewUrl.ts"));
  ({ AUTOSAVE_SLOT: autosaveSlot } = await vite.ssrLoadModule(
    "/src/lib/gridViewUrl.ts",
  ));
  ({ createNamedViews, attachAutoSavedView } =
    await vite.ssrLoadModule("@svgrid/grid"));
  ({ createTrackColumnWidthActions } = await vite.ssrLoadModule(
    "/src/lib/components/dashboard/trackColumnWidthActions.ts",
  ));
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
  const componentSource = await readFile(
    new URL(
      "../src/lib/components/dashboard/ArtefactTable.svelte",
      import.meta.url,
    ),
    "utf8",
  );
  const actionSource = await readFile(
    new URL(
      "../src/lib/components/dashboard/trackColumnWidthActions.ts",
      import.meta.url,
    ),
    "utf8",
  );
  assert.match(componentSource, /fitColumns/);
  assert.match(componentSource, /onColumnResize=\{handleColumnResize\}/);
  assert.match(componentSource, /createUserResizeViewHost\(ready\)/);
  assert.match(componentSource, /attachAutoSavedView\(viewHost/);
  assert.match(actionSource, /action === ["']Reset columns["']/);
  assert.match(actionSource, /persistence\.resetResizes\(\)/);
  assert.match(componentSource, /use:trackColumnWidthActions/);
});

void test("Search grid autosaves sparse resize overrides to isolated session storage", async () => {
  if (
    !createUserResizeViewHost ||
    !familyViewStorage ||
    !searchGridViewStorage ||
    !autosaveSlot ||
    !createNamedViews ||
    !attachAutoSavedView ||
    !encodeView
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

  const familyViews = familyViewStorage("snaps");
  familyViews.write([
    {
      name: autosaveSlot,
      createdAt: 1,
      state: { columnWidths: { name: 222 } },
    },
  ]);
  const familySnapshot = sessionStorage.getItem(
    "test-observer-grid-view:snaps",
  );

  const first = createFittingGrid(900);
  const firstWidthHost = createUserResizeViewHost(first.api);
  const firstViews = createNamedViews(firstWidthHost.host, {
    storage: searchGridViewStorage(),
  });
  const detachAutosave = attachAutoSavedView(firstWidthHost.host, firstViews, {
    skipRestore: true,
    intervalMs: 100,
  });

  try {
    assert.deepEqual(first.api.getState().columnWidths, {
      name: 300,
      status: 300,
      updated: 300,
    });
    assert.equal(
      sessionStorage.getItem("test-observer-search-grid-view"),
      null,
      "fresh Search autosave must not serialize fitted effective widths",
    );

    // Even an explicit initial snapshot contains no fitted width overrides.
    firstViews.save(autosaveSlot);
    const freshSnapshot = sessionStorage.getItem(
      "test-observer-search-grid-view",
    );
    assert.ok(freshSnapshot);
    const freshSnapshotValue = /** @type {unknown} */ (
      JSON.parse(freshSnapshot)
    );
    assert.ok(Array.isArray(freshSnapshotValue));
    const freshViews =
      /** @type {Array<{ name: string; state: { columnWidths: Record<string, number> } }>} */ (
        freshSnapshotValue
      );
    const freshView = freshViews.find((view) => view.name === autosaveSlot);
    assert.ok(freshView);
    assert.deepEqual(freshView.state.columnWidths, {});
    assert.deepEqual(Object.keys(freshView.state), ["columnWidths"]);

    // SvGrid's public resize callback records only the explicitly dragged
    // column; autosave persists that sparse map to Search's dedicated key.
    first.resizeUserColumn("name", 240);
    firstWidthHost.recordResize("name", 240);
    await new Promise((resolve) => setTimeout(resolve, 125));
    const savedSnapshot = sessionStorage.getItem(
      "test-observer-search-grid-view",
    );
    assert.ok(savedSnapshot);
    const savedSnapshotValue = /** @type {unknown} */ (
      JSON.parse(savedSnapshot)
    );
    assert.ok(Array.isArray(savedSnapshotValue));
    const savedViews =
      /** @type {Array<{ name: string; state: { columnWidths: Record<string, number> } }>} */ (
        savedSnapshotValue
      );
    const savedView = savedViews.find((view) => view.name === autosaveSlot);
    assert.ok(savedView);
    assert.deepEqual(savedView.state.columnWidths, { name: 240 });
    assert.deepEqual(Object.keys(savedView.state), ["columnWidths"]);
    assert.equal(
      sessionStorage.getItem("test-observer-grid-view:snaps"),
      familySnapshot,
      "Search persistence must not overwrite family view storage",
    );

    const restored = createFittingGrid(1200);
    const restoredWidthHost = createUserResizeViewHost(restored.api);
    const restoredViews = createNamedViews(restoredWidthHost.host, {
      storage: searchGridViewStorage(),
    });
    assert.equal(restoredViews.load(autosaveSlot), true);
    assert.deepEqual(restored.api.getState().columnWidths, {
      name: 240,
      status: 480,
      updated: 480,
    });
    restored.setContainerWidth(1500);
    assert.deepEqual(restored.api.getState().columnWidths, {
      name: 240,
      status: 630,
      updated: 630,
    });

    const shareStateWithWidth =
      /** @type {import("../src/lib/gridViewUrl").SharedGridView & { columnWidths: Record<string, number> }} */ ({
        columnWidths: { name: 240 },
      });
    assert.equal(
      encodeView(shareStateWithWidth),
      null,
      "column widths must remain outside URL state",
    );
  } finally {
    detachAutosave();
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

void test("Search grid wires resize persistence and menu action tracking", async () => {
  const componentSource = await readFile(
    new URL("../src/routes/test-results/+page.svelte", import.meta.url),
    "utf8",
  );
  assert.match(componentSource, /fitColumns/);
  assert.match(componentSource, /columnResize/);
  assert.match(componentSource, /onColumnResize=\{handleColumnResize\}/);
  assert.match(componentSource, /onApiReady=\{handleApiReady\}/);
  assert.match(componentSource, /createUserResizeViewHost\(ready\)/);
  assert.match(componentSource, /searchGridViewStorage\(\)/);
  assert.match(componentSource, /attachAutoSavedView\(viewHost/);
  assert.match(componentSource, /use:trackColumnWidthActions/);
  assert.match(componentSource, /detachAutosave\?\.\(\)/);
  assert.match(componentSource, /virtualization/);
  assert.match(componentSource, /enableRowHover/);
});

void test("family grid menu actions persist only measured width overrides", async () => {
  if (
    !createUserResizeViewHost ||
    !familyViewStorage ||
    !autosaveSlot ||
    !createNamedViews ||
    !attachAutoSavedView ||
    !createTrackColumnWidthActions
  ) {
    throw new Error("Grid view helpers were not loaded");
  }

  const originalSessionStorage = Object.getOwnPropertyDescriptor(
    globalThis,
    "sessionStorage",
  );
  const originalElement = Object.getOwnPropertyDescriptor(
    globalThis,
    "Element",
  );
  const browserWindow = new Window();
  const sessionStorage = new MemorySessionStorage();
  Object.defineProperty(globalThis, "sessionStorage", {
    configurable: true,
    value: sessionStorage,
  });
  Object.defineProperty(globalThis, "Element", {
    configurable: true,
    value: browserWindow.Element,
  });

  const grid = createFittingGrid(900);
  const persistence = createUserResizeViewHost(grid.api);
  const views = createNamedViews(persistence.host, {
    storage: familyViewStorage("snaps"),
  });
  const wrapper = browserWindow.document.createElement("div");
  wrapper.innerHTML = `
    <div class="sv-grid-root">
      <header data-svgrid-header-col="name"><button class="sv-grid-col-menu-btn"></button></header>
      <header data-svgrid-header-col="status"><button class="sv-grid-col-menu-btn is-open"></button></header>
      <header data-svgrid-header-col="updated"><button class="sv-grid-col-menu-btn"></button></header>
      <div data-col-id="name"></div>
      <div data-col-id="status"></div>
    </div>
    <div role="menu">
      <button role="menuitem"><span>Autosize</span> this column</button>
      <button role="menuitem">Autosize all columns</button>
      <button role="menuitem">Reset columns</button>
    </div>
  `;
  browserWindow.document.body.append(wrapper);

  const trackColumnWidthActions = createTrackColumnWidthActions({
    getPersistence: () => persistence,
    getCurrentApi: () => grid.api,
  });
  const action = trackColumnWidthActions(
    /** @type {HTMLDivElement} */ (/** @type {unknown} */ (wrapper)),
  );
  const detachAutosave = attachAutoSavedView(persistence.host, views, {
    skipRestore: true,
    intervalMs: 100,
  });

  const waitForAutosave = () =>
    new Promise((resolve) => setTimeout(resolve, 125));
  /**
   * @param {string} label
   * @param {() => void} applyGridAction
   */
  const clickMenuItem = (label, applyGridAction) => {
    const menuItem = Array.from(
      wrapper.querySelectorAll('[role="menuitem"]'),
    ).find((item) => item.textContent.replace(/\s+/g, " ").trim() === label);
    assert.ok(menuItem, `menu should contain ${label}`);
    menuItem.addEventListener("click", applyGridAction, { once: true });
    menuItem.dispatchEvent(
      new browserWindow.MouseEvent("click", { bubbles: true }),
    );
  };

  try {
    // User drags are already tracked by onColumnResize; menu actions must add
    // their widths without turning untouched fitted widths into overrides.
    grid.resizeUserColumn("name", 240);
    persistence.recordResize("name", 240);
    await waitForAutosave();
    assert.deepEqual(views.list()[0]?.state.columnWidths, { name: 240 });

    clickMenuItem("Autosize this column", () => {
      grid.resizeUserColumn("status", 360);
    });
    await waitForAutosave();
    assert.deepEqual(views.list()[0]?.state.columnWidths, {
      name: 240,
      status: 360,
    });

    clickMenuItem("Autosize all columns", () => {
      grid.resizeUserColumn("name", 250);
      grid.resizeUserColumn("status", 350);
      // The updated column has no rendered cell, so SvGrid cannot measure it.
    });
    await waitForAutosave();
    assert.deepEqual(views.list()[0]?.state.columnWidths, {
      name: 250,
      status: 350,
    });
    assert.equal(
      Object.hasOwn(views.list()[0]?.state.columnWidths ?? {}, "updated"),
      false,
      "unmeasurable fitted columns must not become persisted overrides",
    );

    clickMenuItem("Reset columns", () => {
      grid.resetColumns();
    });
    await waitForAutosave();
    assert.deepEqual(views.list()[0]?.state.columnWidths, {});

    const resetReload = createFittingGrid(1200);
    const resetViews = createNamedViews(
      createUserResizeViewHost(resetReload.api).host,
      { storage: familyViewStorage("snaps") },
    );
    assert.equal(resetViews.load(autosaveSlot), true);
    assert.deepEqual(resetReload.api.getState().columnWidths, {
      name: 400,
      status: 400,
      updated: 400,
    });
  } finally {
    detachAutosave();
    action.destroy();
    wrapper.remove();
    await browserWindow.happyDOM.abort();
    if (originalSessionStorage) {
      Object.defineProperty(
        globalThis,
        "sessionStorage",
        originalSessionStorage,
      );
    } else {
      Reflect.deleteProperty(globalThis, "sessionStorage");
    }
    if (originalElement) {
      Object.defineProperty(globalThis, "Element", originalElement);
    } else {
      Reflect.deleteProperty(globalThis, "Element");
    }
  }
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
    getColumns() {
      return columns.map((id) => ({ id }));
    },
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
