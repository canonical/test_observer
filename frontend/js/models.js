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
 * Data models for Test Observer
 * Translated from Dart models in lib/models/
 */

// Family Names
export const FamilyName = {
  SNAP: 'snap',
  DEB: 'deb',
  CHARM: 'charm',
  IMAGE: 'image'
};

// Stage Names
export const StageName = {
  BETA: 'beta',
  CANDIDATE: 'candidate',
  STABLE: 'stable',
  EDGE: 'edge'
};

// Artefact Status
export const ArtefactStatus = {
  APPROVED: 'APPROVED',
  REJECTED: 'MARKED_AS_FAILED',
  UNDECIDED: 'UNDECIDED',
  
  getName(status) {
    switch (status) {
      case this.APPROVED: return 'Approved';
      case this.REJECTED: return 'Rejected';
      case this.UNDECIDED: return 'Undecided';
      default: return status;
    }
  }
};

// Test Execution Status
export const TestExecutionStatus = {
  FAILED: 'FAILED',
  NOT_STARTED: 'NOT_STARTED',
  NOT_TESTED: 'NOT_TESTED',
  IN_PROGRESS: 'IN_PROGRESS',
  PASSED: 'PASSED',
  ENDED_PREMATURELY: 'ENDED_PREMATURELY',
  
  isCompleted(status) {
    return status === this.PASSED || status === this.FAILED;
  },
  
  getName(status) {
    switch (status) {
      case this.FAILED: return 'Failed';
      case this.NOT_STARTED: return 'Not Started';
      case this.NOT_TESTED: return 'Not Tested';
      case this.IN_PROGRESS: return 'In Progress';
      case this.PASSED: return 'Passed';
      case this.ENDED_PREMATURELY: return 'Ended Prematurely';
      default: return status;
    }
  }
};

// Test Result Status
export const TestResultStatus = {
  FAILED: 'FAILED',
  PASSED: 'PASSED',
  SKIPPED: 'SKIPPED',
  
  getName(status) {
    switch (status) {
      case this.FAILED: return 'Failed';
      case this.PASSED: return 'Passed';
      case this.SKIPPED: return 'Skipped';
      default: return status;
    }
  }
};

// User model
export class User {
  constructor(data = {}) {
    this.id = data.id || 0;
    this.launchpadHandle = data.launchpad_handle || '';
    this.launchpadEmail = data.launchpad_email || '';
    this.name = data.name || '';
  }
  
  static empty() {
    return new User();
  }
}

// Environment model
export class Environment {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.architecture = data.architecture;
  }
}

// Execution Metadata model
export class ExecutionMetadata {
  constructor(data = {}) {
    this.data = data.data || {};
  }
}

// Test Execution Relevant Link model
export class TestExecutionRelevantLink {
  constructor(data) {
    this.id = data.id;
    this.testExecutionId = data.test_execution_id;
    this.url = data.url;
    this.description = data.description || '';
  }
}

// Test Execution model
export class TestExecution {
  constructor(data) {
    this.id = data.id;
    this.ciLink = data.ci_link;
    this.c3Link = data.c3_link;
    this.status = data.status;
    this.environment = new Environment(data.environment);
    this.isRerunRequested = data.is_rerun_requested || false;
    this.artefactBuildId = data.artefact_build_id;
    this.testPlan = data.test_plan || 'unknown';
    this.relevantLinks = (data.relevant_links || []).map(link => new TestExecutionRelevantLink(link));
    this.createdAt = new Date(data.created_at);
    this.executionMetadata = new ExecutionMetadata(data.execution_metadata || {});
  }
}

// Artefact Build model
export class ArtefactBuild {
  constructor(data) {
    this.id = data.id;
    this.architecture = data.architecture;
    this.revision = data.revision;
    this.testExecutions = (data.test_executions || []).map(te => {
      return new TestExecution({
        ...te,
        artefact_build_id: data.id
      });
    });
  }
}

// Artefact model
export class Artefact {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.version = data.version;
    this.family = data.family;
    this.track = data.track || '';
    this.store = data.store || '';
    this.branch = data.branch || '';
    this.series = data.series || '';
    this.repo = data.repo || '';
    this.source = data.source || '';
    this.os = data.os || '';
    this.release = data.release || '';
    this.owner = data.owner || '';
    this.sha256 = data.sha256 || '';
    this.imageUrl = data.image_url || '';
    this.status = data.status;
    this.comment = data.comment || '';
    this.stage = data.stage;
    this.allEnvironmentReviewsCount = data.all_environment_reviews_count;
    this.completedEnvironmentReviewsCount = data.completed_environment_reviews_count;
    this.assignee = new User(data.assignee || {});
    this.bugLink = data.bug_link || '';
    this.dueDate = data.due_date ? new Date(data.due_date) : null;
  }
  
  get dueDateString() {
    if (!this.dueDate) return null;
    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return `${monthNames[this.dueDate.getMonth()]} ${this.dueDate.getDate()}`;
  }
  
  get remainingTestExecutionCount() {
    return this.allEnvironmentReviewsCount - this.completedEnvironmentReviewsCount;
  }
}

// Issue Attachment model
export class IssueAttachment {
  constructor(data) {
    this.id = data.id;
    this.testResultId = data.test_result_id;
    this.issueId = data.issue_id;
    this.issue = data.issue ? new Issue(data.issue) : null;
  }
}

// Issue model
export class Issue {
  constructor(data) {
    this.id = data.id;
    this.url = data.url;
    this.description = data.description;
  }
}

// Previous Test Result model
export class PreviousTestResult {
  constructor(data) {
    this.status = data.status;
    this.version = data.version;
    this.artefactId = data.artefact_id;
  }
}

// Test Result model
export class TestResult {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.status = data.status;
    this.createdAt = new Date(data.created_at);
    this.category = data.category || '';
    this.comment = data.comment || '';
    this.templateId = data.template_id || '';
    this.ioLog = data.io_log || '';
    this.previousResults = (data.previous_results || []).map(pr => new PreviousTestResult(pr));
    this.issueAttachments = (data.issues || []).map(issue => new IssueAttachment(issue));
  }
}

// Test Event model
export class TestEvent {
  constructor(data) {
    this.id = data.id;
    this.testExecutionId = data.test_execution_id;
    this.timestamp = new Date(data.timestamp);
    this.eventName = data.event_name;
    this.detail = data.detail || '';
  }
}

// Environment Review model
export class EnvironmentReview {
  constructor(data) {
    this.id = data.id;
    this.artefactId = data.artefact_id;
    this.environmentId = data.environment_id;
    this.reviewDecision = data.review_decision || [];
    this.reviewComment = data.review_comment || '';
  }
}

// Artefact Version model
export class ArtefactVersion {
  constructor(data) {
    this.version = data.version;
    this.createdAt = new Date(data.created_at);
  }
}

// Test Issue model
export class TestIssue {
  constructor(data) {
    this.id = data.id;
    this.url = data.url;
    this.description = data.description;
    this.caseName = data.case_name || null;
    this.templateId = data.template_id || null;
  }
  
  toJson() {
    return {
      id: this.id,
      url: this.url,
      description: this.description,
      case_name: this.caseName,
      template_id: this.templateId
    };
  }
}

// Environment Issue model
export class EnvironmentIssue {
  constructor(data) {
    this.id = data.id;
    this.url = data.url || '';
    this.description = data.description;
    this.environmentName = data.environment_name;
    this.isConfirmed = data.is_confirmed || false;
  }
  
  toJson() {
    return {
      id: this.id,
      url: this.url.length === 0 ? null : this.url,
      description: this.description,
      environment_name: this.environmentName,
      is_confirmed: this.isConfirmed
    };
  }
}

// Rerun Request model
export class RerunRequest {
  constructor(data) {
    this.testExecutionId = data.test_execution_id;
    this.ciLink = data.ci_link;
  }
}

// Issue Source and Status
export const IssueSource = {
  GITHUB: 'github',
  JIRA: 'jira',
  LAUNCHPAD: 'launchpad'
};

export const IssueStatus = {
  UNKNOWN: 'unknown',
  CLOSED: 'closed',
  OPEN: 'open',
  
  getName(status) {
    switch (status) {
      case this.UNKNOWN: return 'Unknown';
      case this.CLOSED: return 'Closed';
      case this.OPEN: return 'Open';
      default: return status;
    }
  }
};

// Attachment Rule model
export class AttachmentRule {
  constructor(data) {
    this.id = data.id;
    this.issueId = data.issue_id;
    this.testName = data.test_name || '';
    this.templateId = data.template_id || '';
  }
  
  toJson() {
    return {
      id: this.id,
      issue_id: this.issueId,
      test_name: this.testName,
      template_id: this.templateId
    };
  }
}

// Issue with Context model
export class IssueWithContext {
  constructor(data) {
    this.id = data.id;
    this.source = data.source;
    this.project = data.project;
    this.key = data.key;
    this.title = data.title;
    this.status = data.status;
    this.url = data.url;
    this.attachmentRules = (data.attachment_rules || []).map(rule => new AttachmentRule(rule));
  }
  
  toIssue() {
    return new Issue({
      id: this.id,
      source: this.source,
      project: this.project,
      key: this.key,
      title: this.title,
      status: this.status,
      url: this.url
    });
  }
}

// Artefact Build Minimal model
export class ArtefactBuildMinimal {
  constructor(data) {
    this.id = data.id;
    this.architecture = data.architecture;
    this.revision = data.revision || null;
  }
}

// Test Result with Context model
export class TestResultWithContext {
  constructor(data) {
    this.testResult = new TestResult(data.test_result);
    this.testExecution = new TestExecution(data.test_execution);
    this.artefact = new Artefact(data.artefact);
    this.artefactBuild = new ArtefactBuildMinimal(data.artefact_build);
  }
}

// Test Results Search Result model
export class TestResultsSearchResult {
  constructor(data) {
    this.count = data.count;
    this.testResults = (data.test_results || []).map(tr => new TestResultWithContext(tr));
  }
  
  get hasMore() {
    return this.count > this.testResults.length;
  }
  
  static empty() {
    return new TestResultsSearchResult({
      count: 0,
      test_results: []
    });
  }
}
