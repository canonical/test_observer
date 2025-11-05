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
 * Issues Page Component
 * Displays linked external issues
 */

import { getIssues, createIssue, deleteIssue } from '../api.js';
import { IssueStatus, IssueSource } from '../models.js';
import { createElement, getStatusClass } from '../utils/helpers.js';
import { showConfirm, showAlert } from '../utils/modal.js';

let issues = [];
let filteredIssues = [];
let searchQuery = '';

/**
 * Create filter sidebar
 */
function createFiltersSidebar(onFilterChange) {
  const container = createElement('div', {
    className: 'p-card',
    style: 'width: 250px;'
  });
  
  const content = createElement('div', { className: 'p-card__content' });
  
  content.appendChild(createElement('h4', {
    className: 'p-heading--5',
    textContent: 'Search'
  }));
  
  // Search input
  const searchInput = createElement('input', {
    type: 'text',
    className: 'p-form__control',
    placeholder: 'Search issues...',
    value: searchQuery
  });
  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase();
    onFilterChange();
  });
  content.appendChild(searchInput);
  
  container.appendChild(content);
  return container;
}

/**
 * Create add issue form
 */
function createAddIssueForm(onIssueAdded) {
  const container = createElement('div', {
    className: 'p-card mt-2'
  });
  
  const content = createElement('div', { className: 'p-card__content' });
  
  content.appendChild(createElement('h4', {
    className: 'p-heading--5',
    textContent: 'Add New Issue'
  }));
  
  // URL input
  const urlGroup = createElement('div', { className: 'p-form__group mt-2' });
  urlGroup.appendChild(createElement('label', {
    className: 'p-form__label',
    textContent: 'Issue URL',
    for: 'issue-url'
  }));
  const urlInput = createElement('input', {
    type: 'url',
    id: 'issue-url',
    className: 'p-form__control',
    placeholder: 'https://github.com/...'
  });
  urlGroup.appendChild(urlInput);
  content.appendChild(urlGroup);
  
  // Title input
  const titleGroup = createElement('div', { className: 'p-form__group mt-2' });
  titleGroup.appendChild(createElement('label', {
    className: 'p-form__label',
    textContent: 'Title (optional)',
    for: 'issue-title'
  }));
  const titleInput = createElement('input', {
    type: 'text',
    id: 'issue-title',
    className: 'p-form__control',
    placeholder: 'Issue title'
  });
  titleGroup.appendChild(titleInput);
  content.appendChild(titleGroup);
  
  // Add button
  const addButton = createElement('button', {
    className: 'p-button--positive mt-2',
    textContent: 'Add Issue'
  });
  
  addButton.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    const title = titleInput.value.trim() || null;
    
    if (!url) {
      await showAlert('Missing URL', 'Please enter an issue URL', { isError: true });
      return;
    }
    
    try {
      addButton.disabled = true;
      addButton.textContent = 'Adding...';
      
      await createIssue(url, title);
      
      urlInput.value = '';
      titleInput.value = '';
      
      await onIssueAdded();
      
    } catch (error) {
      console.error('Error adding issue:', error);
      await showAlert('Error', `Error adding issue: ${error.message}`, { isError: true });
    } finally {
      addButton.disabled = false;
      addButton.textContent = 'Add Issue';
    }
  });
  content.appendChild(addButton);
  
  container.appendChild(content);
  return container;
}

/**
 * Create issues table
 */
function createIssuesTable(issuesToDisplay, onDelete) {
  if (issuesToDisplay.length === 0) {
    return createElement('p', {
      className: 'text-muted',
      textContent: 'No issues found'
    });
  }
  
  const table = createElement('table', {
    className: 'p-table'
  });
  
  // Header
  const thead = createElement('thead');
  const headerRow = createElement('tr');
  ['Source', 'Project', 'Key', 'Title', 'Status', 'Attachment Rules', 'Actions'].forEach(header => {
    headerRow.appendChild(createElement('th', { textContent: header }));
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  
  // Body
  const tbody = createElement('tbody');
  issuesToDisplay.forEach(issue => {
    const tr = createElement('tr', { className: 'clickable-row' });
    
    // Click to view issue details
    tr.addEventListener('click', (e) => {
      if (!e.target.closest('button')) {
        window.location.hash = `#/issues/${issue.id}`;
      }
    });
    
    // Source
    tr.appendChild(createElement('td', {
      textContent: issue.source.toUpperCase()
    }));
    
    // Project
    tr.appendChild(createElement('td', {
      textContent: issue.project
    }));
    
    // Key
    tr.appendChild(createElement('td', {
      textContent: issue.key
    }));
    
    // Title
    const titleCell = createElement('td');
    titleCell.appendChild(createElement('a', {
      href: issue.url,
      target: '_blank',
      textContent: issue.title,
      onclick: (e) => e.stopPropagation()
    }));
    tr.appendChild(titleCell);
    
    // Status
    const statusCell = createElement('td');
    statusCell.appendChild(createElement('span', {
      className: `status-badge ${issue.status === 'open' ? 'status-badge--in-progress' : 'status-badge--passed'}`,
      textContent: IssueStatus.getName(issue.status)
    }));
    tr.appendChild(statusCell);
    
    // Attachment rules count
    tr.appendChild(createElement('td', {
      textContent: issue.attachmentRules.length.toString()
    }));
    
    // Actions
    const actionsCell = createElement('td');
    const deleteButton = createElement('button', {
      className: 'p-button--base is-small is-dense',
      textContent: 'Delete'
    });
    deleteButton.addEventListener('click', async (e) => {
      e.stopPropagation();
      const confirmed = await showConfirm(
        'Delete Issue',
        `Are you sure you want to delete issue ${issue.key}? This action cannot be undone.`,
        { confirmText: 'Delete', isDangerous: true }
      );
      if (confirmed) {
        await onDelete(issue.id);
      }
    });
    actionsCell.appendChild(deleteButton);
    tr.appendChild(actionsCell);
    
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  
  return table;
}

/**
 * Create the issues page
 */
export async function createIssuesPage(state) {
  const container = createElement('div', { className: 'p-strip is-shallow' });
  
  // Page header
  const headerRow = createElement('div', { className: 'row' });
  const headerCol = createElement('div', { className: 'col-12' });
  const headerFlex = createElement('div', { className: 'flex-between' });
  
  headerFlex.appendChild(createElement('h1', {
    className: 'p-heading--2',
    textContent: 'Linked External Issues'
  }));
  
  // Filter toggle button
  let showFilters = true;
  const filterButton = createElement('button', {
    className: 'p-button',
    textContent: '🔍 Toggle Filters'
  });
  headerFlex.appendChild(filterButton);
  
  headerCol.appendChild(headerFlex);
  headerRow.appendChild(headerCol);
  container.appendChild(headerRow);
  
  // Main content
  const contentRow = createElement('div', { className: 'row mt-2' });
  
  // Filters sidebar (col-3)
  const filtersCol = createElement('div', { className: 'col-3' });
  
  // Issues table area (col-9)
  const issuesCol = createElement('div', { className: 'col-9' });
  
  // Filter function
  function applyFilters() {
    if (searchQuery) {
      filteredIssues = issues.filter(issue => 
        issue.title.toLowerCase().includes(searchQuery) ||
        issue.key.toLowerCase().includes(searchQuery) ||
        issue.project.toLowerCase().includes(searchQuery)
      );
    } else {
      filteredIssues = [...issues];
    }
    renderIssuesTable();
  }
  
  // Render issues table
  function renderIssuesTable() {
    issuesCol.innerHTML = '';
    issuesCol.appendChild(createElement('p', {
      className: 'text-muted mb-2',
      textContent: `Showing ${filteredIssues.length} of ${issues.length} issues`
    }));
    issuesCol.appendChild(createIssuesTable(filteredIssues, async (issueId) => {
      try {
        await deleteIssue(issueId);
        await loadIssues();
      } catch (error) {
        console.error('Error deleting issue:', error);
        await showAlert('Error', `Error deleting issue: ${error.message}`, { isError: true });
      }
    }));
  }
  
  // Load issues
  async function loadIssues() {
    issuesCol.innerHTML = '';
    issuesCol.appendChild(createElement('div', {
      className: 'loading',
      textContent: 'Loading...'
    }));
    
    try {
      issues = await getIssues();
      applyFilters();
    } catch (error) {
      console.error('Error loading issues:', error);
      issuesCol.innerHTML = '';
      issuesCol.appendChild(createElement('div', { className: 'error' }, [
        createElement('p', {}, `Error loading issues: ${error.message}`)
      ]));
    }
  }
  
  // Create filters
  filtersCol.appendChild(createFiltersSidebar(applyFilters));
  filtersCol.appendChild(createAddIssueForm(loadIssues));
  
  // Filter toggle functionality
  filterButton.addEventListener('click', () => {
    showFilters = !showFilters;
    filtersCol.style.display = showFilters ? 'block' : 'none';
  });
  
  contentRow.appendChild(filtersCol);
  contentRow.appendChild(issuesCol);
  container.appendChild(contentRow);
  
  // Initial load
  await loadIssues();
  
  return container;
}
