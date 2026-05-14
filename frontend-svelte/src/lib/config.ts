// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { parse } from "yaml";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { Config } from "$lib/types/config.js";

let _config: Config | null = null;

export function loadConfig(): Config {
  if (_config) return _config;
  const raw = readFileSync(resolve("static/config.yaml"), "utf-8");
  const parsed = parse(raw) as { require_authentication?: boolean; tabs?: string[] };
  _config = {
    requireAuthentication: parsed.require_authentication ?? false,
    tabs: parsed.tabs ?? [],
  };
  return _config;
}
