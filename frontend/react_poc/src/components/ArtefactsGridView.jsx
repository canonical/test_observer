import { useMemo } from 'react'
import { FAMILY_STAGES, STATUS_NAMES } from '../services/api'
import UserAvatar from './UserAvatar'
import './ArtefactsGridView.css'

export default function ArtefactsGridView({ artefacts, family, onArtefactClick }) {
  const stages = FAMILY_STAGES[family] || []

  const getStageTitle = (stage) => {
    if (!stage && family === 'deb') return 'PPAs'
    if (!stage) return 'Unknown'
    return stage.charAt(0).toUpperCase() + stage.slice(1)
  }

  const getArtefactsForStage = (stage) => {
    return artefacts.filter(a => a.stage === stage)
  }

  const formatDueDate = (dueDate) => {
    if (!dueDate) return ''

    const date = new Date(dueDate)
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December']
    // Use UTC to match Flutter behavior which uses the date components directly
    return `${monthNames[date.getUTCMonth()]} ${date.getUTCDate()}`
  }

  const getStatusClass = (status) => {
    const statusMap = {
      'APPROVED': 'status-approved',
      'MARKED_AS_FAILED': 'status-rejected',
      'UNDECIDED': 'status-undecided'
    }
    return statusMap[status] || 'status-undecided'
  }

  const getStatusName = (status) => {
    return STATUS_NAMES[status] || status
  }

  if (artefacts.length === 0) {
    return (
      <div className="grid-view">
        <div className="no-results">No artefacts found.</div>
      </div>
    )
  }

  return (
    <div className="grid-view">
      <div className="stages-container">
        {stages.map(stage => (
          <div key={stage} className="stage-column">
            <h3 className="stage-title">{getStageTitle(stage)}</h3>
            <div className="artefacts-list">
              {getArtefactsForStage(stage).map(artefact => (
                <div
                  key={artefact.id}
                  className="artefact-card"
                  onClick={() => onArtefactClick(artefact.id)}
                >
                  <h4 className="artefact-name">{artefact.name}</h4>
                  <div className="artefact-info">
                    <p>version: {artefact.version}</p>
                    {artefact.track && <p>track: {artefact.track}</p>}
                    {artefact.store && <p>store: {artefact.store}</p>}
                    {artefact.branch && <p>branch: {artefact.branch}</p>}
                    {artefact.series && <p>series: {artefact.series}</p>}
                    {artefact.repo && <p>repo: {artefact.repo}</p>}
                    {artefact.source && <p>source: {artefact.source}</p>}
                    {artefact.os && <p>os: {artefact.os}</p>}
                    {artefact.release && <p>release: {artefact.release}</p>}
                    {artefact.owner && <p>owner: {artefact.owner}</p>}
                  </div>
                  <div className="artefact-footer">
                    <span className={`status-badge ${getStatusClass(artefact.status)}`}>
                      {getStatusName(artefact.status)}
                    </span>
                    {artefact.due_date && (
                      <span className="due-date">
                        Due {formatDueDate(artefact.due_date)}
                      </span>
                    )}
                    <UserAvatar
                      user={artefact.assignee}
                      allEnvironmentReviewsCount={artefact.all_environment_reviews_count}
                      completedEnvironmentReviewsCount={artefact.completed_environment_reviews_count}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
