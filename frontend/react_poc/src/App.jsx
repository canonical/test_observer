import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './views/Dashboard'
import ArtefactPage from './views/ArtefactPage'
import TestResultsSearchPage from './views/TestResultsSearchPage'
import IssuesPage from './views/IssuesPage'
import IssuePage from './views/IssuePage'
import './App.css'

export default function App() {
  return (
    <Router basename="/react_poc">
      <div id="app">
        <Navbar />
        <main>
          <div className="content-container">
            <Routes>
              <Route path="/" element={<Navigate to="/snaps" replace />} />
              <Route path="/snaps" element={<Dashboard />} />
              <Route path="/snaps/:artefactId" element={<ArtefactPage />} />
              <Route path="/debs" element={<Dashboard />} />
              <Route path="/debs/:artefactId" element={<ArtefactPage />} />
              <Route path="/charms" element={<Dashboard />} />
              <Route path="/charms/:artefactId" element={<ArtefactPage />} />
              <Route path="/images" element={<Dashboard />} />
              <Route path="/images/:artefactId" element={<ArtefactPage />} />
              <Route path="/test-results" element={<TestResultsSearchPage />} />
              <Route path="/issues" element={<IssuesPage />} />
              <Route path="/issues/:issueId" element={<IssuePage />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  )
}
