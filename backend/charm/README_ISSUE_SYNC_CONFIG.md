# Issue Sync Configuration for Test Observer Backend Charm

This document describes how to configure issue tracking integration credentials for the Test Observer backend charm.

## Overview

The Test Observer backend can sync issue statuses from GitHub, Jira, and Launchpad bug tracking systems. This feature runs as a periodic Celery task every 15 minutes, updating the status of linked issues in the database.

## Configuration Options

The following configuration options have been added to the charm:

### GitHub Integration

- **`github_token`** (string, default: "")
  - GitHub personal access token or GitHub App token
  - Required for syncing GitHub issue statuses
  - Needs at least `repo` scope for private repositories or no scope for public repositories

### Jira Integration  

- **`jira_username`** (string, default: "")
  - Jira username (typically your email address)
  - Required for syncing Jira issue statuses
  
- **`jira_token`** (string, default: "")
  - Jira API token (not your password)
  - Required for syncing Jira issue statuses
  - Generate from: https://id.atlassian.com/manage-profile/security/api-tokens

- **`jira_base_url`** (string, default: "https://warthogs.atlassian.net")
  - Base URL of your Jira instance
  - Default is set to Canonical's Jira instance
  - Change this if using a different Jira instance

### Launchpad Integration

Launchpad bug tracking uses anonymous access and doesn't require credentials.

## Setting Configuration

### During Deployment

```bash
juju deploy test-observer-api \
  --config github_token="ghp_xxxxxxxxxxxx" \
  --config jira_username="user@example.com" \
  --config jira_token="xxxxxxxxxxxx"
```

### After Deployment

```bash
# Set individual options
juju config test-observer-api github_token="ghp_xxxxxxxxxxxx"
juju config test-observer-api jira_username="user@example.com"
juju config test-observer-api jira_token="xxxxxxxxxxxx"

# Set multiple options at once
juju config test-observer-api \
  github_token="ghp_xxxxxxxxxxxx" \
  jira_username="user@example.com" \
  jira_token="xxxxxxxxxxxx"

# Change Jira instance URL if needed
juju config test-observer-api jira_base_url="https://your-company.atlassian.net"
```

### Using a Configuration File

Create a YAML file (e.g., `issue-sync-config.yaml`):

```yaml
test-observer-api:
  github_token: "ghp_xxxxxxxxxxxx"
  jira_username: "user@example.com"
  jira_token: "xxxxxxxxxxxx"
  jira_base_url: "https://your-company.atlassian.net"
```

Then apply it:

```bash
juju config test-observer-api --file issue-sync-config.yaml
```

## Verifying Configuration

Check current configuration:

```bash
# View all config
juju config test-observer-api

# View specific options
juju config test-observer-api github_token
juju config test-observer-api jira_username
```

## Security Considerations

1. **Credential Storage**: Juju stores configuration values securely, but they are visible to users with model access
2. **Token Permissions**: Use tokens with minimal required permissions:
   - GitHub: `repo` scope only if accessing private repositories
   - Jira: Read-only access to projects
3. **Rotation**: Regularly rotate API tokens and update configuration

## Troubleshooting

### Check Celery Logs

```bash
# View Celery worker logs
juju ssh test-observer-api/0
kubectl logs -c celery test-observer-api-0 -f
```

### Check Sync Status

The sync status is stored in the database for each issue:
- `sync_status`: NEVER_SYNCED, SYNCED, or SYNC_FAILED
- `sync_error`: Error message if sync failed
- `last_synced_at`: Timestamp of last successful sync

### Common Issues

1. **401 Unauthorized**: Check that credentials are correct
2. **403 Forbidden**: Token may lack required permissions
3. **404 Not Found**: Issue may have been deleted or moved
4. **Connection errors**: Check network connectivity and firewall rules

## Environment Variables

The charm sets the following environment variables for the application:

- `GITHUB_TOKEN`: From `github_token` config
- `JIRA_USERNAME`: From `jira_username` config  
- `JIRA_TOKEN`: From `jira_token` config
- `JIRA_BASE_URL`: From `jira_base_url` config

These are used by the issue tracking API clients in the application.