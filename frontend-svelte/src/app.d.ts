// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { User } from "$lib/types/user.js";
import type { Config } from "$lib/types/config.js";

declare global {
  namespace App {
    interface Locals {
      user: User | null;
      config: Config;
    }
    interface PageData {
      user: User | null;
      config: Config;
    }
  }
}

export {};
