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
 * Issue Page Component
 * Displays detailed information about a specific issue
 */

import { getIssue } from '../api.js';
import { IssueStatus } from '../models.js';
import { createElement, getStatusClass } from '../utils/helpers.js';

/**
 * Create issue header
 */
function createIssueHeader(issue) {
  const header = createElement('div', { className: 'p-card' });
  const content = createElement('div', { className: 'p-card__content' });
  
  // Title row
  const titleRow = createElement('div', { className: 'flex-between mb-2' });
  titleRow.appendChild(createElement('h2', {
    className: 'p-heading--3',
    textContent: `${issue.key}: ${issue.title}`
  }));
  
  const statusBadge = createElement('span', {
    className: `status-badge ${issue.status === 'open' ? 'status-badge--in-progress' : 'status-badge--passed'}`,
    textContent: IssueStatus.getName(issue.status)
  });
  titleRow.appendChild(statusBadge);
  content.appendChild(titleRow);
  
  // Details
  content.appendChild(createElement('p', {}, [
    createElement('strong', { textContent: 'Source: ' }),
    document.createTextNode(issue.source.toUpperCase())
  ]));
  
  content.appendChild(createElement('p', {}, [
    createElement('strong', { textContent: 'Project: ' }),
    document.createTextNode(issue.project)
  ]));
  
  content.appendChild(createElement('p', {}, [
    createElement('strong', { textContent: 'URL: ' }),
    createElement('a', {
      href: issue.url,
      target: '_blank',
      textContent: issue.url
    })
  ]));
  
  header.appendChild(content);
  return header;
}

/**
 * Create attachment rules section
 */
function createAttachmentRulesSection(attachmentRules) {
  const section = createElement('div', { className: 'p-card mt-2' });
  const content = createElement('div', { className: 'p-card__content' });
  
  content.appendChild(createElement('h3', {
    className: 'p-heading--4',
    textContent: 'Attachment Rules'
  }));
  
  if (attachmentRules.length === 0) {
    content.appendChild(createElement('p', {
      className: 'text-muted',
      textContent: 'No attachment rules defined'
    }));
  } else {
    const table = createElement('table', {
      className: 'p-table p-table--compact mt-2'
    });
    
    // Header
    const thead = createElement('thead');
    const headerRow = createElement('tr');
    ['ID', 'Test Name', 'Template ID'].forEach(header => {
      headerRow.appendChild(createElement('th', { textContent: header }));
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Body
    const tbody = createElement('tbody');
    attachmentRules.forEach(rule => {
      const tr = createElement('tr');
      
      tr.appendChild(createElement('td', {
        textContent: rule.id.toString()
      }));
      
      tr.appendChild(createElement('td', {
        textContent: rule.testName || '-'
      }));
      
      tr.appendChild(createElement('td', {
        textContent: rule.templateId || '-'
      }));
      
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    content.appendChild(table);
  }
  
  section.appendChild(content);
  return section;
}

/**
 * Create test results section
 */
function createTestResultsSection(issue) {
  const section = createElement('div', { className: 'p-card mt-2' });
  const content = createElement('div', { className: 'p-card__content' });
  
  content.appendChild(createElement('h3', {
    className: 'p-heading--4',
    textContent: 'Related Test Results'
  }));
  
  content.appendChild(createElement('p', {
    className: 'text-muted',
    textContent: 'Test results attached to this issue will appear here. Use the Test Results page to attach test results to this issue.'
  }));
  
  // Button to go to test results
  const button = createElement('button', {
    className: 'p-button mt-2',
    textContent: 'View Test Results'
  });
  button.addEventListener('click', () => {
    window.location.hash = '#/test-results';
  });
  content.appendChild(button);
  
  section.appendChild(content);
  return section;
}

/**
 * Create the issue page
 */
export async function createIssuePage(state, issueId) {
  const container = createElement('div', { className: 'p-strip is-shallow' });
  
  try {
    // Fetch issue details
    const issue = await getIssue(issueId);
    
    // Back button
    const backButton = createElement('button', {
      className: 'p-button--base mb-2',
      textContent: '← Back to Issues'
    });
    backButton.addEventListener('click', () => {
      window.location.hash = '#/issues';
    });
    container.appendChild(backButton);
    
    // Issue header
    container.appendChild(createIssueHeader(issue));
    
    // Attachment rules section
    container.appendChild(createAttachmentRulesSection(issue.attachmentRules));
    
    // Test results section
    container.appendChild(createTestResultsSection(issue));
    
  } catch (error) {
    console.error('Error loading issue:', error);
    container.appendChild(createElement('div', { className: 'error' }, [
      createElement('p', {}, `Error loading issue: ${error.message}`)
    ]));
  }
  
  return container;
}
