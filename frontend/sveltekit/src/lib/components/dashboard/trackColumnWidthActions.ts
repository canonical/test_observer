// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { createUserResizeViewHost } from "$lib/gridViewUrl";

type ResizeWidthPersistence = ReturnType<typeof createUserResizeViewHost>;
interface CurrentGridApi {
  getColumns(): readonly { id: string }[];
  getState(): { columnWidths: Partial<Record<string, number>> };
}

/**
 * Creates the DOM action that records menu-driven width changes for autosave.
 * The getters keep it connected to the current family grid and persistence
 * host when the dashboard is reused across family routes.
 */
export function createTrackColumnWidthActions(getters: {
  getPersistence(): ResizeWidthPersistence | null;
  getCurrentApi(): CurrentGridApi | null;
}) {
  return function trackColumnWidthActions(node: HTMLDivElement) {
    function handleClick(event: MouseEvent) {
      const target = event.target;
      if (!(target instanceof Element)) return;
      const menuItem = target.closest<HTMLElement>('[role="menuitem"]');
      const action = menuItem?.textContent.replace(/\s+/g, " ").trim();
      const persistence = getters.getPersistence();
      if (!menuItem || !persistence || !action) return;

      if (action === "Reset columns") {
        persistence.resetResizes();
        return;
      }

      const autosizeAll = action === "Autosize all columns";
      if (!autosizeAll && action !== "Autosize this column") return;

      const ready = getters.getCurrentApi();
      if (!ready) return;
      const gridRoot = node.querySelector<HTMLElement>(".sv-grid-root");
      const measurableColumns = new Set(
        Array.from(
          gridRoot?.querySelectorAll<HTMLElement>("[data-col-id]") ?? [],
        )
          .map((cell) => cell.getAttribute("data-col-id"))
          .filter((id): id is string => id !== null),
      );
      const columnId = autosizeAll
        ? null
        : (node
            .querySelector<HTMLElement>(".sv-grid-col-menu-btn.is-open")
            ?.closest<HTMLElement>("[data-svgrid-header-col]")
            ?.getAttribute("data-svgrid-header-col") ?? null);
      const columnIds = autosizeAll
        ? ready.getColumns().map((column) => column.id)
        : columnId
          ? [columnId]
          : [];
      // autosizeColumn() returns without changing state when no rendered body
      // cell exists. That same condition must not turn a fitted width into an
      // apparent explicit width in our persistence layer.
      const measuredIds = columnIds.filter((id) => measurableColumns.has(id));
      if (measuredIds.length === 0) return;

      queueMicrotask(() => {
        if (
          getters.getPersistence() !== persistence ||
          getters.getCurrentApi() !== ready
        ) {
          return;
        }
        const widths = ready.getState().columnWidths;
        for (const id of measuredIds) {
          const width = widths[id];
          if (width !== undefined) persistence.recordResize(id, width);
        }
      });
    }

    node.addEventListener("click", handleClick, true);
    return {
      destroy() {
        node.removeEventListener("click", handleClick, true);
      },
    };
  };
}
