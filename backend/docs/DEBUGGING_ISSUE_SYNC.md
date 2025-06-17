# Debugging Issue Sync Errors

This document explains how to debug "Failed to sync environment issue" and similar errors in the Test Observer backend.

## Problem Description

The issue sync service synchronizes issue statuses from external platforms (GitHub, Jira, Launchpad) with the Test Observer database. When sync fails, you may see generic error messages like:
- "Failed to sync environment issue"
- "Failed to sync test case issue"

## Recent Improvements

The following improvements have been made to provide better error visibility:

1. **Enhanced Logging**: Added detailed logging throughout the sync process
2. **Exception Details**: Errors now include exception type and full stack traces
3. **API Response Logging**: HTTP errors include response status codes and body content
4. **Re-raising Exceptions**: API clients now re-raise exceptions instead of swallowing them

## Enabling Verbose Logging

### For Docker Compose

Set the `LOG_LEVEL` environment variable to `DEBUG`:

```bash
# In your .env file or docker-compose.yml
LOG_LEVEL=DEBUG

# Or when running docker-compose
LOG_LEVEL=DEBUG docker-compose up
```

### For Kubernetes

Update your deployment or use kubectl to set the environment variable:

```bash
kubectl set env deployment/test-observer-api LOG_LEVEL=DEBUG
kubectl set env deployment/test-observer-celery LOG_LEVEL=DEBUG
```

### View Logs

#### Docker Compose
```bash
# View API logs
docker-compose logs -f backend

# View Celery worker logs (where sync happens)
docker-compose logs -f celery
```

#### Kubernetes
```bash
# View API logs
kubectl logs -f service/test-observer-api

# View Celery worker logs
kubectl logs -f deployment/test-observer-celery
```

## Understanding the Logs

With debug logging enabled, you'll see:

1. **Sync Start/End Messages**:
   ```
   Starting issue sync task
   Issue sync completed successfully: {'total_synced': 5, 'total_failed': 1, ...}
   ```

2. **API Request Details**:
   ```
   Fetching GitHub issue from: https://api.github.com/repos/canonical/test-observer/issues/123
   ```

3. **Detailed Error Messages**:
   ```
   HTTP error fetching GitHub issue canonical/test-observer#123: HTTPError: 401 Unauthorized
   Response status: 401, body: {"message":"Bad credentials","documentation_url":"..."}
   ```

4. **Stack Traces** (with `exc_info=True`):
   ```
   Error syncing environment issue 42 (https://github.com/...): ValueError: Invalid response format
   Traceback (most recent call last):
     File "...", line X, in sync_environment_issues
     ...
   ```

## Common Issues and Solutions

### 1. Authentication Errors

**Symptoms**: 401 Unauthorized errors in logs

**Solution**: Check your API credentials:
- GitHub: Ensure `GITHUB_TOKEN` is set correctly
- Jira: Verify `JIRA_USERNAME` and `JIRA_TOKEN`
- Launchpad: No credentials needed (uses anonymous access)

### 2. Network/Connection Issues

**Symptoms**: Connection timeouts, DNS resolution failures

**Solution**: 
- Check network connectivity from the container/pod
- Verify API endpoints are accessible
- Check for proxy settings if behind a corporate firewall

### 3. API Rate Limiting

**Symptoms**: 429 Too Many Requests errors

**Solution**:
- The system has built-in retry logic with backoff
- Consider reducing sync frequency in Celery beat schedule
- For GitHub, ensure you're using an authenticated token (higher rate limits)

### 4. Invalid URLs

**Symptoms**: "Could not parse issue URL" warnings

**Solution**:
- Verify URLs in the database are correctly formatted
- Supported formats:
  - GitHub: `https://github.com/owner/repo/issues/123`
  - Jira: `https://your-domain.atlassian.net/browse/KEY-123`
  - Launchpad: `https://bugs.launchpad.net/project/+bug/123456`
    - Also supports: `https://bugs.launchpad.net/ubuntu/+source/package/+bug/123456`
    - And: `https://bugs.launchpad.net/bugs/123456`

## Testing Issue Sync

To manually test issue sync:

```python
# In a Python shell within the container
from test_observer.services.issue_sync_service import IssueSyncService
from test_observer.data_access.setup import SessionLocal

db = SessionLocal()
sync_service = IssueSyncService()

# Test a specific URL
result = sync_service._sync_issue_status("https://github.com/canonical/test-observer/issues/1")
print(result)

# Run full sync
stats = sync_service.sync_all_issues(db)
print(stats)
```

## Database Queries

To check sync status in the database:

```sql
-- Check failed test case issues
SELECT id, url, sync_status, sync_error, last_synced_at 
FROM test_case_issue 
WHERE sync_status = 'sync_failed';

-- Check failed environment issues
SELECT id, url, sync_status, sync_error, last_synced_at 
FROM environment_issue 
WHERE sync_status = 'sync_failed';

-- View recent sync attempts
SELECT id, url, sync_status, sync_error, last_synced_at 
FROM environment_issue 
WHERE last_synced_at > NOW() - INTERVAL '1 hour'
ORDER BY last_synced_at DESC;
```

## Further Debugging

If issues persist after enabling verbose logging:

1. Check the Celery beat schedule is running: `docker-compose logs celery | grep "Scheduler:"`
2. Verify the database migrations are up to date: `docker-compose exec backend alembic current`
3. Test API connectivity directly using curl from within the container
4. Review Sentry logs if `SENTRY_DSN` is configured