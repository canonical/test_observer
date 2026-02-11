import { useState, useEffect } from 'react'
import { api } from '../services/api'
import './IssuesPage.css'

export default function IssuesPage() {
  const [issues, setIssues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadIssues = async () => {
      try {
        setLoading(true)
        const data = await api.fetchIssues({ limit: 50 })
        setIssues(data)
      } catch (e) {
        setError('Failed to load issues: ' + e.message)
        console.error('Failed to load issues:', e)
      } finally {
        setLoading(false)
      }
    }

    loadIssues()
  }, [])

  return (
    <div className="issues-page">
      <div className="page-header">
        <h1>Issues</h1>
      </div>

      {loading && <div className="loading">Loading issues...</div>}
      {error && <div className="error">{error}</div>}
      
      {!loading && !error && (
        <div className="issues-list">
          {issues.length === 0 ? (
            <div className="no-results">No issues found.</div>
          ) : (
            issues.map(issue => (
              <div key={issue.id} className="issue-card">
                <h3>{issue.title || `Issue #${issue.id}`}</h3>
                <p className="issue-meta">
                  {issue.project && <span>Project: {issue.project}</span>}
                  {issue.status && <span>Status: {issue.status}</span>}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
