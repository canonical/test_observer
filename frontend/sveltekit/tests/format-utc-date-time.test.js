// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import assert from "node:assert/strict";
import { test } from "node:test";
import { formatUtcDateTime } from "../src/lib/formatUtcDateTime.js";

void test("converts explicit offsets to UTC, including a date rollover", () => {
  assert.equal(
    formatUtcDateTime("2026-01-02T00:34:05.987654+01:00"),
    "2026-01-01 23:34:05",
  );
});

void test("drops fractional seconds and the timezone suffix", () => {
  assert.equal(
    formatUtcDateTime("2026-06-07T08:09:10.999999Z"),
    "2026-06-07 08:09:10",
  );
});
