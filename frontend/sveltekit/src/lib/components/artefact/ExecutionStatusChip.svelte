<!--
  SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
  SPDX-License-Identifier: Apache-2.0
-->
<script lang="ts">
  import { Chip } from '@canonical/svelte-ds-app-launchpad';
  import type { TestExecutionStatus } from '$lib/types/openapi';
  import type { TestResultStatus } from '$lib/types/artefact-page';

  interface Props {
    status: TestExecutionStatus | TestResultStatus;
    density?: 'dense' | 'compact' | 'medium';
  }

  let { status, density = 'dense' }: Props = $props();

  const severity = $derived.by((): 'positive' | 'negative' | 'caution' | undefined => {
    switch (status) {
      case 'PASSED': return 'positive';
      case 'FAILED': return 'negative';
      case 'NOT_STARTED':
      case 'NOT_TESTED':
      case 'IN_PROGRESS':
      case 'ENDED_PREMATURELY':
      case 'SKIPPED': return 'caution';
      default: return undefined;
    }
  });

  const label = $derived.by(() => {
    switch (status) {
      case 'NOT_STARTED': return 'Not Started';
      case 'NOT_TESTED': return 'Not Tested';
      case 'IN_PROGRESS': return 'In Progress';
      case 'ENDED_PREMATURELY': return 'Ended Early';
      case 'FAILED': return 'Failed';
      case 'PASSED': return 'Passed';
      case 'SKIPPED': return 'Skipped';
      default: return status;
    }
  });
</script>

<Chip value={label} severity={severity} readonly {density} />
