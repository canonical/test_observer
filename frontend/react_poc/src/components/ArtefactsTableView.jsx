import { useMemo } from 'react'
import { STATUS_NAMES } from '../services/api'
import './ArtefactsTableView.css'

export default function ArtefactsTableView({ artefacts, family, onArtefactClick }) {
  const columns = useMemo(() => {
    const baseColumns = [
      { key: 'name', label: 'Name', flex: 2 },
      { key: 'version', label: 'Version', flex: 2 }
    ]

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
    }

    const endColumns = [
      { key: 'due_date', label: 'Due date', flex: 1 },
      { key: 'reviews_remaining', label: 'Reviews remaining', flex: 1 },
      { key: 'status', label: 'Status', flex: 1 },
      { key: 'assignee', label: 'Assignee', flex: 1 }
    ]

    return [...baseColumns, ...(familyColumns[family] || []), ...endColumns]
  }, [family])

  const getStageName = (stage) => {
    if (!stage) return ''
    return stage.charAt(0).toUpperCase() + stage.slice(1)
  }

  const formatDueDate = (dueDate) => {
    if (!dueDate) return ''

    const date = new Date(dueDate)
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December']
    // Use UTC to match Flutter behavior which uses the date components directly
    return `${monthNames[date.getUTCMonth()]} ${date.getUTCDate()}`
  }

  const getStatusName = (status) => {
    return STATUS_NAMES[status] || status
  }

  if (artefacts.length === 0) {
    return (
      <div className="table-view">
        <div className="no-results">No artefacts found.</div>
      </div>
    )
  }

  return (
    <div className="table-view">
      <div className="table-container">
        <table className="artefacts-table">
          <thead>
            <tr>
              {columns.map(column => (
                <th key={column.key} style={{ flex: column.flex }}>
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {artefacts.map(artefact => (
              <tr
                key={artefact.id}
                onClick={() => onArtefactClick(artefact.id)}
                className="artefact-row"
              >
                <td style={{ flex: 2 }}>{artefact.name}</td>
                <td style={{ flex: 2 }}>{artefact.version}</td>
                {(family === 'snap' || family === 'charm') && (
                  <>
                    <td style={{ flex: 1 }}>{artefact.track}</td>
                    <td style={{ flex: 1 }}>{getStageName(artefact.stage)}</td>
                    <td style={{ flex: 1 }}>{artefact.branch}</td>
                  </>
                )}
                {family === 'deb' && (
                  <>
                    <td style={{ flex: 1 }}>{artefact.series}</td>
                    <td style={{ flex: 1 }}>{artefact.repo}</td>
                    <td style={{ flex: 1 }}>{getStageName(artefact.stage)}</td>
                    <td style={{ flex: 2 }}>{artefact.source}</td>
                  </>
                )}
                {family === 'image' && (
                  <>
                    <td style={{ flex: 1 }}>{artefact.os}</td>
                    <td style={{ flex: 1 }}>{artefact.release}</td>
                    <td style={{ flex: 1 }}>{getStageName(artefact.stage)}</td>
                  </>
                )}
                <td style={{ flex: 1 }}>{formatDueDate(artefact.due_date)}</td>
                <td style={{ flex: 1 }}>{artefact.all_environment_reviews_count - artefact.completed_environment_reviews_count}</td>
                <td style={{ flex: 1 }}>{getStatusName(artefact.status)}</td>
                <td style={{ flex: 1 }}>{artefact.assignee?.name || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
