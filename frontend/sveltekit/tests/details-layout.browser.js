// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

// Shared semantic + real geometry assertions for live API and synthetic fixture
// browsers. No Playwright project dependency, app hooks or intercepted requests.
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return */
import assert from "node:assert/strict";

export async function assertDetailsLayout(
  dialog,
  metadata = /** @type {Record<string, string[]>} */ ({}),
) {
  const entries = Object.entries(metadata).sort(([a], [b]) =>
    a < b ? -1 : a > b ? 1 : 0,
  );
  const table = dialog.getByRole("table", {
    name: "Execution Metadata",
    exact: true,
  });
  assert.equal(await table.count(), entries.length ? 1 : 0);
  if (entries.length) {
    assert.deepEqual(
      await table.locator("thead th[scope=col]").allTextContents(),
      ["Category", "Values"],
    );
    assert.deepEqual(
      await table.locator("tbody th[scope=row]").allTextContents(),
      entries.map(([key]) => (key === "" ? "—" : key)),
    );
    assert.equal(await table.locator("tbody tr").count(), entries.length);
    for (let i = 0; i < entries.length; i++) {
      const values = entries[i][1];
      const row = table.locator("tbody tr").nth(i);
      assert.equal(await row.locator("th, td").count(), 2);
      if (values.length)
        assert.deepEqual(
          await row.locator("td li").allTextContents(),
          [...values].sort().map((value) => (value === "" ? "—" : value)),
        );
      else assert.equal((await row.locator("td").textContent()).trim(), "—");
    }
  } else {
    assert.equal(
      await dialog
        .getByText("No execution metadata available.", { exact: true })
        .count(),
      1,
    );
  }
  const geometry = await dialog.evaluate(
    /** @param {HTMLDialogElement} element */ (element) => {
      const body = element.querySelector(".details-body");
      if (!body) throw new Error("Missing modal body");
      /** @param {Element | null} node */
      const bounds = (node) => {
        if (!node) throw new Error("Missing detail element");
        const rect = node.getBoundingClientRect();
        return {
          top: rect.top,
          bottom: rect.bottom,
          left: rect.left,
          right: rect.right,
          width: rect.width,
          height: rect.height,
        };
      };
      const rows = Array.from(
        element.querySelectorAll(".scalar-details .description-list-item"),
      ).map((row) => ({
        row: bounds(row),
        label: bounds(row.querySelector("dt")),
        value: bounds(row.querySelector("dd")),
        align: getComputedStyle(row).alignItems,
        labelTextAlign: getComputedStyle(row.querySelector("dt")).textAlign,
        valueTextAlign: getComputedStyle(row.querySelector("dd")).textAlign,
      }));
      const table = element.querySelector("table.execution-metadata");
      const log = element.querySelector("pre.io-log");
      return {
        modal: bounds(element),
        body: bounds(body),
        header: bounds(element.querySelector("header")),
        footer: bounds(element.querySelector("footer")),
        viewport: { width: innerWidth, height: innerHeight },
        rows,
        table: table
          ? {
              bounds: bounds(table),
              section: bounds(table.closest("section")),
              nested: Boolean(table.closest("dd")),
              cells: Array.from(table.querySelectorAll("tr")).map((row) =>
                Array.from(row.children).map((cell) => ({
                  bounds: bounds(cell),
                  align: getComputedStyle(cell).verticalAlign,
                })),
              ),
            }
          : null,
        scrollers: Array.from(body.querySelectorAll("*"))
          .filter((node) =>
            /auto|scroll/.test(getComputedStyle(node).overflowY),
          )
          .map((node) => node.tagName + "." + node.className),
        horizontalOverflow: Array.from(body.querySelectorAll("*"))
          .filter(
            (node) =>
              node.clientWidth > 0 && node.scrollWidth > node.clientWidth + 1,
          )
          .map((node) => node.tagName + "." + node.className),
        log: log
          ? {
              maxHeight: getComputedStyle(log).maxHeight,
              overflow: getComputedStyle(log).overflow,
              whitespace: getComputedStyle(log).whiteSpace,
              wrap: getComputedStyle(log).overflowWrap,
              tabindex: log.getAttribute("tabindex"),
            }
          : null,
        locked:
          getComputedStyle(document.documentElement).overflowY === "hidden",
        bodyOverflow: body.scrollHeight > body.clientHeight,
      };
    },
  );
  const { modal, viewport, header, footer, rows } = geometry;
  assert.ok(
    Math.abs(modal.width - Math.min(900, viewport.width - 32)) <= 2,
    "Keep the existing ~900px modal and viewport margins",
  );
  assert.ok(
    modal.left >= 15 &&
      modal.right <= viewport.width - 15 &&
      modal.top >= 15 &&
      modal.bottom <= viewport.height - 15,
  );
  assert.ok(
    header.top >= modal.top &&
      header.bottom <= modal.bottom &&
      footer.top >= modal.top &&
      footer.bottom <= modal.bottom,
    "Header/footer stay visible outside the body scroller",
  );
  assert.ok(rows.length >= 14, "Every scalar field has a label/value row");
  for (const {
    row,
    label,
    value,
    align,
    labelTextAlign,
    valueTextAlign,
  } of rows) {
    assert.equal(align, "start");
    assert.equal(labelTextAlign, "start");
    assert.equal(
      valueTextAlign,
      "start",
      "Pragma's right-aligned list rule must not win",
    );
    assert.ok(
      Math.abs(label.top - value.top) < 1,
      "Multiline label and value top align",
    );
    assert.ok(
      value.left > label.right && Math.abs(value.right - row.right) < 1,
      "Values get the rest of the row, not a narrow grid column",
    );
    assert.ok(
      value.width > row.width * 0.55,
      "Scalar values have most of the modal width",
    );
    assert.ok(label.width <= 12 * 16 + 1, "Compact label column");
  }
  for (let i = 1; i < rows.length; i++)
    assert.ok(
      rows[i].row.top >= rows[i - 1].row.bottom - 1,
      "Scalar fields stack vertically",
    );
  if (geometry.table) {
    const { bounds, section, nested, cells } = geometry.table;
    assert.equal(nested, false);
    assert.ok(
      Math.abs(bounds.width - section.width) < 1 &&
        Math.abs(bounds.left - section.left) < 1,
      "Metadata spans the full section, outside the scalar value column",
    );
    for (const row of cells) {
      assert.equal(row.length, 2);
      assert.ok(row.every((cell) => cell.align === "top"));
      const ratio = row[1].bounds.width / bounds.width;
      assert.ok(
        ratio > 0.58 && ratio < 0.68,
        "Metadata values receive roughly 65% width",
      );
    }
  }
  assert.deepEqual(
    geometry.scrollers,
    [],
    "The modal body is the only vertical scroll container",
  );
  assert.deepEqual(
    geometry.horizontalOverflow,
    [],
    "No clipping or nested horizontal scrollpanes",
  );
  assert.equal(geometry.locked, true);
  if (geometry.log)
    assert.deepEqual(geometry.log, {
      maxHeight: "none",
      overflow: "visible",
      whitespace: "pre-wrap",
      wrap: "anywhere",
      tabindex: null,
    });
  return geometry;
}

export async function assertLogBodyScrolling(page, dialog) {
  const body = dialog.locator(".details-body");
  assert.equal(
    await body.getAttribute("tabindex"),
    "0",
    "Only the body needs a keyboard scroll stop",
  );
  await body.evaluate((element) => {
    element.scrollTop = 0;
  });
  await body.focus();
  await page.keyboard.press("PageDown");
  await page.waitForTimeout(250);
  assert.ok(
    await body.evaluate((element) => element.scrollTop > 0),
    "PageDown scrolls the body from the scalar fields",
  );
  await page.keyboard.press("End");
  await page.waitForTimeout(250);
  assert.ok(
    await body.evaluate(
      (element) =>
        Math.abs(
          element.scrollHeight - element.clientHeight - element.scrollTop,
        ) < 2,
    ),
    "End reaches the complete log's end",
  );
  const wheel = [];
  for (const fraction of [0, 0.5, 1]) {
    const before = await body.evaluate(
      /** @param {HTMLElement} element @param {number} fraction */ (
        element,
        fraction,
      ) => {
        const log = element.querySelector("pre");
        if (!log) throw new Error("Missing log");
        const start =
          log.getBoundingClientRect().top -
          element.getBoundingClientRect().top +
          element.scrollTop -
          element.clientHeight / 3;
        const max = element.scrollHeight - element.clientHeight;
        element.scrollTop = start + (max - start) * fraction;
        const bounds = element.getBoundingClientRect();
        const logBounds = log.getBoundingClientRect();
        return {
          top: element.scrollTop,
          x: bounds.left + bounds.width / 2,
          y:
            (Math.max(bounds.top, logBounds.top) +
              Math.min(bounds.bottom, logBounds.bottom)) /
            2,
          page: document.scrollingElement.scrollTop,
        };
      },
      fraction,
    );
    await page.mouse.move(before.x, before.y);
    assert.equal(
      await page.evaluate(
        ({ x, y }) =>
          Boolean(
            document.elementFromPoint(Number(x), Number(y))?.closest("pre"),
          ),
        before,
      ),
      true,
      "Wheel really targets the log, not another element",
    );
    await page.mouse.wheel(0, fraction === 1 ? -500 : 500);
    await page.waitForTimeout(250);
    const after = await body.evaluate((element) => ({
      top: element.scrollTop,
      page: document.scrollingElement.scrollTop,
    }));
    assert.ok(
      fraction === 1 ? after.top < before.top : after.top > before.top,
      "Wheel over log moves the modal body at start/middle/end",
    );
    assert.equal(after.page, before.page, "Background stays locked");
    wheel.push({ fraction, before: before.top, after: after.top });
  }
  await body.focus();
  await page.keyboard.press("End");
  await page.waitForTimeout(250);
  assert.ok(
    await body.evaluate(
      /** @param {HTMLElement} element */ (element) =>
        element.querySelector("pre").getBoundingClientRect().bottom <=
        element.getBoundingClientRect().bottom + 1,
    ),
    "End of the natural-height log is reachable inside the body",
  );
  return { keyboardPageDownEnd: true, wheel };
}
