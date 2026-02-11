import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api'
import './ArtefactPage.css'

export default function ArtefactPage() {
  const { artefactId } = useParams()
  const [artefact, setArtefact] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const loadArtefact = async () => {
      try {
        setLoading(true)
        const data = await api.fetchArtefact(artefactId)
        setArtefact(data)
      } catch (e) {
        setError('Failed to load artefact: ' + e.message)
        console.error('Failed to load artefact:', e)
      } finally {
        setLoading(false)
      }
    }

    loadArtefact()
  }, [artefactId])

  if (loading) {
    return <div className="page-container"><div className="loading">Loading artefact...</div></div>
  }

  if (error) {
    return <div className="page-container"><div className="error">{error}</div></div>
  }

  if (!artefact) {
    return <div className="page-container"><div className="error">Artefact not found</div></div>
  }

  return (
    <div className="artefact-page">
      <div className="artefact-header">
        <h1>{artefact.name}</h1>
        <h2>Version: {artefact.version}</h2>
      </div>

      <div className="artefact-details">
        <div className="detail-section">
          <h3>Details</h3>
          <div className="detail-grid">
            {artefact.track && <p><strong>Track:</strong> {artefact.track}</p>}
            {artefact.stage && <p><strong>Stage:</strong> {artefact.stage}</p>}
            {artefact.branch && <p><strong>Branch:</strong> {artefact.branch}</p>}
            {artefact.series && <p><strong>Series:</strong> {artefact.series}</p>}
            {artefact.repo && <p><strong>Repo:</strong> {artefact.repo}</p>}
            {artefact.source && <p><strong>Source:</strong> {artefact.source}</p>}
            {artefact.os && <p><strong>OS:</strong> {artefact.os}</p>}
            {artefact.release && <p><strong>Release:</strong> {artefact.release}</p>}
            {artefact.status && <p><strong>Status:</strong> {artefact.status}</p>}
            {artefact.assignee && <p><strong>Assignee:</strong> {artefact.assignee.name}</p>}
          </div>
        </div>

        <div className="placeholder-message">
          <p>Full artefact page implementation coming soon...</p>
          <p>This would display environment reviews, test executions, and build information.</p>
        </div>
      </div>
    </div>
  )
}
