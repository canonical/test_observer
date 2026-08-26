// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: Apache-2.0

import type { PageLoad } from "./$types";
import { error } from "@sveltejs/kit";

export const load: PageLoad = async ({ parent, params }) => {
  const parentData = await parent();
  const families = parentData.artefactFamilies;
  const family = params.family;
  for (let i = 0; i < families.length; i++) {
    if (families[i].name === family) {
      return { family, title: families[i].friendly_name };
    }
  }
  error(404, `Unknown family: ${family}`);
};
