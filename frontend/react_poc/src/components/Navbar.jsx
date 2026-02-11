import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import './Navbar.css'

export default function Navbar() {
  const [user, setUser] = useState(null)

  const apiUrl = window.location.origin.replace(':30001', ':30000')
  const reactAppUrl = window.location.origin + '/react_poc/'
  const logoutUrl = `${apiUrl}/v1/auth/saml/logout?return_to=${encodeURIComponent(reactAppUrl)}`

  const login = () => {
    const loginUrl = `${apiUrl}/v1/auth/saml/login?return_to=${encodeURIComponent(reactAppUrl)}`
    window.location.href = loginUrl
  }

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await fetch(`${apiUrl}/v1/users/me`, {
          credentials: 'include',
          headers: {
            'X-CSRF-Token': '1'
          }
        })

        if (response.ok) {
          const data = await response.json()
          setUser(data || null)
        } else {
          setUser(null)
        }
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        setUser(null)
      }
    }

    fetchCurrentUser()
  }, [apiUrl])

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <div className="navbar-logo">
          <img src="/canonical.png" alt="Canonical" />
        </div>

        <div className="navbar-links">
          <NavLink to="/snaps" className="nav-link">Snap Testing</NavLink>
          <NavLink to="/debs" className="nav-link">Deb Testing</NavLink>
          <NavLink to="/charms" className="nav-link">Charm Testing</NavLink>
          <NavLink to="/images" className="nav-link">Image Testing</NavLink>

          <div className="spacer"></div>

          <NavLink to="/test-results" className="nav-link">Search</NavLink>
          <NavLink to="/issues" className="nav-link">Issues</NavLink>

          <div className="dropdown">
            <button className="nav-button dropdown-toggle">Help</button>
            <div className="dropdown-menu">
              <a href="https://canonical-test-observer.readthedocs-hosted.com/en/latest/" target="_blank" rel="noreferrer" className="dropdown-item">Docs</a>
              <a href="https://github.com/canonical/test_observer/issues" target="_blank" rel="noreferrer" className="dropdown-item">Feedback</a>
              <a href="https://github.com/canonical/test_observer" target="_blank" rel="noreferrer" className="dropdown-item">Source Code</a>
            </div>
          </div>

          {user ? (
            <div className="dropdown">
              <button className="nav-button dropdown-toggle">{user.name}</button>
              <div className="dropdown-menu">
                <a href={logoutUrl} className="dropdown-item">Log out</a>
              </div>
            </div>
          ) : (
            <button onClick={login} className="nav-button">Log in</button>
          )}
        </div>
      </div>
    </nav>
  )
}
