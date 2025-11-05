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
 * Dashboard Page Component
 * Displays artefacts grouped by stage (beta, candidate, stable, edge)
 */

import { getFamilyArtefacts } from '../api.js';
import { ArtefactStatus, StageName } from '../models.js';
import { createElement, getStatusClass, sortBy } from '../utils/helpers.js';

/**
 * Create an artefact card
 */
function createArtefactCard(artefact, family) {
  const card = createElement('div', {
    className: 'p-card u-no-margin clickable-row',
    style: 'width: 320px; min-height: 182px;'
  });
  
  // Card content
  const content = createElement('div', { className: 'p-card__content' }, [
    createElement('h4', {
      className: 'p-heading--5',
      textContent: artefact.name
    }),
    createElement('p', {
      className: 'text-small text-muted',
      textContent: `version: ${artefact.version}`
    })
  ]);
  
  // Add optional fields if present
  const optionalFields = [];
  if (artefact.track) optionalFields.push(['track', artefact.track]);
  if (artefact.store) optionalFields.push(['store', artefact.store]);
  if (artefact.branch) optionalFields.push(['branch', artefact.branch]);
  if (artefact.series) optionalFields.push(['series', artefact.series]);
  if (artefact.repo) optionalFields.push(['repo', artefact.repo]);
  if (artefact.source) optionalFields.push(['source', artefact.source]);
  if (artefact.os) optionalFields.push(['os', artefact.os]);
  if (artefact.release) optionalFields.push(['release', artefact.release]);
  if (artefact.owner) optionalFields.push(['owner', artefact.owner]);
  
  optionalFields.forEach(([label, value]) => {
    content.appendChild(createElement('p', {
      className: 'text-small',
      textContent: `${label}: ${value}`
    }));
  });
  
  // Status and metadata row
  const metadataRow = createElement('div', {
    className: 'flex-between mt-2'
  });
  
  const statusBadge = createElement('span', {
    className: `status-badge ${getStatusClass(artefact.status)}`,
    textContent: ArtefactStatus.getName(artefact.status)
  });
  metadataRow.appendChild(statusBadge);
  
  // Due date if present
  if (artefact.dueDateString) {
    const dueDateBadge = createElement('span', {
      className: 'status-badge status-badge--rejected text-small',
      textContent: `Due ${artefact.dueDateString}`
    });
    metadataRow.appendChild(dueDateBadge);
  }
  
  // Review count
  const reviewInfo = createElement('span', {
    className: 'text-small text-muted',
    textContent: `${artefact.completedEnvironmentReviewsCount}/${artefact.allEnvironmentReviewsCount} reviews`
  });
  metadataRow.appendChild(reviewInfo);
  
  content.appendChild(metadataRow);
  card.appendChild(content);
  
  // Make card clickable
  card.addEventListener('click', () => {
    window.location.hash = `#/${family}/${artefact.id}`;
  });
  
  return card;
}

/**
 * Create a stage column
 */
function createStageColumn(stageName, artefacts, family) {
  const column = createElement('div', {
    className: 'p-section'
  });
  
  // Column header
  const header = createElement('h3', {
    className: 'p-heading--4',
    textContent: stageName.charAt(0).toUpperCase() + stageName.slice(1)
  });
  column.appendChild(header);
  
  // Artefact cards
  const cardsContainer = createElement('div', {
    className: 'u-sv3',
    style: 'display: flex; flex-direction: column; gap: 1rem;'
  });
  
  if (artefacts.length === 0) {
    cardsContainer.appendChild(createElement('p', {
      className: 'text-muted',
      textContent: 'No artefacts'
    }));
  } else {
    artefacts.forEach(artefact => {
      cardsContainer.appendChild(createArtefactCard(artefact, family));
    });
  }
  
  column.appendChild(cardsContainer);
  return column;
}

/**
 * Create the dashboard page
 */
export async function createDashboardPage(state, family) {
  const container = createElement('div', { className: 'p-strip is-shallow' });
  
  // Page header
  const header = createElement('div', { className: 'row' }, [
    createElement('div', { className: 'col-12' }, [
      createElement('h1', {
        className: 'p-heading--2',
        textContent: `${family.charAt(0).toUpperCase() + family.slice(1)} Update Verification`
      })
    ])
  ]);
  container.appendChild(header);
  
  // Fetch artefacts
  try {
    const artefactsMap = await getFamilyArtefacts(family);
    const artefacts = Object.values(artefactsMap);
    
    // Group by stage
    const stages = {
      beta: [],
      candidate: [],
      stable: [],
      edge: []
    };
    
    artefacts.forEach(artefact => {
      const stage = artefact.stage.toLowerCase();
      if (stages[stage]) {
        stages[stage].push(artefact);
      }
    });
    
    // Sort each stage by creation date (most recent first)
    Object.keys(stages).forEach(stage => {
      stages[stage] = sortBy(stages[stage], a => a.id, false);
    });
    
    // Create columns layout
    const columnsRow = createElement('div', {
      className: 'row',
      style: 'display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2rem;'
    });
    
    // Add stage columns
    ['beta', 'candidate', 'stable', 'edge'].forEach(stageName => {
      const stageArtefacts = stages[stageName] || [];
      columnsRow.appendChild(createStageColumn(stageName, stageArtefacts, family));
    });
    
    container.appendChild(columnsRow);
    
  } catch (error) {
    console.error('Error loading artefacts:', error);
    container.appendChild(createElement('div', { className: 'error' }, [
      createElement('p', {}, `Error loading artefacts: ${error.message}`)
    ]));
  }
  
  return container;
}
