// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import type { PageLoad } from "./$types.js";
import { getIssue } from "$lib/api/issues.js";

export const load: PageLoad = async ({ params, url, fetch, parent }) => {
  const id = Number(params.id);
  const issue = await getIssue(id, fetch);
  const { config } = await parent();

  return {
    issue,
    familyOptions: config.tabs,
    activeAttachmentRuleId: url.searchParams.get("attachmentRule")
      ? Number(url.searchParams.get("attachmentRule"))
      : undefined,
  };
};
