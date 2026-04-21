<script lang="ts">
  import { userStore } from '$lib/stores/user.svelte';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';

  interface Props {
    executionId: number;
    artefactId: number;
    store: ArtefactPageStore;
    open: boolean;
    onclose: () => void;
  }

  let { executionId, artefactId, store, open, onclose }: Props = $props();

  let dialogEl: HTMLDialogElement | undefined = $state();

  let name = $state('');
  let status = $state<'PASSED' | 'FAILED' | 'SKIPPED'>('PASSED');
  let comment = $state('');
  let ioLog = $state('');
  let submitting = $state(false);

  // Auto-prefix name with launchpad handle
  const namePrefix = $derived(
    userStore.current?.launchpad_handle
      ? `${userStore.current.launchpad_handle}/`
      : '',
  );

  // Open/close dialog based on prop
  $effect(() => {
    if (open && dialogEl) {
      name = '';
      status = 'PASSED';
      comment = '';
      ioLog = '';
      dialogEl.showModal();
    } else if (!open && dialogEl?.open) {
      dialogEl.close();
    }
  });

  async function handleSubmit() {
    const fullName = namePrefix + name;
    if (!fullName.trim()) return;
    submitting = true;
    await store.addTestResult(executionId, artefactId, {
      name: fullName,
      status,
      comment: comment || undefined,
      io_log: ioLog || undefined,
    });
    submitting = false;
    onclose();
  }
</script>

<dialog
  bind:this={dialogEl}
  onclose={onclose}
  class="add-result-dialog"
>
  <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
    <h3>Add Test Result</h3>

    <label class="field">
      Name
      <div class="name-input">
        {#if namePrefix}
          <span class="name-prefix">{namePrefix}</span>
        {/if}
        <input type="text" bind:value={name} required placeholder="test-case-name" />
      </div>
    </label>

    <label class="field">
      Status
      <select bind:value={status}>
        <option value="PASSED">Passed</option>
        <option value="FAILED">Failed</option>
        <option value="SKIPPED">Skipped</option>
      </select>
    </label>

    <label class="field">
      Comment
      <textarea bind:value={comment} rows="3" placeholder="Optional comment..."></textarea>
    </label>

    <label class="field">
      IO Log
      <textarea bind:value={ioLog} rows="4" placeholder="Optional log output..." class="mono"></textarea>
    </label>

    <div class="dialog-actions">
      <button type="button" class="cancel-btn" onclick={onclose}>Cancel</button>
      <button type="submit" class="save-btn" disabled={submitting || !name.trim()}>
        {submitting ? 'Adding...' : 'Add Result'}
      </button>
    </div>
  </form>
</dialog>

<style>
  .add-result-dialog {
    border: none;
    border-radius: 8px;
    padding: 24px;
    width: 500px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }

  .add-result-dialog::backdrop {
    background: rgba(0, 0, 0, 0.3);
  }

  h3 {
    margin: 0 0 16px;
    font-size: 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 12px;
    font-size: 13px;
    font-weight: 500;
  }

  .name-input {
    display: flex;
    align-items: center;
    border: 1px solid #ccc;
    border-radius: 4px;
    overflow: hidden;
  }

  .name-input:focus-within {
    border-color: #E95420;
  }

  .name-prefix {
    padding: 8px;
    background: #f5f5f5;
    color: #666;
    font-size: 13px;
    white-space: nowrap;
    border-right: 1px solid #ccc;
  }

  .name-input input {
    flex: 1;
    padding: 8px;
    border: none;
    font-size: 13px;
    font-family: inherit;
    outline: none;
  }

  select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
    background: #fff;
  }

  select:focus {
    outline: none;
    border-color: #E95420;
  }

  textarea {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
    resize: vertical;
  }

  textarea:focus {
    outline: none;
    border-color: #E95420;
  }

  textarea.mono {
    font-family: 'Ubuntu Mono', monospace;
    font-size: 12px;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 4px;
  }

  .cancel-btn {
    padding: 6px 14px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
  }

  .save-btn {
    padding: 6px 14px;
    border: none;
    border-radius: 4px;
    background: #E95420;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    font-family: inherit;
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
