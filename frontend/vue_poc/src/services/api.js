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
