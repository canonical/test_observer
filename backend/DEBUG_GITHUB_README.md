# GitHub Issue Fetching Debug Tool

This directory contains a dedicated test program (`debug_github.py`) for debugging and iterating on the GitHub issue fetching functionality.

## Purpose

The debug tool helps isolate and fix issues with GitHub issue fetching without affecting the main Test Observer application. It's particularly useful for:

- Testing URL parsing for GitHub issue URLs
- Debugging API authentication and rate limiting issues
- Understanding the structure of GitHub issue objects
- Testing with different repositories and issue states
- Iterating on fixes for specific problematic issues

## Usage

### Basic Usage

```bash
# Run with default test cases (including canonical/checkbox/issues/1627)
python debug_github.py

# Test a specific issue URL
python debug_github.py https://github.com/canonical/checkbox/issues/1627

# Test with short formats
python debug_github.py canonical/checkbox/issues/1627
python debug_github.py canonical/checkbox#1627
```

### Prerequisites

Make sure you're in the backend directory and have the proper environment activated:

```bash
cd backend
uv shell  # or your preferred environment activation
python debug_github.py
```

### Environment Variables

For authenticated requests (recommended), set this environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Getting a GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "Test Observer Debug"
4. Select scopes:
   - `public_repo` for public repositories
   - `repo` for private repositories (if needed)
5. Copy the token and set it as `GITHUB_TOKEN`

## What It Tests

The debug tool performs three levels of testing:

### 1. URL Parsing Test
- Tests the `IssueURLParser.parse_url()` function
- Verifies that GitHub URLs are parsed correctly
- Shows extracted owner, repo, and issue number

### 2. GitHub API Test
- Tests the `GitHubAPI.get_issue()` method
- Shows the structured `IssueInfo` result
- Displays all extracted issue information
- Tests authentication and rate limiting

### 3. Raw HTTP Access
- Direct HTTP requests to GitHub REST API
- Inspects the raw JSON response structure
- Shows rate limit information
- Helps understand available fields and their formats

## Default Test Cases

The tool includes several test cases by default:

1. **Canonical Checkbox Issue**: `https://github.com/canonical/checkbox/issues/1627`
   - The main test case from your example
   
2. **Classic GitHub Test**: `https://github.com/octocat/Hello-World/issues/1`
   - Well-known GitHub test repository
   
3. **Linux Kernel Repo**: `https://github.com/torvalds/linux/issues/1`
   - Tests with a repository that may have issues disabled

## Sample Output

```
🚀 Starting GitHub issue fetching debug session
============================================================
🔧 Environment Configuration:
   GITHUB_TOKEN: ghp_abcd...xyz1
============================================================

📋 Test Case 1: Canonical Checkbox issue (main test case)
URL: https://github.com/canonical/checkbox/issues/1627
Repository: canonical/checkbox
Issue Number: 1627
----------------------------------------
2025-06-17 11:00:00 - DEBUG - Testing URL parsing for: https://github.com/canonical/checkbox/issues/1627
2025-06-17 11:00:00 - INFO - ✅ URL parsed successfully:
2025-06-17 11:00:00 - INFO -    Platform: github
2025-06-17 11:00:00 - INFO -    Host: github.com
2025-06-17 11:00:00 - INFO -    External ID: 1627
2025-06-17 11:00:00 - INFO -    Owner: canonical
2025-06-17 11:00:00 - INFO -    Repository: checkbox
...
```

## Debugging Specific Issues

### Authentication Issues
```
❌ Authentication failed - check GITHUB_TOKEN
```
**Solution**: Verify your GitHub token is valid and has the correct scopes.

### Rate Limiting Issues
```
❌ Rate limit exceeded - try again later or use GITHUB_TOKEN
```
**Solution**: Wait for rate limit reset or use an authenticated token for higher limits.

### Repository Access Issues
```
❌ Issue not found - check owner/repo/issue_number
```
**Solution**: Verify the repository exists, is accessible, and has issues enabled.

### Pull Request vs Issue
GitHub API treats Pull Requests as issues with additional data. The tool will detect and warn about this:
```
⚠️  This is a Pull Request, not an Issue!
```

## Input Formats

The debug tool supports multiple input formats:

### Full URLs
```bash
python debug_github.py https://github.com/canonical/checkbox/issues/1627
```

### Path Format
```bash
python debug_github.py canonical/checkbox/issues/1627
```

### Short Hash Format  
```bash
python debug_github.py canonical/checkbox#1627
```

### Issue Number Only (Not Supported)
Bare issue numbers are not supported as the repository cannot be determined:
```bash
python debug_github.py 1627  # Error: repository must be specified
```

## Environment Configuration

### With GitHub Token (Recommended)
```bash
export GITHUB_TOKEN="ghp_your_token_here"
python debug_github.py
```

**Benefits:**
- 5000 requests/hour (vs 60 without token)
- Access to private repositories
- Better error messages

### Without Token
```bash
unset GITHUB_TOKEN
python debug_github.py
```

**Limitations:**
- 60 requests/hour rate limit
- No access to private repositories
- May get rate limited quickly

## Rate Limits

GitHub API has different rate limits:

| Authentication | Rate Limit | Notes |
|----------------|------------|-------|
| No token | 60/hour | Per IP address |
| Personal token | 5000/hour | Per user |
| App token | 5000/hour | Per installation |

The debug tool shows current rate limit status:
```
📊 Rate Limit: 4999/5000 (resets at 1634567890)
```

## Common Issues and Solutions

### Import Errors
```
Failed to import required modules: No module named 'requests'
```
**Solution**: Make sure you're in the backend directory and have activated the proper Python environment.

### Network Issues
```
❌ Raw HTTP access failed: ConnectionError
```
**Solution**: Check network connectivity and firewall settings.

### Invalid Repository
```
❌ Issue not found - check owner/repo/issue_number
```
**Solution**: 
- Verify repository exists and is accessible
- Check if issues are enabled for the repository
- Verify issue number exists

### Token Scope Issues
```
❌ Access forbidden - user may not have permission to view this issue
```
**Solution**: Ensure your token has appropriate scopes (`public_repo` or `repo`).

## Modifying the Tool

The debug tool is designed to be easily modified:

1. **Add new test repositories**: Modify the `test_cases` list in `main()`
2. **Test different fields**: Add fields to `field_mappings` in `test_github_raw_access()`
3. **Add new input formats**: Extend `parse_github_input()` function
4. **Add new test functions**: Create new test functions and call them from `main()`

## Integration with Main Application

Once issues are identified and fixed using this debug tool, the fixes should be applied to:

- `test_observer/external_apis/issue_tracking/github_api.py`
- `test_observer/external_apis/issue_tracking/url_parser.py`
- `test_observer/services/issue_sync_service.py`

Remember to run the full test suite after making changes to ensure no regressions.

## Security Notes

- Never commit GitHub tokens to version control
- Use environment variables for token storage
- Regularly rotate tokens for security
- Use minimal required scopes for tokens
- Consider using GitHub Apps for production instead of personal tokens