// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { after, test } from "node:test";
import { Window } from "happy-dom";

const browserWindow = new Window({ url: "http://localhost/snaps" });
/** @type {Map<string, PropertyDescriptor | undefined>} */
const originalGlobals = new Map();
for (const name of [
  "document",
  "location",
  "Element",
  "HTMLAnchorElement",
  "SVGAElement",
]) {
  originalGlobals.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
  Object.defineProperty(globalThis, name, {
    configurable: true,
    value: Reflect.get(browserWindow, name),
  });
}

const [{ get_router_options }, { PRELOAD_PRIORITIES }] = await Promise.all([
  import("../node_modules/@sveltejs/kit/src/runtime/client/utils.js"),
  import("../node_modules/@sveltejs/kit/src/runtime/client/constants.js"),
]);

after(async () => {
  for (const [name, descriptor] of originalGlobals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else Reflect.deleteProperty(globalThis, name);
  }
  await browserWindow.happyDOM.abort();
});

void test("family links preload route code on hover but never preload route data", async () => {
  const appTemplate = await readFile(
    new URL("../src/app.html", import.meta.url),
    "utf8",
  );
  browserWindow.document.write(appTemplate);

  const familyLink = browserWindow.document.createElement("a");
  familyLink.href = "/debs";
  browserWindow.document.body.append(familyLink);

  // Resolve the inherited options using SvelteKit's installed router utility,
  // the same options its hover/tap listeners consult before preloading.
  const options = get_router_options(familyLink);
  assert.equal(
    options.preload_data,
    PRELOAD_PRIORITIES.false,
    "false disables hover and tap DATA preloads",
  );
  assert.equal(
    options.preload_code,
    PRELOAD_PRIORITIES.hover,
    "hover still preloads route code",
  );
});
