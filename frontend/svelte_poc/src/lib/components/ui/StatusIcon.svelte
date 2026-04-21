<script lang="ts">
  import { EXECUTION_STATUS_ICONS, RESULT_STATUS_ICONS } from '$lib/utils/status-icons';
  import type { TestExecutionStatus, TestResultStatus } from '$lib/types/artefact-page';

  interface Props {
    status: TestExecutionStatus | TestResultStatus;
    size?: string;
  }

  let { status, size = '20px' }: Props = $props();

  const info = $derived(
    (EXECUTION_STATUS_ICONS as Record<string, { icon: string; color: string; label: string }>)[
      status
    ] ??
      (RESULT_STATUS_ICONS as Record<string, { icon: string; color: string; label: string }>)[
        status
      ],
  );
</script>

<span
  class="material-symbols-outlined status-icon"
  style="color: {info?.color}; font-size: {size}"
  title={info?.label}>{info?.icon}</span
>

<style>
  .status-icon {
    vertical-align: middle;
    line-height: 1;
  }
</style>
