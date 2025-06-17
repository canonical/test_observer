# Launchpad Issue Fetching Debug Tool

This directory contains a dedicated test program (`debug_launchpad.py`) for debugging and iterating on the Launchpad issue fetching functionality.

## Purpose

The debug tool helps isolate and fix issues with Launchpad bug fetching without affecting the main Test Observer application. It's particularly useful for:

- Testing URL parsing for complex Launchpad URLs
- Debugging API access issues
- Understanding the structure of Launchpad bug objects
- Iterating on fixes for specific problematic bugs

## Usage

### Basic Usage

```bash
# Run with default test cases (including the problematic URL)
python debug_launchpad.py

# Test a specific bug number
python debug_launchpad.py 2091878

# Test with Launchpad credentials for private bugs
export LAUNCHPAD_CONSUMER_NAME="Your Consumer Name"
export LAUNCHPAD_OAUTH_TOKEN="your_oauth_token"
export LAUNCHPAD_OAUTH_TOKEN_SECRET="your_oauth_token_secret"
python debug_launchpad.py 2069797
```

### Prerequisites

Make sure you're in the backend directory and have the proper environment activated:

```bash
cd backend
poetry shell  # or your preferred environment activation
python debug_launchpad.py
```

### Launchpad Credentials (Optional)

For accessing private bugs, set the following environment variables:

```bash
export LAUNCHPAD_CONSUMER_NAME="Your Consumer Name"
export LAUNCHPAD_OAUTH_TOKEN="your_oauth_token"
export LAUNCHPAD_OAUTH_TOKEN_SECRET="your_oauth_token_secret"
```

The debug tool will automatically detect and use these credentials for authenticated access.

#### Getting Launchpad OAuth Credentials

1. Go to [Launchpad](https://launchpad.net)
2. Log in to your account  
3. Navigate to your profile settings
4. Create an OAuth application/consumer
5. Note down the consumer name, token, and token secret

**Note**: Without credentials, the tool uses anonymous access which cannot access private bugs.

## What It Tests

The debug tool performs three levels of testing:

### 1. URL Parsing Test
- Tests the `parse_issue_url()` function
- Verifies that complex Launchpad URLs are parsed correctly
- Shows extracted bug numbers and metadata

### 2. Launchpad API Test
- Tests the `LaunchpadBugAPI.get_bug()` method
- Shows the structured `IssueInfo` result
- Displays all extracted bug information

### 3. Raw Launchpadlib Access
- Direct access to the launchpadlib API
- Inspects the raw bug object structure
- Helps understand what attributes are available
- Useful for debugging AttributeError issues

## Default Test Cases

The tool includes several test cases by default:

1. **Complex URL**: `https://bugs.launchpad.net/ubuntu/+source/linux-signed-hwe-6.8/+bug/2091878`
   - The main problematic URL format with `/+source/` path
   
2. **Simple Ubuntu Bug**: `https://bugs.launchpad.net/ubuntu/+bug/1979671`
   - Standard ubuntu project bug URL
   
3. **Direct Bugs URL**: `https://bugs.launchpad.net/bugs/2089015`
   - Direct `/bugs/` format URL

## Sample Output

```
🚀 Starting Launchpad issue fetching debug session
============================================================

📋 Test Case 1: Complex URL with +source (main test case)
URL: https://bugs.launchpad.net/ubuntu/+source/linux-signed-hwe-6.8/+bug/2091878
Bug Number: 2091878
----------------------------------------
2025-06-16 18:30:00 - DEBUG - Testing URL parsing for: https://bugs.launchpad.net/ubuntu/+source/linux-signed-hwe-6.8/+bug/2091878
2025-06-16 18:30:00 - INFO - ✅ URL parsed successfully:
2025-06-16 18:30:00 - INFO -    Platform: launchpad
2025-06-16 18:30:00 - INFO -    External ID: 2091878
2025-06-16 18:30:00 - INFO - 🔐 Using authenticated Launchpad access
2025-06-16 18:30:00 - INFO -    Consumer: System-wide: Ubuntu Core (athena)
2025-06-16 18:30:00 - INFO - Testing direct Launchpad API access for bug: 2091878
2025-06-16 18:30:01 - INFO - ✅ LaunchpadBugAPI initialized successfully
2025-06-16 18:30:01 - INFO - ✅ Bug fetched successfully:
2025-06-16 18:30:01 - INFO -    Private: True
...
```

## Debugging Specific Issues

### AttributeError Issues
If you encounter AttributeError issues (like missing `status` attribute), the raw launchpadlib access will show you exactly which attributes are available on the bug object.

### URL Parsing Issues
The URL parsing test will show whether complex URLs are being parsed correctly and what bug number is extracted.

### API Access Issues
The Launchpad API test will show the full structured result and any errors that occur during bug fetching.

## Modifying the Tool

The debug tool is designed to be easily modified for testing specific scenarios:

1. **Add new test URLs**: Modify the `test_cases` list in `main()`
2. **Test different attributes**: Add attributes to `attributes_to_check` in `test_launchpad_raw_access()`
3. **Add new test functions**: Create new test functions and call them from `main()`

## Common Issues and Solutions

### Import Errors
```
Failed to import required modules: No module named 'test_observer'
```
**Solution**: Make sure you're in the backend directory and have activated the proper Python environment.

### Launchpad Connection Issues
```
Raw Launchpad connection failed: HTTPError: HTTP Error 503: Service Temporarily Unavailable
```
**Solution**: Launchpad API may be temporarily unavailable. Try again later.

### Permission Issues
```
Bug not found or not accessible: NotFound: HTTP Error 404: Not Found
```
**Solution**: Bug may be private, deleted, or the URL may be incorrect. For private bugs, provide Launchpad OAuth credentials.

### Private Bug Access
```
Bug fetch returned None (bug may be private or deleted)
```
**Solution**: The bug is likely private. Set `LAUNCHPAD_CONSUMER_NAME`, `LAUNCHPAD_OAUTH_TOKEN`, and `LAUNCHPAD_OAUTH_TOKEN_SECRET` environment variables for authenticated access.

## Integration with Main Application

Once issues are identified and fixed using this debug tool, the fixes should be applied to:

- `test_observer/external_apis/issue_tracking/launchpad_bug_api.py`
- `test_observer/external_apis/issue_tracking/url_parser.py`
- `test_observer/services/issue_sync_service.py`

Remember to run the full test suite after making changes to ensure no regressions.