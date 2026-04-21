<script lang="ts">
  import { STATUS_COLORS, STATUS_LABELS, type ArtefactStatus } from '$lib/types';

  let { status }: { status: ArtefactStatus } = $props();
</script>

<span class="status-chip" style="color: {STATUS_COLORS[status]}; border-color: {STATUS_COLORS[status]};">
  {STATUS_LABELS[status]}
</span>

<style>
  .status-chip {
    display: inline-block;
    padding: 2px 8px;
    border: 1px solid;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 500;
    white-space: nowrap;
  }
</style>
