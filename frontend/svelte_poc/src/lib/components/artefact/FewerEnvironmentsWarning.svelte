<script lang="ts">
  import { api } from '$lib/api/client';
  import type { Artefact } from '$lib/types';
  import type { ArtefactVersion } from '$lib/types/artefact-page';

  interface Props {
    artefact: Artefact;
    versions: ArtefactVersion[];
  }

  let { artefact, versions }: Props = $props();

  let previousArtefact = $state<Artefact | null>(null);
  let dismissed = $state(false);
  let dismissedForId = $state<number | null>(null);
  let loaded = $state(false);

  // Reset dismissal when artefact changes
  $effect(() => {
    if (artefact.id !== dismissedForId) {
      dismissed = false;
      dismissedForId = null;
    }
  });

  // Load previous version data
  $effect(() => {
    loaded = false;
    previousArtefact = null;

    const sorted = [...versions].sort((a, b) => b.artefact_id - a.artefact_id);
    const currentIdx = sorted.findIndex((v) => v.artefact_id === artefact.id);
    if (currentIdx < 0 || currentIdx >= sorted.length - 1) {
      loaded = true;
      return;
    }

    const previousId = sorted[currentIdx + 1].artefact_id;

    api<Artefact>(`/artefacts/${previousId}`).then((data) => {
      if (data) previousArtefact = data;
      loaded = true;
    });
  });

  const showWarning = $derived(
    loaded &&
    !dismissed &&
    previousArtefact !== null &&
    artefact.all_environment_reviews_count < previousArtefact.all_environment_reviews_count,
  );

  const previousVersion = $derived(
    previousArtefact ? previousArtefact.version : '',
  );

  function dismiss() {
    dismissed = true;
    dismissedForId = artefact.id;
  }
</script>

{#if showWarning && previousArtefact}
  <div class="warning-banner">
    <span class="material-symbols-outlined warning-icon">warning</span>
    <span class="warning-text">
      This version has {artefact.all_environment_reviews_count} environment{artefact.all_environment_reviews_count !== 1 ? 's' : ''},
      which is fewer than the {previousArtefact.all_environment_reviews_count} environment{previousArtefact.all_environment_reviews_count !== 1 ? 's' : ''}
      of the previously added version ({previousVersion}).
    </span>
    <button class="dismiss-btn" onclick={dismiss} aria-label="Dismiss warning">
      <span class="material-symbols-outlined">close</span>
    </button>
  </div>
{/if}

<style>
  .warning-banner {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 16px;
    background: #fef3e2;
    border: 1px solid #f0c36d;
    border-radius: 8px;
    font-size: 13px;
    color: #5c3d00;
  }

  .warning-icon {
    font-size: 20px;
    color: #e08700;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .warning-text {
    flex: 1;
    line-height: 1.4;
  }

  .dismiss-btn {
    all: unset;
    cursor: pointer;
    flex-shrink: 0;
    color: #5c3d00;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    padding: 2px;
  }

  .dismiss-btn:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  .dismiss-btn .material-symbols-outlined {
    font-size: 18px;
  }
</style>
