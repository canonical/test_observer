<script>
  import { FAMILY_STAGES, STATUS_NAMES } from '../services/api';
  import UserAvatar from './UserAvatar.svelte';
  import { createEventDispatcher } from 'svelte';

  export let artefacts;
  export let family;

  const dispatch = createEventDispatcher();

  $: stages = FAMILY_STAGES[family] || [];

  function getStageTitle(stage) {
    if (!stage && family === 'deb') return 'PPAs';
    if (!stage) return 'Unknown';
    return stage.charAt(0).toUpperCase() + stage.slice(1);
  }

  function getArtefactsForStage(stage) {
    return artefacts.filter(a => a.stage === stage);
  }

  function formatDueDate(dueDate) {
    if (!dueDate) return '';

    const date = new Date(dueDate);
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'];
    return `${monthNames[date.getUTCMonth()]} ${date.getUTCDate()}`;
  }

  function getStatusClass(status) {
    const statusMap = {
      'APPROVED': 'status-approved',
      'MARKED_AS_FAILED': 'status-rejected',
      'UNDECIDED': 'status-undecided'
    };
    return statusMap[status] || 'status-undecided';
  }

  function getStatusName(status) {
    return STATUS_NAMES[status] || status;
  }

  function handleArtefactClick(artefactId) {
    dispatch('artefact-click', artefactId);
  }
</script>

<div class="grid-view">
  {#if artefacts.length === 0}
    <div class="no-results">
      No artefacts found.
    </div>
  {:else}
    <div class="stages-container">
      {#each stages as stage (stage)}
        <div class="stage-column">
          <h3 class="stage-title">{getStageTitle(stage)}</h3>
          <div class="artefacts-list">
            {#each getArtefactsForStage(stage) as artefact (artefact.id)}
              <div
                class="artefact-card"
                on:click={() => handleArtefactClick(artefact.id)}
              >
                <h4 class="artefact-name">{artefact.name}</h4>
                <div class="artefact-info">
                  <p>version: {artefact.version}</p>
                  {#if artefact.track}<p>track: {artefact.track}</p>{/if}
                  {#if artefact.store}<p>store: {artefact.store}</p>{/if}
                  {#if artefact.branch}<p>branch: {artefact.branch}</p>{/if}
                  {#if artefact.series}<p>series: {artefact.series}</p>{/if}
                  {#if artefact.repo}<p>repo: {artefact.repo}</p>{/if}
                  {#if artefact.source}<p>source: {artefact.source}</p>{/if}
                  {#if artefact.os}<p>os: {artefact.os}</p>{/if}
                  {#if artefact.release}<p>release: {artefact.release}</p>{/if}
                  {#if artefact.owner}<p>owner: {artefact.owner}</p>{/if}
                </div>
                <div class="artefact-footer">
                  <span class="status-badge {getStatusClass(artefact.status)}">
                    {getStatusName(artefact.status)}
                  </span>
                  {#if artefact.due_date}
                    <span class="due-date">
                      Due {formatDueDate(artefact.due_date)}
                    </span>
                  {/if}
                  <UserAvatar
                    user={artefact.assignee}
                    allEnvironmentReviewsCount={artefact.all_environment_reviews_count}
                    completedEnvironmentReviewsCount={artefact.completed_environment_reviews_count}
                  />
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
.grid-view {
  width: 100%;
}

.stages-container {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 16px;
}

.stage-column {
  flex: 0 0 320px;
  min-width: 320px;
}

.stage-title {
  font-size: 20px;
  font-weight: 400;
  margin-bottom: 16px;
  color: #111;
}

.artefacts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.artefact-card {
  background: white;
  border: 1px solid #CDCDCD;
  border-radius: 2px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 180px;
  display: flex;
  flex-direction: column;
}

.artefact-card:hover {
  border-color: #0E8420;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.artefact-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #111;
}

.artefact-info {
  flex: 1;
  font-size: 14px;
  color: #111;
  line-height: 1.4;
}

.artefact-info p {
  margin: 2px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artefact-footer {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
  padding-top: 8px;
}

.artefact-footer :global(.user-avatar) {
  margin-left: auto;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
  border: 1px solid #CDCDCD;
}

.status-approved {
  color: #0E8420;
}

.status-rejected {
  color: #C7162B;
}

.status-undecided {
  color: #666;
}

.due-date {
  font-size: 11px;
  color: #C7162B;
  flex-shrink: 0;
  padding: 4px 12px;
  border-radius: 16px;
  border: 1px solid #CDCDCD;
}

.no-results {
  padding: 32px;
  text-align: center;
  color: #666;
}
</style>
