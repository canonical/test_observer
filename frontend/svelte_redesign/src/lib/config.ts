// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import { parse } from "yaml";
import { base } from "$app/paths";
import type { Config } from "$lib/types/config.js";

let _config: Config | null = null;

export async function loadConfig(fetchFn: typeof fetch = fetch): Promise<Config> {
  if (_config) return _config;
  const res = await fetchFn(`${base}/config.yaml`);
  const raw = await res.text();
  const parsed = parse(raw) as { require_authentication?: boolean; tabs?: string[] };
  _config = {
    requireAuthentication: parsed.require_authentication ?? false,
    tabs: parsed.tabs ?? [],
  };
  return _config;
}
