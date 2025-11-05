// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/**
 * Main Application Entry Point
 * Handles routing, state management, and page rendering
 */

import { FamilyName } from './models.js';
import { createElement } from './utils/helpers.js';
import { createDashboardPage } from './components/DashboardPage.js';
import { createArtefactPage } from './components/ArtefactPage.js';
import { createTestResultsPage } from './components/TestResultsPage.js';
import { createIssuesPage } from './components/IssuesPage.js';
import { createIssuePage } from './components/IssuePage.js';

// Application state
const state = {
  currentRoute: null,
  currentFamily: null,
  artefactId: null,
  filters: {
    searchQuery: '',
    sortBy: null,
    sortDirection: 'asc'
  }
};

// Routes
const Routes = {
  SNAPS: '/snaps',
  DEBS: '/debs',
  CHARMS: '/charms',
  IMAGES: '/images',
  TEST_RESULTS: '/test-results',
  ISSUES: '/issues'
};

/**
 * Create the navigation bar
 */
function createNavbar() {
  const currentPath = window.location.hash.slice(1) || Routes.SNAPS;
  
  const navLinks = [
    { title: 'Snap Testing', route: Routes.SNAPS },
    { title: 'Deb Testing', route: Routes.DEBS },
    { title: 'Charm Testing', route: Routes.CHARMS },
    { title: 'Image Testing', route: Routes.IMAGES },
    { title: 'Test Results', route: Routes.TEST_RESULTS },
    { title: 'Issues', route: Routes.ISSUES }
  ];
  
  const navItems = navLinks.map(({ title, route }) => {
    const isActive = currentPath.startsWith(route);
    return createElement('li', {
      className: `p-navigation__item ${isActive ? 'is-selected' : ''}`
    }, [
      createElement('a', {
        className: 'p-navigation__link',
        href: `#${route}`,
        textContent: title
      })
    ]);
  });
  
  const helpMenu = createElement('li', { className: 'p-navigation__item' }, [
    createElement('a', {
      className: 'p-navigation__link',
      href: '#',
      textContent: 'Help',
      onclick: (e) => {
        e.preventDefault();
        // Simple dropdown implementation - could be enhanced
      }
    })
  ]);
  
  const nav = createElement('nav', { className: 'p-navigation is-dark' }, [
    createElement('div', { className: 'p-navigation__row' }, [
      createElement('div', { className: 'p-navigation__banner' }, [
        createElement('div', { className: 'p-navigation__logo' }, [
          createElement('a', {
            className: 'p-navigation__link',
            href: '#/snaps',
            textContent: 'Test Observer'
          })
        ])
      ]),
      createElement('ul', { className: 'p-navigation__items' }, navItems),
      createElement('ul', { className: 'p-navigation__items' }, [helpMenu])
    ])
  ]);
  
  return nav;
}

/**
 * Parse the current route from the URL hash
 */
function parseRoute() {
  const hash = window.location.hash.slice(1) || Routes.SNAPS;
  const parts = hash.split('/').filter(Boolean);
  
  let route = {
    path: hash,
    family: null,
    artefactId: null,
    issueId: null,
    page: 'dashboard'
  };
  
  // Determine family from first segment
  if (parts.length > 0) {
    const firstSegment = '/' + parts[0];
    switch (firstSegment) {
      case Routes.SNAPS:
        route.family = FamilyName.SNAP;
        break;
      case Routes.DEBS:
        route.family = FamilyName.DEB;
        break;
      case Routes.CHARMS:
        route.family = FamilyName.CHARM;
        break;
      case Routes.IMAGES:
        route.family = FamilyName.IMAGE;
        break;
      case Routes.TEST_RESULTS:
        route.page = 'test-results';
        break;
      case Routes.ISSUES:
        route.page = 'issues';
        break;
    }
  }
  
  // Check for artefact ID in second segment
  if (parts.length > 1 && route.family) {
    const id = parseInt(parts[1], 10);
    if (!isNaN(id)) {
      route.artefactId = id;
      route.page = 'artefact';
    }
  }
  
  // Check for issue ID in second segment
  if (parts.length > 1 && parts[0] === 'issues') {
    const id = parseInt(parts[1], 10);
    if (!isNaN(id)) {
      route.issueId = id;
      route.page = 'issue';
    }
  }
  
  return route;
}

/**
 * Render the current page based on route
 */
async function render() {
  const route = parseRoute();
  state.currentRoute = route;
  state.currentFamily = route.family;
  state.artefactId = route.artefactId;
  
  const appContainer = document.getElementById('app');
  appContainer.innerHTML = '';
  
  // Create navigation
  const nav = createNavbar();
  appContainer.appendChild(nav);
  
  // Create main content container
  const mainContainer = createElement('main', {
    className: 'u-fixed-width'
  });
  
  // Create loading indicator
  const loading = createElement('div', {
    className: 'loading',
    textContent: 'Loading...'
  });
  mainContainer.appendChild(loading);
  appContainer.appendChild(mainContainer);
  
  try {
    let pageContent;
    
    // Route to appropriate page
    if (route.page === 'artefact') {
      pageContent = await createArtefactPage(state, route.artefactId);
    } else if (route.page === 'test-results') {
      pageContent = await createTestResultsPage(state);
    } else if (route.page === 'issues') {
      pageContent = await createIssuesPage(state);
    } else if (route.page === 'issue') {
      pageContent = await createIssuePage(state, route.issueId);
    } else if (route.family) {
      // Dashboard for specific family
      pageContent = await createDashboardPage(state, route.family);
    } else {
      // Default redirect to snaps
      window.location.hash = Routes.SNAPS;
      return;
    }
    
    // Replace loading with actual content
    mainContainer.innerHTML = '';
    mainContainer.appendChild(pageContent);
    
  } catch (error) {
    console.error('Error rendering page:', error);
    mainContainer.innerHTML = '';
    const errorDiv = createElement('div', { className: 'error' }, [
      createElement('h3', {}, 'Error Loading Page'),
      createElement('p', {}, error.message || 'An unexpected error occurred')
    ]);
    mainContainer.appendChild(errorDiv);
  }
}

/**
 * Initialize the application
 */
function init() {
  // Set default route if none present
  if (!window.location.hash) {
    window.location.hash = Routes.SNAPS;
  }
  
  // Listen for hash changes
  window.addEventListener('hashchange', render);
  
  // Initial render
  render();
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export for use in other modules
export { state, Routes, render };
