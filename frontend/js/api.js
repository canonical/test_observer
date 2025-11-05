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
 * API Repository - handles all data fetching
 * Translated from lib/repositories/api_repository.dart
 */

import {
  Artefact,
  ArtefactBuild,
  ArtefactVersion,
  TestResult,
  TestEvent,
  RerunRequest,
  TestIssue,
  EnvironmentIssue,
  EnvironmentReview
} from './models.js';

// Get base API URL from window or default
const API_BASE_URL = window.testObserverAPIBaseURI || 'http://localhost:30000/';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  };
  
  const response = await fetch(url, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    const error = new Error(`API Error: ${response.status} ${response.statusText}`);
    error.response = response;
    throw error;
  }
  
  return response.json();
}

/**
 * Get all artefacts for a specific family
 * @param {string} family - Family name (snap, deb, charm, image)
 * @returns {Promise<Object>} Map of artefact ID to Artefact objects
 */
export async function getFamilyArtefacts(family) {
  const data = await apiFetch(`v1/artefacts?family=${family}`);
  const artefacts = {};
  for (const json of data) {
    artefacts[json.id] = new Artefact(json);
  }
  return artefacts;
}

/**
 * Change artefact status
 * @param {number} artefactId - Artefact ID
 * @param {string} newStatus - New status value
 * @returns {Promise<Artefact>}
 */
export async function changeArtefactStatus(artefactId, newStatus) {
  const data = await apiFetch(`v1/artefacts/${artefactId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status: newStatus })
  });
  return new Artefact(data);
}

/**
 * Change artefact comment
 * @param {number} artefactId - Artefact ID
 * @param {string} comment - New comment
 * @returns {Promise<Artefact>}
 */
export async function changeArtefactComment(artefactId, comment) {
  const data = await apiFetch(`v1/artefacts/${artefactId}`, {
    method: 'PATCH',
    body: JSON.stringify({ comment })
  });
  return new Artefact(data);
}

/**
 * Get artefact builds
 * @param {number} artefactId - Artefact ID
 * @returns {Promise<ArtefactBuild[]>}
 */
export async function getArtefactBuilds(artefactId) {
  const data = await apiFetch(`v1/artefacts/${artefactId}/builds`);
  return data.map(json => new ArtefactBuild(json));
}

/**
 * Get test execution results
 * @param {number} testExecutionId - Test Execution ID
 * @returns {Promise<TestResult[]>}
 */
export async function getTestExecutionResults(testExecutionId) {
  const data = await apiFetch(`v1/test-executions/${testExecutionId}/test-results`);
  return data.map(json => new TestResult(json));
}

/**
 * Get test execution events
 * @param {number} testExecutionId - Test Execution ID
 * @returns {Promise<TestEvent[]>}
 */
export async function getTestExecutionEvents(testExecutionId) {
  const data = await apiFetch(`v1/test-executions/${testExecutionId}/status_update`);
  return data.map(json => new TestEvent(json));
}

/**
 * Request test execution reruns
 * @param {Set<number>} testExecutionIds - Set of test execution IDs
 * @returns {Promise<RerunRequest[]>}
 */
export async function rerunTestExecutions(testExecutionIds) {
  const data = await apiFetch('v1/test-executions/reruns', {
    method: 'POST',
    body: JSON.stringify({ test_execution_ids: Array.from(testExecutionIds) })
  });
  return data.map(json => new RerunRequest(json));
}

/**
 * Get all test issues
 * @returns {Promise<TestIssue[]>}
 */
export async function getTestIssues() {
  const data = await apiFetch('v1/test-cases/reported-issues');
  return data.map(json => new TestIssue(json));
}

/**
 * Update a test issue
 * @param {TestIssue} issue - Test issue to update
 * @returns {Promise<TestIssue>}
 */
export async function updateTestIssue(issue) {
  const data = await apiFetch(`v1/test-cases/reported-issues/${issue.id}`, {
    method: 'PUT',
    body: JSON.stringify(issue.toJson())
  });
  return new TestIssue(data);
}

/**
 * Create a new test issue
 * @param {string} url - Issue URL
 * @param {string} description - Issue description
 * @param {string|null} caseName - Test case name
 * @param {string|null} templateId - Template ID
 * @returns {Promise<TestIssue>}
 */
export async function createTestIssue(url, description, caseName = null, templateId = null) {
  const body = { url, description };
  if (caseName !== null) body.case_name = caseName;
  if (templateId !== null) body.template_id = templateId;
  
  const data = await apiFetch('v1/test-cases/reported-issues', {
    method: 'POST',
    body: JSON.stringify(body)
  });
  return new TestIssue(data);
}

/**
 * Delete a test issue
 * @param {number} issueId - Issue ID
 * @returns {Promise<void>}
 */
export async function deleteTestIssue(issueId) {
  await apiFetch(`v1/test-cases/reported-issues/${issueId}`, {
    method: 'DELETE'
  });
}

/**
 * Get a single artefact
 * @param {number} artefactId - Artefact ID
 * @returns {Promise<Artefact>}
 */
export async function getArtefact(artefactId) {
  const data = await apiFetch(`v1/artefacts/${artefactId}`);
  return new Artefact(data);
}

/**
 * Get artefact versions
 * @param {number} artefactId - Artefact ID
 * @returns {Promise<ArtefactVersion[]>}
 */
export async function getArtefactVersions(artefactId) {
  const data = await apiFetch(`v1/artefacts/${artefactId}/versions`);
  return data.map(json => new ArtefactVersion(json));
}

/**
 * Get all environment issues
 * @returns {Promise<EnvironmentIssue[]>}
 */
export async function getEnvironmentIssues() {
  const data = await apiFetch('v1/environments/reported-issues');
  return data.map(json => new EnvironmentIssue(json));
}

/**
 * Create environment issue
 * @param {string} url - Issue URL
 * @param {string} description - Issue description
 * @param {string} environmentName - Environment name
 * @param {boolean} isConfirmed - Whether issue is confirmed
 * @returns {Promise<EnvironmentIssue>}
 */
export async function createEnvironmentIssue(url, description, environmentName, isConfirmed) {
  const data = await apiFetch('v1/environments/reported-issues', {
    method: 'POST',
    body: JSON.stringify({
      url: url.length === 0 ? null : url,
      description,
      environment_name: environmentName,
      is_confirmed: isConfirmed
    })
  });
  return new EnvironmentIssue(data);
}

/**
 * Update environment issue
 * @param {EnvironmentIssue} issue - Issue to update
 * @returns {Promise<EnvironmentIssue>}
 */
export async function updateEnvironmentIssue(issue) {
  const data = await apiFetch(`v1/environments/reported-issues/${issue.id}`, {
    method: 'PUT',
    body: JSON.stringify(issue.toJson())
  });
  return new EnvironmentIssue(data);
}

/**
 * Delete environment issue
 * @param {number} issueId - Issue ID
 * @returns {Promise<void>}
 */
export async function deleteEnvironmentIssue(issueId) {
  await apiFetch(`v1/environments/reported-issues/${issueId}`, {
    method: 'DELETE'
  });
}

/**
 * Get artefact environment reviews
 * @param {number} artefactId - Artefact ID
 * @returns {Promise<EnvironmentReview[]>}
 */
export async function getArtefactEnvironmentReviews(artefactId) {
  const data = await apiFetch(`v1/artefacts/${artefactId}/environment-reviews`);
  return data.map(json => new EnvironmentReview(json));
}

/**
 * Update environment review
 * @param {number} artefactId - Artefact ID
 * @param {EnvironmentReview} review - Review to update
 * @returns {Promise<EnvironmentReview>}
 */
export async function updateEnvironmentReview(artefactId, review) {
  const data = await apiFetch(`v1/artefacts/${artefactId}/environment-reviews/${review.id}`, {
    method: 'PATCH',
    body: JSON.stringify({
      id: review.id,
      artefact_id: review.artefactId,
      environment_id: review.environmentId,
      review_decision: review.reviewDecision,
      review_comment: review.reviewComment
    })
  });
  return new EnvironmentReview(data);
}

/**
 * Search artefacts
 * @param {Object} params - Search parameters
 * @param {string} params.query - Search query
 * @param {string[]} params.families - Artefact families to filter
 * @param {number} params.limit - Result limit
 * @param {number} params.offset - Result offset
 * @returns {Promise<string[]>}
 */
export async function searchArtefacts({ query = null, families = null, limit = 50, offset = 0 } = {}) {
  const queryParams = new URLSearchParams({ limit, offset });
  
  if (query && query.trim().length > 0) {
    queryParams.append('q', query.trim());
  }
  
  if (families && families.length > 0) {
    for (const family of families) {
      queryParams.append('families', family);
    }
  }
  
  const data = await apiFetch(`v1/artefacts/search?${queryParams}`);
  return data.artefacts || [];
}

/**
 * Search environments
 * @param {Object} params - Search parameters
 * @returns {Promise<string[]>}
 */
export async function searchEnvironments({ query = null, families = null, limit = 50, offset = 0 } = {}) {
  const queryParams = new URLSearchParams({ limit, offset });
  
  if (query && query.trim().length > 0) {
    queryParams.append('q', query.trim());
  }
  
  if (families && families.length > 0) {
    for (const family of families) {
      queryParams.append('families', family);
    }
  }
  
  const data = await apiFetch(`v1/environments/search?${queryParams}`);
  return data.environments || [];
}
