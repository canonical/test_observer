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
 * Artefact Page Component
 * Displays detailed information about a specific artefact
 */

import { getArtefact, getArtefactBuilds } from '../api.js';
import { ArtefactStatus, TestExecutionStatus } from '../models.js';
import { createElement, formatDate, getStatusClass } from '../utils/helpers.js';

/**
 * Create test execution row
 */
function createTestExecutionRow(testExecution) {
  const tr = createElement('tr', {});
  
  // Environment
  tr.appendChild(createElement('td', {
    textContent: testExecution.environment.name
  }));
  
  // Architecture
  tr.appendChild(createElement('td', {
    textContent: testExecution.environment.architecture
  }));
  
  // Status
  const statusCell = createElement('td', {});
  const statusBadge = createElement('span', {
    className: `status-badge ${getStatusClass(testExecution.status)}`,
    textContent: TestExecutionStatus.getName(testExecution.status)
  });
  statusCell.appendChild(statusBadge);
  tr.appendChild(statusCell);
  
  // Test Plan
  tr.appendChild(createElement('td', {
    textContent: testExecution.testPlan
  }));
  
  // Links
  const linksCell = createElement('td', {});
  if (testExecution.ciLink) {
    linksCell.appendChild(createElement('a', {
      href: testExecution.ciLink,
      target: '_blank',
      textContent: 'CI',
      className: 'mr-1'
    }));
  }
  if (testExecution.c3Link) {
    linksCell.appendChild(createElement('a', {
      href: testExecution.c3Link,
      target: '_blank',
      textContent: 'C3'
    }));
  }
  tr.appendChild(linksCell);
  
  // Created date
  tr.appendChild(createElement('td', {
    textContent: formatDate(testExecution.createdAt),
    className: 'text-small'
  }));
  
  return tr;
}

/**
 * Create artefact builds table
 */
function createBuildsTable(builds) {
  const container = createElement('div', { className: 'p-section' });
  
  container.appendChild(createElement('h3', {
    className: 'p-heading--4',
    textContent: 'Builds and Test Executions'
  }));
  
  if (builds.length === 0) {
    container.appendChild(createElement('p', {
      className: 'text-muted',
      textContent: 'No builds available'
    }));
    return container;
  }
  
  builds.forEach(build => {
    const buildSection = createElement('div', { className: 'mt-2 mb-2' });
    
    // Build header
    const buildHeader = createElement('h4', {
      className: 'p-heading--5',
      textContent: `${build.architecture}${build.revision ? ` (revision ${build.revision})` : ''}`
    });
    buildSection.appendChild(buildHeader);
    
    // Test executions table
    if (build.testExecutions.length > 0) {
      const table = createElement('table', {
        className: 'p-table p-table--compact'
      });
      
      const thead = createElement('thead', {});
      const headerRow = createElement('tr', {});
      ['Environment', 'Architecture', 'Status', 'Test Plan', 'Links', 'Created'].forEach(header => {
        headerRow.appendChild(createElement('th', { textContent: header }));
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);
      
      const tbody = createElement('tbody', {});
      build.testExecutions.forEach(te => {
        tbody.appendChild(createTestExecutionRow(te));
      });
      table.appendChild(tbody);
      
      buildSection.appendChild(table);
    } else {
      buildSection.appendChild(createElement('p', {
        className: 'text-muted text-small',
        textContent: 'No test executions'
      }));
    }
    
    container.appendChild(buildSection);
  });
  
  return container;
}

/**
 * Create the artefact page
 */
export async function createArtefactPage(state, artefactId) {
  const container = createElement('div', { className: 'p-strip is-shallow' });
  
  try {
    // Fetch artefact details
    const artefact = await getArtefact(artefactId);
    const builds = await getArtefactBuilds(artefactId);
    
    // Page header with artefact info
    const header = createElement('div', { className: 'row' }, [
      createElement('div', { className: 'col-12' }, [
        createElement('h1', {
          className: 'p-heading--2',
          textContent: artefact.name
        }),
        createElement('p', {
          className: 'p-heading--5',
          textContent: `Version: ${artefact.version}`
        })
      ])
    ]);
    container.appendChild(header);
    
    // Artefact details card
    const detailsCard = createElement('div', { className: 'p-card mt-2' });
    const detailsContent = createElement('div', { className: 'p-card__content' });
    
    // Status
    const statusRow = createElement('div', { className: 'flex-between mb-2' }, [
      createElement('strong', { textContent: 'Status:' }),
      createElement('span', {
        className: `status-badge ${getStatusClass(artefact.status)}`,
        textContent: ArtefactStatus.getName(artefact.status)
      })
    ]);
    detailsContent.appendChild(statusRow);
    
    // Stage
    if (artefact.stage) {
      detailsContent.appendChild(createElement('p', {}, [
        createElement('strong', { textContent: 'Stage: ' }),
        document.createTextNode(artefact.stage)
      ]));
    }
    
    // Add other fields if present
    const fields = [
      ['Family', artefact.family],
      ['Track', artefact.track],
      ['Store', artefact.store],
      ['Branch', artefact.branch],
      ['Series', artefact.series],
      ['Repo', artefact.repo],
      ['Source', artefact.source],
      ['OS', artefact.os],
      ['Release', artefact.release],
      ['Owner', artefact.owner]
    ];
    
    fields.forEach(([label, value]) => {
      if (value) {
        detailsContent.appendChild(createElement('p', {}, [
          createElement('strong', { textContent: `${label}: ` }),
          document.createTextNode(value)
        ]));
      }
    });
    
    // Comment
    if (artefact.comment) {
      detailsContent.appendChild(createElement('div', { className: 'mt-2' }, [
        createElement('strong', { textContent: 'Comment:' }),
        createElement('p', {
          className: 'text-small',
          textContent: artefact.comment
        })
      ]));
    }
    
    // Due date
    if (artefact.dueDate) {
      detailsContent.appendChild(createElement('p', {
        className: 'mt-2'
      }, [
        createElement('strong', { textContent: 'Due Date: ' }),
        document.createTextNode(artefact.dueDateString)
      ]));
    }
    
    // Review progress
    detailsContent.appendChild(createElement('p', {
      className: 'mt-2'
    }, [
      createElement('strong', { textContent: 'Reviews: ' }),
      document.createTextNode(`${artefact.completedEnvironmentReviewsCount}/${artefact.allEnvironmentReviewsCount} completed`)
    ]));
    
    detailsCard.appendChild(detailsContent);
    container.appendChild(detailsCard);
    
    // Builds and test executions
    container.appendChild(createBuildsTable(builds));
    
  } catch (error) {
    console.error('Error loading artefact:', error);
    container.appendChild(createElement('div', { className: 'error' }, [
      createElement('p', {}, `Error loading artefact: ${error.message}`)
    ]));
  }
  
  return container;
}
