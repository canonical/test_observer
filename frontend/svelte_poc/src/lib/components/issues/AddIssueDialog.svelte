<script lang="ts">
  interface Props {
    open: boolean;
    onadd: (id: number) => void;
    onclose: () => void;
  }

  let { open, onadd, onclose }: Props = $props();

  import { api } from '$lib/api/client';

  let dialogEl = $state<HTMLDialogElement | null>(null);
  let url = $state('');
  let busy = $state(false);
  let errorMsg = $state('');

  $effect(() => {
    if (open && dialogEl) {
      url = '';
      errorMsg = '';
      busy = false;
      dialogEl.showModal();
    } else if (!open && dialogEl) {
      dialogEl.close();
    }
  });

  async function handleAdd() {
    if (!url.trim()) return;
    busy = true;
    errorMsg = '';
    const result = await api<{ id: number }>('/issues', {
      method: 'PUT',
      body: JSON.stringify({ url: url.trim() }),
    });
    if (result) {
      busy = false;
      onadd(result.id);
    } else {
      errorMsg = 'Failed to add issue. Check the URL and try again.';
      busy = false;
    }
  }

  function handleClose() {
    onclose();
  }
</script>

<dialog
  bind:this={dialogEl}
  class="add-issue-dialog"
  onclose={handleClose}
>
  <h3>Add Issue</h3>
  <p class="dialog-subtitle">Enter the URL of a GitHub, Jira, or Launchpad issue.</p>
  <label class="dialog-label">
    Issue URL
    <input
      type="url"
      class="dialog-input"
      bind:value={url}
      placeholder="https://github.com/org/repo/issues/123"
    />
  </label>
  {#if errorMsg}
    <p class="dialog-error">{errorMsg}</p>
  {/if}
  <div class="dialog-actions">
    <button class="btn-cancel" onclick={handleClose}>Cancel</button>
    <button class="btn-submit" disabled={busy || !url.trim()} onclick={handleAdd}>
      {busy ? 'Adding...' : 'Add'}
    </button>
  </div>
</dialog>

<style>
  .add-issue-dialog {
    border: none;
    border-radius: 8px;
    padding: 24px;
    max-width: 480px;
    width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }

  .add-issue-dialog::backdrop {
    background: rgba(0, 0, 0, 0.4);
  }

  h3 {
    margin: 0 0 4px;
    font-size: 18px;
  }

  .dialog-subtitle {
    margin: 0 0 16px;
    font-size: 13px;
    color: #666;
  }

  .dialog-label {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
    color: #333;
  }

  .dialog-input {
    padding: 8px 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    outline: none;
  }

  .dialog-input:focus {
    border-color: #E95420;
  }

  .dialog-error {
    color: #c7162b;
    font-size: 13px;
    margin: 8px 0 0;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 20px;
  }

  .btn-cancel {
    background: none;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
    cursor: pointer;
    color: #000;
  }

  .btn-cancel:hover {
    border-color: #999;
  }

  .btn-submit {
    background: #E95420;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
    cursor: pointer;
    font-weight: 500;
  }

  .btn-submit:hover:not(:disabled) {
    background: #d4471a;
  }

  .btn-submit:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
