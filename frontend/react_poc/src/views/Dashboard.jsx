import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../services/api'
import FilterIcon from '../components/FilterIcon'
import ArtefactsTableView from '../components/ArtefactsTableView'
import ArtefactsGridView from '../components/ArtefactsGridView'
import './Dashboard.css'

export default function Dashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  
  const [viewMode, setViewMode] = useState(localStorage.getItem('viewMode') || 'grid')
  const [showFilters, setShowFilters] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [artefacts, setArtefacts] = useState([])
  const [selectedFilters, setSelectedFilters] = useState({})
  const [expandedFilters, setExpandedFilters] = useState({})

  // Helper functions for filtering (defined before use to avoid TDZ issues)
  const getDueDateCategory = (dueDate) => {
    if (!dueDate) return 'No due date'

    const now = new Date()
    const due = new Date(dueDate)

    if (due < now) return 'Overdue'

    const daysDiff = Math.ceil((due - now) / (1000 * 60 * 60 * 24))
    if (daysDiff <= 7) return 'Within a week'
    return 'More than a week'
  }

  const getArtefactFilterValue = (artefact, filterName) => {
    switch (filterName) {
      case 'Assignee':
        return artefact.assignee?.name || 'N/A'
      case 'Status':
        return artefact.status === 'APPROVED' ? 'Approved'
             : artefact.status === 'MARKED_AS_FAILED' ? 'Rejected'
             : 'Undecided'
      case 'Due date':
        return getDueDateCategory(artefact.due_date)
      case 'Risk':
      case 'Pocket':
        return artefact.stage ? artefact.stage.charAt(0).toUpperCase() + artefact.stage.slice(1) : ''
      case 'Series':
        return artefact.series
      case 'OS type':
        return artefact.os
      case 'Release':
        return artefact.release
      case 'Owner':
        return artefact.owner
      default:
        return ''
    }
  }

  const getFilterOptions = (filterName) => {
    const options = new Set()
    artefacts.forEach(artefact => {
      const value = getArtefactFilterValue(artefact, filterName)
      if (value) options.add(value)
    })
    return Array.from(options).sort()
  }

  // Extract family from route meta
  const family = useMemo(() => {
    const path = location.pathname
    if (path.includes('/snaps')) return 'snap'
    if (path.includes('/debs')) return 'deb'
    if (path.includes('/charms')) return 'charm'
    if (path.includes('/images')) return 'image'
    return 'snap'
  }, [location.pathname])

  const title = useMemo(() => {
    const familyName = family.charAt(0).toUpperCase() + family.slice(1)
    return `${familyName} Update Verification`
  }, [family])

  const filteredArtefacts = useMemo(() => {
    let filtered = artefacts

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(a =>
        a.name.toLowerCase().includes(query) ||
        a.version.toLowerCase().includes(query)
      )
    }

    // Apply selected filters
    for (const [filterName, selectedOptions] of Object.entries(selectedFilters)) {
      if (selectedOptions.length > 0) {
        filtered = filtered.filter(artefact => {
          const value = getArtefactFilterValue(artefact, filterName)
          return selectedOptions.includes(value)
        })
      }
    }

    return filtered
  }, [artefacts, searchQuery, selectedFilters])

  const availableFilters = useMemo(() => {
    if (!artefacts.length) return []

    const filterDefinitions = {
      snap: ['Assignee', 'Status', 'Due date', 'Risk'],
      deb: ['Assignee', 'Status', 'Due date', 'Series', 'Pocket'],
      charm: ['Assignee', 'Status', 'Due date', 'Risk'],
      image: ['OS type', 'Release', 'Owner', 'Assignee', 'Status', 'Due date']
    }

    const filtersForFamily = filterDefinitions[family] || []

    return filtersForFamily.map(filterName => ({
      name: filterName,
      options: getFilterOptions(filterName)
    }))
  }, [artefacts, family])

  const navigateToArtefact = (artefactId) => {
    navigate(`/${family}s/${artefactId}`)
  }

  const loadArtefacts = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await api.fetchArtefacts(family)
      setArtefacts(data)
      // Reset filters when family changes
      setSelectedFilters({})
      setExpandedFilters({})
    } catch (e) {
      setError('Failed to load artefacts: ' + e.message)
      console.error('Failed to load artefacts:', e)
    } finally {
      setLoading(false)
    }
  }, [family])

  const toggleFilterOption = (filterName, option, isSelected) => {
    setSelectedFilters(prev => {
      const current = prev[filterName] || []
      
      if (isSelected) {
        if (!current.includes(option)) {
          return { ...prev, [filterName]: [...current, option] }
        }
      } else {
        return { ...prev, [filterName]: current.filter(o => o !== option) }
      }
      
      return prev
    })
  }

  const isOptionSelected = (filterName, option) => {
    return selectedFilters[filterName]?.includes(option) || false
  }

  const toggleFilterExpanded = (filterName) => {
    setExpandedFilters(prev => ({ ...prev, [filterName]: !prev[filterName] }))
  }

  const isFilterExpanded = (filterName) => {
    // Default to expanded if not set
    return expandedFilters[filterName] !== false
  }

  useEffect(() => {
    localStorage.setItem('viewMode', viewMode)
  }, [viewMode])

  useEffect(() => {
    loadArtefacts()
  }, [loadArtefacts])

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{title}</h1>
        <div className="view-toggle">
          <button
            onClick={() => setViewMode('list')}
            className={`toggle-button ${viewMode === 'list' ? 'active' : ''}`}
            title="List view"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" y1="6" x2="21" y2="6"></line>
              <line x1="8" y1="12" x2="21" y2="12"></line>
              <line x1="8" y1="18" x2="21" y2="18"></line>
              <line x1="3" y1="6" x2="3.01" y2="6"></line>
              <line x1="3" y1="12" x2="3.01" y2="12"></line>
              <line x1="3" y1="18" x2="3.01" y2="18"></line>
            </svg>
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`toggle-button ${viewMode === 'grid' ? 'active' : ''}`}
            title="Dashboard view"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
          </button>
        </div>
      </div>

      <div className="dashboard-body">
        <div className="filters-toggle">
          <button onClick={() => setShowFilters(!showFilters)} className="filter-button">
            <FilterIcon />
          </button>
        </div>

        {showFilters && (
          <div className="filters-panel">
            <h3>Filters</h3>

            <div className="filter-section">
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                type="text"
                placeholder="Search by name"
                className="search-input"
              />
            </div>

            {availableFilters.map(filter => (
              <div key={filter.name} className="filter-section">
                <div className="filter-header" onClick={() => toggleFilterExpanded(filter.name)}>
                  <span className="filter-title">{filter.name}</span>
                  <span className="expand-icon">{isFilterExpanded(filter.name) ? '▼' : '▶'}</span>
                </div>
                {isFilterExpanded(filter.name) && (
                  <div className="filter-options">
                    {filter.options.map(option => (
                      <label key={option} className="filter-option">
                        <input
                          type="checkbox"
                          checked={isOptionSelected(filter.name, option)}
                          onChange={(e) => toggleFilterOption(filter.name, option, e.target.checked)}
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="content-area">
          {loading && <div className="loading">Loading artefacts...</div>}
          {error && <div className="error">{error}</div>}
          {!loading && !error && (
            viewMode === 'list' ? (
              <ArtefactsTableView
                artefacts={filteredArtefacts}
                family={family}
                onArtefactClick={navigateToArtefact}
              />
            ) : (
              <ArtefactsGridView
                artefacts={filteredArtefacts}
                family={family}
                onArtefactClick={navigateToArtefact}
              />
            )
          )}
        </div>
      </div>
    </div>
  )
}
