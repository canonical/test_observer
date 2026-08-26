// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

export interface User {
  id: number;
  email: string;
  name: string;
  launchpad_handle: string | null;
}
