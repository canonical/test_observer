<script>
  import { STATUS_NAMES } from '../services/api';
  import { createEventDispatcher } from 'svelte';

  export let artefacts;
  export let family;

  const dispatch = createEventDispatcher();

  $: columns = (() => {
    const baseColumns = [
      { key: 'name', label: 'Name', flex: 2 },
      { key: 'version', label: 'Version', flex: 2 }
    ];

    const familyColumns = {
      snap: [
        { key: 'track', label: 'Track', flex: 1 },
        { key: 'risk', label: 'Risk', flex: 1 },
        { key: 'branch', label: 'Branch', flex: 1 }
      ],
      deb: [
        { key: 'series', label: 'Series', flex: 1 },
        { key: 'repo', label: 'Repo', flex: 1 },
        { key: 'pocket', label: 'Pocket', flex: 1 },
        { key: 'source', label: 'Source', flex: 2 }
      ],
      charm: [
        { key: 'track', label: 'Track', flex: 1 },
        { key: 'risk', label: 'Risk', flex: 1 },
        { key: 'branch', label: 'Branch', flex: 1 }
      ],
      image: [
        { key: 'os', label: 'OS', flex: 1 },
        { key: 'release', label: 'Release', flex: 1 },
        { key: 'stage', label: 'Stage', flex: 1 }
      ]
    };

    const endColumns = [
      { key: 'due_date', label: 'Due date', flex: 1 },
      { key: 'reviews_remaining', label: 'Reviews remaining', flex: 1 },
      { key: 'status', label: 'Status', flex: 1 },
      { key: 'assignee', label: 'Assignee', flex: 1 }
    ];

    return [...baseColumns, ...(familyColumns[family] || []), ...endColumns];
  })();

  function getStageName(stage) {
    if (!stage) return '';
    return stage.charAt(0).toUpperCase() + stage.slice(1);
  }

  function formatDueDate(dueDate) {
    if (!dueDate) return '';

    const date = new Date(dueDate);
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'];
    return `${monthNames[date.getUTCMonth()]} ${date.getUTCDate()}`;
  }

  function getStatusName(status) {
    return STATUS_NAMES[status] || status;
  }

  function handleArtefactClick(artefactId) {
    dispatch('artefact-click', artefactId);
  }
</script>

<div class="table-view">
  {#if artefacts.length === 0}
    <div class="no-results">
      No artefacts found.
    </div>
  {:else}
    <div class="table-container">
      <table class="artefacts-table">
        <thead>
          <tr>
            {#each columns as column (column.key)}
              <th style="flex: {column.flex}">
                {column.label}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each artefacts as artefact (artefact.id)}
            <tr
              on:click={() => handleArtefactClick(artefact.id)}
              class="artefact-row"
            >
              <td style="flex: 2">{artefact.name}</td>
              <td style="flex: 2">{artefact.version}</td>
              {#if family === 'snap' || family === 'charm'}
                <td style="flex: 1">{artefact.track}</td>
                <td style="flex: 1">{getStageName(artefact.stage)}</td>
                <td style="flex: 1">{artefact.branch}</td>
              {/if}
              {#if family === 'deb'}
                <td style="flex: 1">{artefact.series}</td>
                <td style="flex: 1">{artefact.repo}</td>
                <td style="flex: 1">{getStageName(artefact.stage)}</td>
                <td style="flex: 2">{artefact.source}</td>
              {/if}
              {#if family === 'image'}
                <td style="flex: 1">{artefact.os}</td>
                <td style="flex: 1">{artefact.release}</td>
                <td style="flex: 1">{getStageName(artefact.stage)}</td>
              {/if}
              <td style="flex: 1">{formatDueDate(artefact.due_date)}</td>
              <td style="flex: 1">{artefact.all_environment_reviews_count - artefact.completed_environment_reviews_count}</td>
              <td style="flex: 1">{getStatusName(artefact.status)}</td>
              <td style="flex: 1">{artefact.assignee?.name || 'N/A'}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
.table-view {
  width: 100%;
}

.table-container {
  width: 100%;
  max-width: 1300px;
  overflow-x: auto;
}

.artefacts-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.artefacts-table thead {
  border-bottom: 1px solid #CDCDCD;
}

.artefacts-table th {
  padding: 16px 8px;
  text-align: left;
  font-size: 16px;
  font-weight: 500;
  color: #111;
  white-space: nowrap;
}

.artefacts-table tbody tr {
  border-bottom: 1px solid #E5E5E5;
}

.artefact-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.artefact-row:hover {
  background-color: #f7f7f7;
}

.artefacts-table td {
  padding: 12px 8px;
  font-size: 14px;
  color: #111;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artefacts-table th,
.artefacts-table td {
  display: inline-flex;
  align-items: center;
}

.artefacts-table tr {
  display: flex;
  width: 100%;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  display: inline-block;
  border: 1px solid currentColor;
}

.status-approved {
  color: #0E8420;
  background: transparent;
}

.status-rejected {
  color: #C7162B;
  background: transparent;
}

.status-undecided {
  color: #666;
  background: transparent;
}

.no-results {
  padding: 32px;
  text-align: center;
  color: #666;
}
</style>
