// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

export interface User {
  id: number;
  name: string;
  email: string;
  launchpadHandle?: string;
}
