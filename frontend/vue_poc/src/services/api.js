// API service for Test Observer
const API_BASE_URL = window.location.origin.replace(':30001', ':30000')

export const api = {
  async fetchArtefacts(family) {
    const response = await fetch(`${API_BASE_URL}/v1/artefacts?family=${family}`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch artefacts: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/v1/users/me`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (response.ok) {
      const data = await response.json()
      return data || null
    }
    return null
  },

  async fetchArtefact(artefactId) {
    const response = await fetch(`${API_BASE_URL}/v1/artefacts/${artefactId}`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch artefact: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchArtefactBuilds(artefactId) {
    const response = await fetch(`${API_BASE_URL}/v1/artefacts/${artefactId}/builds`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch artefact builds: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchEnvironmentReviews(artefactId) {
    const response = await fetch(`${API_BASE_URL}/v1/artefacts/${artefactId}/environment-reviews`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch environment reviews: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchTestResults(testExecutionId) {
    const response = await fetch(`${API_BASE_URL}/v1/test-executions/${testExecutionId}/test-results`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch test results: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchTestEvents(testExecutionId) {
    const response = await fetch(`${API_BASE_URL}/v1/test-executions/${testExecutionId}/status_update`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch test events: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchIssues(params = {}) {
    const queryParams = new URLSearchParams()

    if (params.source) queryParams.append('source', params.source)
    if (params.project) queryParams.append('project', params.project)
    if (params.status) queryParams.append('status', params.status)
    if (params.q) queryParams.append('q', params.q)
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.offset) queryParams.append('offset', params.offset)

    const url = `${API_BASE_URL}/v1/issues${queryParams.toString() ? '?' + queryParams.toString() : ''}`

    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch issues: ${response.statusText}`)
    }

    return response.json()
  },

  async fetchIssue(issueId) {
    const response = await fetch(`${API_BASE_URL}/v1/issues/${issueId}`, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch issue: ${response.statusText}`)
    }

    return response.json()
  },

  async searchTestResults(params = {}) {
    const queryParams = new URLSearchParams()

    // Handle array parameters
    if (params.families && Array.isArray(params.families)) {
      params.families.forEach(f => queryParams.append('families', f))
    }
    if (params.artefacts && Array.isArray(params.artefacts)) {
      params.artefacts.forEach(a => queryParams.append('artefacts', a))
    }
    if (params.environments && Array.isArray(params.environments)) {
      params.environments.forEach(e => queryParams.append('environments', e))
    }
    if (params.test_cases && Array.isArray(params.test_cases)) {
      params.test_cases.forEach(tc => queryParams.append('test_cases', tc))
    }
    if (params.issues && Array.isArray(params.issues)) {
      params.issues.forEach(i => queryParams.append('issues', i))
    }
    if (params.test_result_statuses && Array.isArray(params.test_result_statuses)) {
      params.test_result_statuses.forEach(s => queryParams.append('test_result_statuses', s))
    }

    // Handle scalar parameters
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.offset) queryParams.append('offset', params.offset)
    if (params.from_date) queryParams.append('from_date', params.from_date)
    if (params.until_date) queryParams.append('until_date', params.until_date)

    const url = `${API_BASE_URL}/v1/test-results${queryParams.toString() ? '?' + queryParams.toString() : ''}`

    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch test results: ${response.statusText}`)
    }

    return response.json()
  },

  async searchArtefacts(params) {
    const queryParams = new URLSearchParams()

    // Add query parameter
    if (params.q) queryParams.append('q', params.q)
    
    // Add limit and offset
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.offset) queryParams.append('offset', params.offset)

    const url = `${API_BASE_URL}/v1/artefacts/search${queryParams.toString() ? '?' + queryParams.toString() : ''}`

    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to search artefacts: ${response.statusText}`)
    }

    return response.json()
  },

  async searchEnvironments(params) {
    const queryParams = new URLSearchParams()

    // Add query parameter
    if (params.q) queryParams.append('q', params.q)
    
    // Add limit and offset
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.offset) queryParams.append('offset', params.offset)

    const url = `${API_BASE_URL}/v1/environments${queryParams.toString() ? '?' + queryParams.toString() : ''}`

    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to search environments: ${response.statusText}`)
    }

    return response.json()
  },

  async searchTestCases(params) {
    const queryParams = new URLSearchParams()

    // Add query parameter
    if (params.q) queryParams.append('q', params.q)
    
    // Add limit and offset
    if (params.limit) queryParams.append('limit', params.limit)
    if (params.offset) queryParams.append('offset', params.offset)

    const url = `${API_BASE_URL}/v1/test-cases${queryParams.toString() ? '?' + queryParams.toString() : ''}`

    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'X-CSRF-Token': '1'
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to search test cases: ${response.statusText}`)
    }

    return response.json()
  }
}

// Stage names for different families
export const FAMILY_STAGES = {
  snap: ['edge', 'beta', 'candidate', 'stable'],
  deb: ['proposed', 'updates', ''],
  charm: ['edge', 'beta', 'candidate', 'stable'],
  image: ['pending', 'current', '']
}

// Artefact status colors
export const STATUS_COLORS = {
  APPROVED: '#0E8420',
  MARKED_AS_FAILED: '#C7162B',
  UNDECIDED: '#666'
}

export const STATUS_NAMES = {
  APPROVED: 'Approved',
  MARKED_AS_FAILED: 'Rejected',
  UNDECIDED: 'Undecided'
}
