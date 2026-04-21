<script lang="ts">
  import { api } from '$lib/api/client';
  import type { ArtefactPageStore } from '$lib/stores/artefact-page.svelte';
  import type { Environment } from '$lib/types/artefact-page';
  import { FAMILY_TO_API, type Family } from '$lib/types';

  interface Props {
    artefactId: number;
    family: Family;
    store: ArtefactPageStore;
    open: boolean;
    onclose: () => void;
  }

  let { artefactId, family, store, open, onclose }: Props = $props();

  let dialogEl: HTMLDialogElement | undefined = $state();

  let envQuery = $state('');
  let envResults = $state<Environment[]>([]);
  let selectedEnv = $state<Environment | null>(null);
  let searching = $state(false);
  let relevantLinks = $state<{ label: string; url: string }[]>([]);
  let submitting = $state(false);

  let debounceTimer: ReturnType<typeof setTimeout> | undefined;

  $effect(() => {
    if (open && dialogEl) {
      envQuery = '';
      envResults = [];
      selectedEnv = null;
      relevantLinks = [];
      dialogEl.showModal();
    } else if (!open && dialogEl?.open) {
      dialogEl.close();
    }
  });

  function handleEnvInput() {
    clearTimeout(debounceTimer);
    selectedEnv = null;
    if (envQuery.length < 2) {
      envResults = [];
      return;
    }
    debounceTimer = setTimeout(async () => {
      searching = true;
      const familyApi = FAMILY_TO_API[family];
      const params = new URLSearchParams({ q: envQuery, limit: '20' });
      params.append('families[]', familyApi);
      const data = await api<Environment[]>(`/environments?${params.toString()}`);
      envResults = data ?? [];
      searching = false;
    }, 300);
  }

  function selectEnv(env: Environment) {
    selectedEnv = env;
    envQuery = `${env.name} (${env.architecture})`;
    envResults = [];
  }

  function addLink() {
    relevantLinks = [...relevantLinks, { label: '', url: '' }];
  }

  function removeLink(index: number) {
    relevantLinks = relevantLinks.filter((_, i) => i !== index);
  }

  async function handleSubmit() {
    if (!selectedEnv) return;
    submitting = true;

    const body: Record<string, unknown> = {
      artefact_id: artefactId,
      environment_id: selectedEnv.id,
      test_plan: 'Manual Testing',
      relevant_links: relevantLinks
        .filter((l) => l.url.trim())
        .map((l) => ({ label: l.label || l.url, url: l.url })),
    };

    await store.startManualTest(artefactId, body);
    submitting = false;
    onclose();
  }
</script>

<dialog
  bind:this={dialogEl}
  onclose={onclose}
  class="manual-test-dialog"
>
  <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
    <h3>Start Manual Testing</h3>

    <label class="field">
      Environment
      <div class="env-autocomplete">
        <input
          type="text"
          bind:value={envQuery}
          oninput={handleEnvInput}
          placeholder="Search environments (min 2 chars)..."
        />
        {#if envResults.length > 0 && !selectedEnv}
          <ul class="env-dropdown">
            {#each envResults as env (env.id)}
              <li>
                <button type="button" onclick={() => selectEnv(env)}>
                  {env.name} <span class="env-arch">({env.architecture})</span>
                </button>
              </li>
            {/each}
          </ul>
        {/if}
        {#if searching}
          <span class="searching">Searching...</span>
        {/if}
      </div>
    </label>

    <label class="field">
      Test Plan
      <input type="text" value="Manual Testing" disabled />
    </label>

    <div class="field">
      <span>Relevant Links</span>
      {#each relevantLinks as link, i}
        <div class="link-row">
          <input type="text" bind:value={link.label} placeholder="Label" class="link-label" />
          <input type="url" bind:value={link.url} placeholder="https://..." class="link-url" />
          <button type="button" class="remove-link-btn" onclick={() => removeLink(i)} title="Remove">
            <span class="material-symbols-outlined" style="font-size:16px">close</span>
          </button>
        </div>
      {/each}
      <button type="button" class="add-link-btn" onclick={addLink}>
        <span class="material-symbols-outlined" style="font-size:16px">add</span>
        Add Link
      </button>
    </div>

    <div class="dialog-actions">
      <button type="button" class="cancel-btn" onclick={onclose}>Cancel</button>
      <button type="submit" class="save-btn" disabled={submitting || !selectedEnv}>
        {submitting ? 'Starting...' : 'Start Test'}
      </button>
    </div>
  </form>
</dialog>

<style>
  .manual-test-dialog {
    border: none;
    border-radius: 8px;
    padding: 24px;
    width: 600px;
    max-width: 90vw;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  }

  .manual-test-dialog::backdrop {
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

  .field input,
  .field input[disabled] {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 13px;
    font-family: inherit;
  }

  .field input:focus {
    outline: none;
    border-color: #E95420;
  }

  .field input[disabled] {
    background: #f5f5f5;
    color: #999;
  }

  .env-autocomplete {
    position: relative;
  }

  .env-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 10;
    margin: 2px 0 0;
    padding: 0;
    list-style: none;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    max-height: 200px;
    overflow-y: auto;
  }

  .env-dropdown li button {
    display: block;
    width: 100%;
    padding: 8px 10px;
    border: none;
    background: none;
    text-align: left;
    cursor: pointer;
    font-size: 13px;
    font-family: inherit;
  }

  .env-dropdown li button:hover {
    background: #f5f5f5;
  }

  .env-arch {
    color: #999;
    font-size: 12px;
  }

  .searching {
    font-size: 12px;
    color: #999;
    padding: 4px 0;
  }

  .link-row {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .link-label {
    width: 140px;
    flex-shrink: 0;
  }

  .link-url {
    flex: 1;
  }

  .remove-link-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    color: #999;
    padding: 0;
  }

  .remove-link-btn:hover {
    background: #fde8e8;
    color: #C7162B;
  }

  .add-link-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border: 1px dashed #ccc;
    border-radius: 4px;
    background: transparent;
    cursor: pointer;
    font-size: 13px;
    color: #666;
    font-family: inherit;
    align-self: flex-start;
  }

  .add-link-btn:hover {
    border-color: #E95420;
    color: #E95420;
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
