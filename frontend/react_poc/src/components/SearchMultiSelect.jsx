import { useState, useEffect, useRef } from 'react'
import './SearchMultiSelect.css'

export default function SearchMultiSelect({
  title,
  placeholder = 'Type 2+ characters to search...',
  value = [],
  onChange,
  searchFunction
}) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const debounceTimeoutRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-expand if there are initial selections
  useEffect(() => {
    if (value.length > 0 && !isExpanded) {
      setIsExpanded(true)
    }
  }, [value, isExpanded])

  const toggle = () => {
    setIsExpanded(prev => !prev)
    if (!isExpanded) {
      // Focus the search input when expanded
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus()
      }, 0)
    }
  }

  const handleSearchInput = (e) => {
    const query = e.target.value
    setSearchQuery(query)

    // Clear previous timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current)
    }

    // Only search if we have 2+ characters
    if (query.trim().length < 2) {
      setSuggestions([])
      return
    }

    // Debounce the search
    debounceTimeoutRef.current = setTimeout(() => {
      performSearch(query.trim())
    }, 300) // 300ms debounce
  }

  const performSearch = async (query) => {
    setIsLoading(true)
    setError(null)

    try {
      const results = await searchFunction(query)
      setSuggestions(results || [])
    } catch (e) {
      setError('Search failed')
      console.error('Search failed:', e)
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }

  const selectArtefact = (artefact) => {
    if (!value.includes(artefact)) {
      onChange([...value, artefact])
    }
    // Clear search after selection
    setSearchQuery('')
    setSuggestions([])
  }

  const deselectArtefact = (artefact) => {
    onChange(value.filter(a => a !== artefact))
  }

  return (
    <div className="search-multiselect">
      {/* Collapsible header */}
      <div className="multiselect-header" onClick={toggle}>
        <span className="header-title">
          {title} ({value.length} selected)
        </span>
        <span className="expand-icon">{isExpanded ? '▲' : '▼'}</span>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="multiselect-content">
          {/* Search input */}
          <input
            ref={inputRef}
            value={searchQuery}
            type="text"
            className="search-input"
            placeholder={placeholder}
            onChange={handleSearchInput}
          />

          {/* Loading state */}
          {isLoading && (
            <div className="loading-state">
              <span className="loading-spinner"></span>
              <span>Searching...</span>
            </div>
          )}

          {/* Error state */}
          {error && (
            <div className="error-state">
              <span>Error loading suggestions</span>
            </div>
          )}

          {/* Search results dropdown */}
          {suggestions.length > 0 && !isLoading && (
            <div className="suggestions-dropdown">
              {suggestions.map(suggestion => (
                <div
                  key={suggestion}
                  className="suggestion-item"
                  onClick={() => selectArtefact(suggestion)}
                >
                  {suggestion}
                </div>
              ))}
            </div>
          )}

          {/* Selected items with checkboxes */}
          {value.length > 0 && (
            <div className="selected-items">
              {value.map(artefact => (
                <div key={artefact} className="selected-item">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={true}
                      onChange={() => deselectArtefact(artefact)}
                    />
                    <span className="item-name">{artefact}</span>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
