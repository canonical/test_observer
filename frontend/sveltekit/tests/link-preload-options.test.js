// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { Window } from "happy-dom";

void test("app template configures code preloading on hover and disables data preloading", async () => {
  const appTemplate = await readFile(
    new URL("../src/app.html", import.meta.url),
    "utf8",
  );
  const browserWindow = new Window();
  try {
    browserWindow.document.write(appTemplate);
    const body = browserWindow.document.body;
    assert.equal(body.getAttribute("data-sveltekit-preload-data"), "false");
    assert.equal(body.getAttribute("data-sveltekit-preload-code"), "hover");
  } finally {
    await browserWindow.happyDOM.abort();
  }
});
