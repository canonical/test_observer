# Jira Issue Fetching Debug Tool

This directory contains a dedicated test program (`debug_jira.py`) for debugging and iterating on the Jira issue fetching functionality.

## Purpose

The debug tool helps isolate and fix issues with Jira issue fetching without affecting the main Test Observer application. It's particularly useful for:

- Testing URL parsing for Jira URLs
- Debugging API authentication issues
- Understanding the structure of Jira issue objects
- Testing ADF (Atlassian Document Format) parsing
- Iterating on fixes for specific problematic issues

## Usage

### Basic Usage

```bash
# Run with default test cases (including LM-1723)
python debug_jira.py

# Test a specific issue key
python debug_jira.py LM-1723
```

### Prerequisites

Make sure you're in the backend directory and have the proper environment activated:

```bash
cd backend
uv shell  # or your preferred environment activation
python debug_jira.py
```

### Environment Variables

For authenticated requests (recommended), set these environment variables:

```bash
export JIRA_USERNAME="your-email@canonical.com"
export JIRA_TOKEN="your-api-token"
export JIRA_BASE_URL="https://warthogs.atlassian.net"  # Optional, defaults to warthogs
```

**Getting a Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label like "Test Observer Debug"
4. Copy the token and set it as `JIRA_TOKEN`

## What It Tests

The debug tool performs three levels of testing:

### 1. URL Parsing Test
- Tests the `IssueURLParser.parse_url()` function
- Verifies that Jira URLs are parsed correctly
- Shows extracted issue keys and metadata

### 2. Jira API Test
- Tests the `JiraAPI.get_issue()` method
- Shows the structured `IssueInfo` result
- Displays all extracted issue information
- Tests ADF description parsing

### 3. Raw HTTP Access
- Direct HTTP requests to Jira REST API
- Inspects the raw JSON response structure
- Helps understand available fields and their formats
- Useful for debugging authentication and permission issues

## Default Test Cases

The tool includes several test cases by default:

1. **Warthogs Issue**: `https://warthogs.atlassian.net/browse/LM-1723`
   - The main test case from your example
   
2. **Generic Format**: `https://example.atlassian.net/browse/TEST-123`
   - Tests standard Jira URL format parsing

## Sample Output

```
🚀 Starting Jira issue fetching debug session
============================================================
🔧 Environment Configuration:
   JIRA_BASE_URL: https://warthogs.atlassian.net
   JIRA_USERNAME: Set
   JIRA_TOKEN: Set
============================================================

📋 Test Case 1: Warthogs Jira issue (main test case)
URL: https://warthogs.atlassian.net/browse/LM-1723
Issue Key: LM-1723
----------------------------------------
2025-06-17 11:00:00 - DEBUG - Testing URL parsing for: https://warthogs.atlassian.net/browse/LM-1723
2025-06-17 11:00:00 - INFO - ✅ URL parsed successfully:
2025-06-17 11:00:00 - INFO -    Platform: jira
2025-06-17 11:00:00 - INFO -    Host: warthogs.atlassian.net
2025-06-17 11:00:00 - INFO -    External ID: LM-1723
...
```

## Debugging Specific Issues

### Authentication Issues
```
❌ Authentication failed - check JIRA_USERNAME and JIRA_TOKEN
```
**Solution**: Verify your Jira credentials and API token.

### Permission Issues
```
❌ Access forbidden - user may not have permission to view this issue
```
**Solution**: Check if the issue exists and if your user has permission to view it.

### URL Parsing Issues
The URL parsing test will show whether Jira URLs are being parsed correctly and what issue key is extracted.

### ADF Description Issues
If Jira descriptions are in Atlassian Document Format (ADF), the raw HTTP access will show the exact structure, helping debug the ADF parser.

## Environment Configuration

### Warthogs Atlassian (Default)
```bash
export JIRA_BASE_URL="https://warthogs.atlassian.net"
export JIRA_USERNAME="your-email@canonical.com"
export JIRA_TOKEN="your-api-token"
```

### Other Jira Instances
```bash
export JIRA_BASE_URL="https://your-company.atlassian.net"
export JIRA_USERNAME="your-username"
export JIRA_TOKEN="your-api-token"
```

### Unauthenticated Testing
You can run without credentials, but many issues will be inaccessible:
```bash
unset JIRA_USERNAME
unset JIRA_TOKEN
python debug_jira.py LM-1723
```

## Modifying the Tool

The debug tool is designed to be easily modified for testing specific scenarios:

1. **Add new test URLs**: Modify the `test_cases` list in `main()`
2. **Test different fields**: Add fields to `field_mappings` in `test_jira_raw_access()`
3. **Add new test functions**: Create new test functions and call them from `main()`

## Common Issues and Solutions

### Import Errors
```
Failed to import required modules: No module named 'requests'
```
**Solution**: Make sure you're in the backend directory and have activated the proper Python environment.

### Network/Connection Issues
```
❌ Raw HTTP access failed: ConnectionError
```
**Solution**: Check network connectivity and firewall settings.

### Invalid Issue Key Format
```
❌ Issue not found - check issue key and Jira base URL
```
**Solution**: Verify the issue key format matches your Jira project naming convention.

### ADF Parsing Issues
If descriptions are complex, the raw HTTP access will show the exact ADF structure to help debug the parser.

## Integration with Main Application

Once issues are identified and fixed using this debug tool, the fixes should be applied to:

- `test_observer/external_apis/issue_tracking/jira_api.py`
- `test_observer/external_apis/issue_tracking/url_parser.py`
- `test_observer/services/issue_sync_service.py`

Remember to run the full test suite after making changes to ensure no regressions.

## Security Notes

- Never commit API tokens to version control
- Use environment variables or secure credential storage
- Consider using application passwords instead of personal API tokens for production
- Regularly rotate API tokens for security