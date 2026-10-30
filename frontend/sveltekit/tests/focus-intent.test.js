// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0
/* eslint-disable @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access */
import assert from "node:assert/strict";
import { before, test } from "node:test";
import { build } from "vite";
import { Window } from "happy-dom";

let FocusIntent;
before(async () => {
  const built = await build({
    configFile: false,
    logLevel: "silent",
    build: {
      write: false,
      lib: { entry: "src/lib/focusIntent.ts", formats: ["es"] },
      rolldownOptions: { output: { codeSplitting: false } },
    },
  });
  const bundle = built[0].output.find((item) => item.type === "chunk");
  ({ FocusIntent } = await import(
    `data:text/javascript;base64,${Buffer.from(bundle.code).toString("base64")}`
  ));
});

function fixture(t) {
  const window = new Window();
  const document = window.document;
  document.body.innerHTML =
    '<div><button id="source">Load</button></div><input id="other"><section id="fallback" tabindex="-1"></section>';
  const source = document.querySelector("#source");
  const other = document.querySelector("#other");
  const fallback = document.querySelector("#fallback");
  const intent = new FocusIntent();
  const listeners = new Set();
  const add = document.addEventListener.bind(document);
  const remove = document.removeEventListener.bind(document);
  document.addEventListener = (name, listener, options) => {
    if (name === "focusin") listeners.add(listener);
    add(name, listener, options);
  };
  document.removeEventListener = (name, listener, options) => {
    if (name === "focusin") listeners.delete(listener);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument -- Test-only forwarding preserves Happy DOM's generic listener overload unchanged.
    remove(name, listener, options);
  };
  t.after(() => {
    intent.cancel();
    assert.equal(
      listeners.size,
      0,
      "no intent listener leaks after completion/disposal",
    );
    void window.happyDOM.abort();
  });
  return { document, source, other, fallback, intent, listeners };
}

void test("focus intent returns an initially focused surviving control only after a navigation/disabled-style body blur", (t) => {
  const f = fixture(t);
  f.source.focus();
  const owner = f.intent.begin(f.source, () => true);
  f.source.blur();
  assert.equal(f.document.activeElement === f.document.body, true);
  owner.restore();
  assert.equal(f.document.activeElement === f.source, true);
  assert.equal(f.listeners.size, 0);
  f.other.focus();
  f.intent.begin(f.source, () => true).restore();
  assert.equal(
    f.document.activeElement === f.other,
    true,
    "programmatic activation of an unfocused source owns no focus",
  );
});

void test("focus intent remembers another destination even when it later blurs to body", (t) => {
  const f = fixture(t);
  f.source.focus();
  const owner = f.intent.begin(f.source, () => true);
  f.other.focus();
  assert.equal(f.listeners.size, 0, "intervening intent cancels immediately");
  f.other.blur();
  owner.restore(() => f.fallback);
  assert.equal(
    f.document.activeElement === f.document.body,
    true,
    "body blur cannot revive old intent",
  );
});

void test("focus intent uses an available current-owner fallback only when the focused source disappeared", (t) => {
  const f = fixture(t);
  f.source.focus();
  const owner = f.intent.begin(f.source, () => true);
  f.source.blur();
  f.source.remove();
  owner.restore(() => f.fallback);
  assert.equal(f.document.activeElement === f.fallback, true);
  f.fallback.blur();
  owner.restore(() => f.other);
  assert.equal(
    f.document.activeElement === f.document.body,
    true,
    "a completed operation cannot restore twice",
  );
});

void test("focus intent supersession and old cleanup cannot cancel or complete a newer pending return", (t) => {
  const f = fixture(t);
  f.source.focus();
  const old = f.intent.begin(f.source, () => true);
  const current = f.intent.begin(f.source, () => true);
  assert.equal(f.listeners.size, 1);
  old.cancel();
  old.restore(() => f.other);
  assert.equal(f.listeners.size, 1);
  f.source.blur();
  current.restore();
  assert.equal(f.document.activeElement === f.source, true);
  assert.equal(f.listeners.size, 0);
});

void test("focus intent invalid owner, explicit hide/unmount cancellation and A/B/A cancellation never refocus", (t) => {
  const f = fixture(t);
  for (const mode of ["invalid", "hide", "unmount", "ABA"]) {
    f.source.focus();
    let current = true;
    const owner = f.intent.begin(f.source, () => current);
    f.source.blur();
    if (mode === "invalid") current = false;
    else {
      current = false;
      f.intent.cancel();
      current = true;
    }
    owner.restore(() => f.fallback);
    assert.equal(f.document.activeElement === f.document.body, true, mode);
    assert.equal(f.listeners.size, 0);
  }
});

void test("focus intent never focuses a hidden, inert, disabled or detached target/fallback", (t) => {
  const f = fixture(t);
  for (const mode of ["hidden", "inert", "disabled", "detached"]) {
    f.source.focus();
    const owner = f.intent.begin(f.source, () => true);
    f.source.blur();
    if (mode === "disabled") f.source.disabled = true;
    else if (mode === "detached") f.source.remove();
    else f.source.parentElement.setAttribute(mode, "");
    f.fallback.setAttribute("hidden", "");
    owner.restore(() => f.fallback);
    assert.equal(f.document.activeElement === f.document.body, true, mode);
    f.document.querySelector("div").append(f.source);
    f.source.disabled = false;
    f.source.parentElement.removeAttribute("hidden");
    f.source.parentElement.removeAttribute("inert");
  }
});
