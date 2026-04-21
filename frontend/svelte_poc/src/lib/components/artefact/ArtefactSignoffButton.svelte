<script lang="ts">
  import type { Artefact, ArtefactStatus } from '$lib/types';
  import { STATUS_LABELS, STATUS_COLORS } from '$lib/types';

  interface Props {
    artefact: Artefact;
    onstatuschange: (status: ArtefactStatus) => void;
  }

  let { artefact, onstatuschange }: Props = $props();

  let popoverRef = $state<HTMLDivElement | null>(null);
  let buttonRef = $state<HTMLButtonElement | null>(null);

  function togglePopover() {
    popoverRef?.togglePopover();
  }

  function select(status: ArtefactStatus) {
    popoverRef?.hidePopover();
    onstatuschange(status);
  }

  const statuses: ArtefactStatus[] = ['APPROVED', 'MARKED_AS_FAILED', 'UNDECIDED'];
  const currentColor = $derived(STATUS_COLORS[artefact.status]);
  const currentLabel = $derived(STATUS_LABELS[artefact.status]);
</script>

<div class="signoff-wrapper">
  <button
    bind:this={buttonRef}
    class="signoff-btn"
    style="border-color: {currentColor}; color: {currentColor}"
    onclick={togglePopover}
  >
    {currentLabel}
    <span class="material-symbols-outlined arrow">arrow_drop_down</span>
  </button>

  <div
    bind:this={popoverRef}
    popover="auto"
    class="signoff-popover"
  >
    {#each statuses as status (status)}
      <button
        class="popover-option"
        class:active={artefact.status === status}
        onclick={() => select(status)}
      >
        <span class="dot" style="background: {STATUS_COLORS[status]}"></span>
        {STATUS_LABELS[status]}
      </button>
    {/each}
  </div>
</div>

<style>
  .signoff-wrapper {
    position: relative;
  }

  .signoff-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    font-size: 14px;
    font-weight: 400;
    font-family: inherit;
    color: #333;
  }

  .signoff-btn:hover {
    background: #f9f9f9;
  }

  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .arrow {
    font-size: 20px;
    color: #666;
  }

  .signoff-popover {
    position: absolute;
    inset: unset;
    top: anchor(bottom);
    left: anchor(left);
    margin: 0;
    padding: 4px 0;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    min-width: 180px;
  }

  .popover-option {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 14px;
    border: none;
    background: none;
    cursor: pointer;
    font-size: 14px;
    font-family: inherit;
    text-align: left;
  }

  .popover-option:hover {
    background: #f5f5f5;
  }

  .popover-option.active {
    font-weight: 600;
  }
</style>
