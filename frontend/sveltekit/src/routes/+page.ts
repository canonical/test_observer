// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import { redirect } from "@sveltejs/kit";
import { resolve } from "$app/paths";
import type { PageLoad } from "./$types";

export const load: PageLoad = () => {
  redirect(307, resolve("/snaps"));
};
