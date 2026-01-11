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
