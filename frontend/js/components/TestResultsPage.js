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
 * Test Results Page Component
 * Displays searchable, filterable test results
 */

import { searchTestResults, searchArtefacts, searchEnvironments, searchTestCases } from '../api.js';
import { TestResultStatus } from '../models.js';
import { createElement, formatDate, getStatusClass } from '../utils/helpers.js';

let currentFilters = {
  artefactName: '',
  environment: '',
  testCase: '',
  status: '',
  sortBy: 'created_at',
  sortDirection: 'desc',
  limit: 50,
  offset: 0
};

let testResults = [];
let totalCount = 0;
let loading = false;

/**
 * Create filter controls
 */
function createFilters(onApplyFilters) {
  const container = createElement('div', {
    className: 'sidebar-section'
  });
  
  // Title
  container.appendChild(createElement('h4', {
    textContent: 'Filters'
  }));
  
  // Artefact name filter
  const artefactGroup = createElement('div', { className: 'p-form__group mt-2' });
  artefactGroup.appendChild(createElement('label', {
    className: 'p-form__label',
    textContent: 'Artefact Name',
    for: 'filter-artefact'
  }));
  const artefactInput = createElement('input', {
    type: 'text',
    id: 'filter-artefact',
    className: 'p-form__control',
    placeholder: 'Search artefacts...',
    value: currentFilters.artefactName
  }));
  artefactInput.addEventListener('input', (e) => {
    currentFilters.artefactName = e.target.value;
  });
  artefactGroup.appendChild(artefactInput);
  container.appendChild(artefactGroup);
  
  // Environment filter
  const envGroup = createElement('div', { className: 'p-form__group mt-2' });
  envGroup.appendChild(createElement('label', {
    className: 'p-form__label',
    textContent: 'Environment',
    for: 'filter-environment'
  }));
  const envInput = createElement('input', {
    type: 'text',
    id: 'filter-environment',
    className: 'p-form__control',
    placeholder: 'Search environments...',
    value: currentFilters.environment
  }));
  envInput.addEventListener('input', (e) => {
    currentFilters.environment = e.target.value;
  });
  envGroup.appendChild(envInput);
  container.appendChild(envGroup);
  
  // Test case filter
  const testCaseGroup = createElement('div', { className: 'p-form__group mt-2' });
  testCaseGroup.appendChild(createElement('label', {
    className: 'p-form__label',
    textContent: 'Test Case',
    for: 'filter-test-case'
  }));
  const testCaseInput = createElement('input', {
    type: 'text',
    id: 'filter-test-case',
    className: 'p-form__control',
    placeholder: 'Search test cases...',
    value: currentFilters.testCase
  });
  testCaseInput.addEventListener('input', (e) => {
    currentFilters.testCase = e.target.value;
  });
  testCaseGroup.appendChild(testCaseInput);
  container.appendChild(testCaseGroup);
  
  // Status filter
  const statusGroup = createElement('div', { className: 'p-form__group mt-2' });
  statusGroup.appendChild(createElement('label', {
    className: 'p-form__label',
    textContent: 'Status',
    for: 'filter-status'
  }));
  const statusSelect = createElement('select', {
    id: 'filter-status',
    className: 'p-form__control'
  });
  statusSelect.appendChild(createElement('option', { value: '', textContent: 'All' }));
  statusSelect.appendChild(createElement('option', { value: 'FAILED', textContent: 'Failed' }));
  statusSelect.appendChild(createElement('option', { value: 'PASSED', textContent: 'Passed' }));
  statusSelect.appendChild(createElement('option', { value: 'SKIPPED', textContent: 'Skipped' }));
  statusSelect.value = currentFilters.status;
  statusSelect.addEventListener('change', (e) => {
    currentFilters.status = e.target.value;
  });
  statusGroup.appendChild(statusSelect);
  container.appendChild(statusGroup);
  
  // Apply button
  const applyButton = createElement('button', {
    className: 'p-button--positive mt-2',
    textContent: 'Apply Filters'
  });
  applyButton.addEventListener('click', () => {
    currentFilters.offset = 0;
    onApplyFilters();
  });
  container.appendChild(applyButton);
  
  return container;
}

/**
 * Create test results table
 */
function createTestResultsTable(results) {
  if (results.length === 0) {
    return createElement('p', {
      className: 'text-muted',
      textContent: 'No test results found'
    });
  }
  
  const table = createElement('table', {
    className: 'p-table p-table--compact'
  });
  
  // Header
  const thead = createElement('thead');
  const headerRow = createElement('tr');
  ['Artefact', 'Test Case', 'Status', 'Track', 'Version', 'Environment', 'Test Plan', 'Created'].forEach(header => {
    headerRow.appendChild(createElement('th', { textContent: header }));
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  
  // Body
  const tbody = createElement('tbody');
  results.forEach(result => {
    const tr = createElement('tr');
    
    // Artefact
    tr.appendChild(createElement('td', {
      textContent: result.artefact.name
    }));
    
    // Test case
    tr.appendChild(createElement('td', {
      textContent: result.testResult.name
    }));
    
    // Status
    const statusCell = createElement('td');
    statusCell.appendChild(createElement('span', {
      className: `status-badge ${getStatusClass(result.testResult.status)}`,
      textContent: TestResultStatus.getName(result.testResult.status)
    }));
    tr.appendChild(statusCell);
    
    // Track
    tr.appendChild(createElement('td', {
      textContent: result.artefact.track || '-'
    }));
    
    // Version
    tr.appendChild(createElement('td', {
      textContent: result.artefact.version
    }));
    
    // Environment
    tr.appendChild(createElement('td', {
      textContent: result.testExecution.environment.name
    }));
    
    // Test plan
    tr.appendChild(createElement('td', {
      textContent: result.testExecution.testPlan
    }));
    
    // Created
    tr.appendChild(createElement('td', {
      textContent: formatDate(result.testResult.createdAt),
      className: 'text-small'
    }));
    
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  
  return table;
}

/**
 * Create the test results page
 */
export async function createTestResultsPage(state) {
  const container = createElement('div', { className: 'page-container' });
  
  // Page header
  const header = createElement('div', { className: 'page-header' });
  
  header.appendChild(createElement('h1', {
    className: 'page-title',
    textContent: 'Test Results'
  }));
  
  // Filter toggle button
  let showFilters = true;
  const filterButton = createElement('button', {
    className: 'p-button',
    textContent: '🔍 Toggle Filters'
  });
  header.appendChild(filterButton);
  
  container.appendChild(header);
  
  // Page content with sidebar and main
  const pageContent = createElement('div', { className: 'page-content' });
  
  // Filters sidebar
  const sidebar = createElement('div', { className: 'sidebar' });
  
  // Main content
  const mainContent = createElement('div', { className: 'main-content' });
  
  // Load and render results
  async function loadResults() {
    mainContent.innerHTML = '';
    mainContent.appendChild(createElement('div', {
      className: 'loading',
      textContent: 'Loading...'
    }));
    
    try {
      loading = true;
      const searchResult = await searchTestResults(currentFilters);
      testResults = searchResult.testResults;
      totalCount = searchResult.count;
      loading = false;
      
      mainContent.innerHTML = '';
      
      // Results summary
      mainContent.appendChild(createElement('p', {
        className: 'text-muted mb-2',
        textContent: `Showing ${testResults.length} of ${totalCount} results`
      }));
      
      // Table
      mainContent.appendChild(createTestResultsTable(testResults));
      
      // Load more button
      if (searchResult.hasMore) {
        const loadMoreButton = createElement('button', {
          className: 'p-button mt-2',
          textContent: 'Load More'
        });
        loadMoreButton.addEventListener('click', async () => {
          currentFilters.offset += currentFilters.limit;
          await loadResults();
        });
        mainContent.appendChild(loadMoreButton);
      }
      
    } catch (error) {
      console.error('Error loading test results:', error);
      mainContent.innerHTML = '';
      mainContent.appendChild(createElement('div', { className: 'error' }, [
        createElement('p', {}, `Error loading test results: ${error.message}`)
      ]));
    }
  }
  
  // Create filters
  const filtersElement = createFilters(loadResults);
  sidebar.appendChild(filtersElement);
  
  // Filter toggle functionality
  filterButton.addEventListener('click', () => {
    showFilters = !showFilters;
    sidebar.style.display = showFilters ? 'block' : 'none';
  });
  
  pageContent.appendChild(sidebar);
  pageContent.appendChild(mainContent);
  container.appendChild(pageContent);
  
  // Initial load
  await loadResults();
  
  return container;
}
