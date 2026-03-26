<!--
Copyright 2026 Canonical Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
SPDX-License-Identifier: Apache-2.0
-->

# GitHub Copilot PR Review Instructions

This file provides guidance for GitHub Copilot when reviewing pull requests in the Test Observer repository.

## Review Focus Areas

### General Code Quality

- **Code clarity**: Flag unclear logic, missing comments where complex behavior needs explanation
- **Error handling**: Verify proper error handling, especially for API calls and async operations
- **Resource management**: Check for proper cleanup in Flutter and ordering of db operations in Python
- **State management**: Look for state inconsistencies, race conditions, or stale state issues
- **Security**: Flag hardcoded credentials, SQL injection risks, XSS vulnerabilities, insecure configurations

### Backend (Python/FastAPI)

- **Type safety**: All functions should have type hints (enforced by Ruff and reviewed by mypy)
- **Database patterns**:
  - Use repository pattern via `data_access/` module
  - Verify proper session management and transactions
  - Check for N+1 query problems
  - Ensure migrations are included for schema changes
- **API design**:
  - Endpoints must be versioned (`/v1/`)
  - Pydantic models for request/response validation
  - Proper HTTP status codes (200, 201, 400, 404, etc.)
  - Authorization checks via dependency injection
- **Testing**:
  - New endpoints must have test coverage
  - Use existing test data generators in `tests/data_generator.py`
  - Tests should run with `docker compose exec backend pytest`
- **Async operations**: Proper use of `async`/`await`, avoid blocking operations
- **Soft deletes**: Check for use of `archived` field instead of physical deletion

### Frontend (Flutter/Dart)

- **State management**:
  - Check for missing `mounted` checks before `setState()` in async operations
  - Verify state is reset in error and success paths
- **UI/UX**:
  - Accessibility: text contrast, semantic labels
  - Loading states and error handling in UI
  - User feedback via SnackBars
  - Responsive design considerations
- **Navigation**: Verify routes are properly defined and navigation logic is correct
- **API integration**:
  - Proper error handling, loading states, and data validation
  - Make sure the frontend calls to the backend conform to the API schema

### Common Issues to Flag

1. **Resource leaks**:
   - Missing `finally` blocks for state cleanup
   - Unclosed streams, subscriptions, or database connections
   - Unmounted widget checks in Flutter async operations

2. **Race conditions**:
   - State updates without proper synchronization
   - Missing locks or atomic operations where needed
   - Optimistic UI updates that don't handle failures

3. **Performance**:
   - Inefficient database queries (N+1, missing indexes)
   - Excessive API calls or missing caching
   - Heavy operations in UI build methods

4. **Breaking changes**:
   - API contract changes without versioning
   - Database migrations that could cause data loss
   - Missing backward compatibility considerations

5. **Configuration**:
   - Missing or incorrect environment variables
   - Hardcoded values that should be configurable
   - Insecure defaults (e.g., `SESSIONS_HTTPS_ONLY=false` in production)

## Review Process

### Initial Pass

1. **Read the PR description**: Understand the problem being solved and the approach
2. **Check the PR template**: Ensure all sections are filled out appropriately
3. **Review linked issues**: Verify Jira and GitHub issues are properly linked
4. **Scan for obvious issues**: Quick pass for security issues, typos, formatting

### Detailed Review

1. **Architecture alignment**: Does the code follow the patterns described in CLAUDE.md?
2. **Code correctness**: Logic bugs, edge cases, error handling
3. **Test coverage**: Are there tests for new functionality and bug fixes?
4. **Documentation**: Are docs updated? Are complex sections commented?
5. **Database changes**: Are migrations included and reviewed?
6. **API changes**: Are breaking changes flagged? Is versioning correct?

### Checklist for PR Approval

- [ ] Code follows repository conventions (see CLAUDE.md)
- [ ] Tests are included and pass (backend: pytest, frontend: flutter test --platform chrome)
- [ ] Type checking passes (backend: mypy, frontend: flutter analyze)
- [ ] Linting passes (backend: ruff, frontend: flutter analyze)
- [ ] Database migrations are included if schema changed
- [ ] API changes are properly versioned
- [ ] Documentation is updated if needed
- [ ] No security vulnerabilities introduced
- [ ] Error handling is comprehensive
- [ ] State management is correct (no leaks, proper cleanup)
- [ ] UI changes have good contrast and accessibility
- [ ] Breaking changes are clearly documented

## Helpful Comments

When providing feedback:

- **Be specific**: Point to exact lines and explain the issue
- **Suggest fixes**: When possible, provide code snippets or alternatives
- **Explain reasoning**: Help the author understand _why_ something is an issue
- **Use examples**: Reference similar patterns in the codebase
- **Be constructive**: Focus on improvement, not criticism
- **Prioritize**: Mark critical issues (security, bugs) vs nice-to-haves (style, minor optimizations)

## Additional Resources

- Repository architecture and conventions: See [CLAUDE.md](../CLAUDE.md)
- PR template requirements: See [pull_request_template.md](pull_request_template.md)
- Development commands: See [CLAUDE.md](../CLAUDE.md#development-commands)
