<!-- SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd. -->
<!-- SPDX-License-Identifier: GPL-3.0-only -->
<script lang="ts">
  import { Chip } from "@canonical/svelte-ds-app-launchpad";
  import type { TestExecutionStatus } from "$lib/types/test-execution.js";
  import { formatStatus } from "$lib/utils/formatting.js";

  interface Props {
    status: TestExecutionStatus;
  }

  const { status }: Props = $props();

  const severity = $derived(
    status === "PASSED"
      ? "positive"
      : status === "FAILED"
        ? "negative"
        : status === "IN_PROGRESS"
          ? "caution"
          : "neutral",
  );
</script>

<Chip value={formatStatus(status)} {severity} readonly />
