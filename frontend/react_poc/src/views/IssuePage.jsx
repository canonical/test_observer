import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'
import './IssuePage.css'

export default function IssuePage() {
  const { issueId } = useParams()
  const [issue, setIssue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadIssue = async () => {
      try {
        setLoading(true)
        const data = await api.fetchIssue(issueId)
        setIssue(data)
      } catch (e) {
        setError('Failed to load issue: ' + e.message)
        console.error('Failed to load issue:', e)
      } finally {
        setLoading(false)
      }
    }

    loadIssue()
  }, [issueId])

  if (loading) {
    return <div className="page-container"><div className="loading">Loading issue...</div></div>
  }

  if (error) {
    return <div className="page-container"><div className="error">{error}</div></div>
  }

  if (!issue) {
    return <div className="page-container"><div className="error">Issue not found</div></div>
  }

  return (
    <div className="issue-page">
      <div className="issue-header">
        <h1>{issue.title || `Issue #${issue.id}`}</h1>
        {issue.url && (
          <a href={issue.url} target="_blank" rel="noreferrer" className="issue-link">
            View in {issue.source || 'external tracker'}
          </a>
        )}
      </div>

      <div className="issue-details">
        <div className="detail-section">
          <h3>Details</h3>
          <div className="detail-grid">
            {issue.project && <p><strong>Project:</strong> {issue.project}</p>}
            {issue.status && <p><strong>Status:</strong> {issue.status}</p>}
            {issue.source && <p><strong>Source:</strong> {issue.source}</p>}
          </div>
        </div>

        {issue.description && (
          <div className="detail-section">
            <h3>Description</h3>
            <p className="issue-description">{issue.description}</p>
          </div>
        )}

        <div className="placeholder-message">
          <p>Full issue page implementation coming soon...</p>
          <p>This would display related test results, comments, and other issue metadata.</p>
        </div>
      </div>
    </div>
  )
}
