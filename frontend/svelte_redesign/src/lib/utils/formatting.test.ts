// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { describe, it, expect } from "vitest";

describe("smoke test", () => {
  it("can import formatting utilities", async () => {
    const { capitalize, formatStatus, formatDate } = await import(
      "$lib/utils/formatting.js"
    );
    expect(capitalize("hello")).toBe("Hello");
    expect(formatStatus("APPROVED")).toBe("Approved");
    expect(typeof formatDate).toBe("function");
  });
});
