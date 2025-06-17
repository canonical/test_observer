#!/usr/bin/env python3
"""
Dedicated test program for debugging GitHub issue fetching.

This script allows for isolated testing and debugging of the GitHub API
integration without affecting the main application.

Usage:
    python debug_github.py [issue_url_or_number]
    
Examples:
    python debug_github.py https://github.com/canonical/checkbox/issues/1627
    python debug_github.py canonical/checkbox/issues/1627
    python debug_github.py 1627
"""

import sys
import logging
import traceback
import os
from typing import Optional

# Set up logging to see debug information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our GitHub API classes
try:
    from test_observer.external_apis.issue_tracking.github_api import GitHubAPI
    from test_observer.external_apis.issue_tracking.url_parser import IssueURLParser
    from test_observer.external_apis.issue_tracking.models import IssueInfo, ParsedIssueURL
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the backend directory with the proper environment")
    sys.exit(1)


def test_url_parsing(url: str) -> Optional[tuple[str, str, str]]:
    """Test URL parsing for a given GitHub URL."""
    logger.info(f"Testing URL parsing for: {url}")
    
    try:
        parsed = IssueURLParser.parse_url(url)
        if parsed:
            logger.info(f"✅ URL parsed successfully:")
            logger.info(f"   Platform: {parsed.platform}")
            logger.info(f"   Host: {parsed.host}")
            logger.info(f"   External ID: {parsed.external_id}")
            if hasattr(parsed, 'owner') and parsed.owner:
                logger.info(f"   Owner: {parsed.owner}")
            if hasattr(parsed, 'repo') and parsed.repo:
                logger.info(f"   Repository: {parsed.repo}")
            if hasattr(parsed, 'project') and parsed.project:
                logger.info(f"   Project: {parsed.project}")
            
            # Return owner, repo, issue_number for GitHub API testing
            if parsed.platform == "github" and hasattr(parsed, 'owner') and hasattr(parsed, 'repo'):
                return (parsed.owner, parsed.repo, parsed.external_id)
            else:
                return None
        else:
            logger.error(f"❌ URL parsing failed - returned None")
            return None
    except Exception as e:
        logger.error(f"❌ URL parsing failed with exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def test_github_api_direct(owner: str, repo: str, issue_number: str) -> Optional[IssueInfo]:
    """Test direct GitHub API access for an issue."""
    logger.info(f"Testing direct GitHub API access for issue: {owner}/{repo}#{issue_number}")
    
    # Check for credentials
    github_token = os.environ.get("GITHUB_TOKEN")
    
    logger.info(f"Repository: {owner}/{repo}")
    logger.info(f"Issue Number: {issue_number}")
    logger.info(f"Token configured: {'Yes' if github_token else 'No'}")
    
    if not github_token:
        logger.warning("⚠️  No GitHub token found in environment variables")
        logger.warning("   Set GITHUB_TOKEN to test authenticated requests")
        logger.info("   Proceeding with unauthenticated request (rate limited, may fail for private repos)")
    else:
        # Mask the token for security
        masked_token = github_token[:8] + "..." + github_token[-4:] if len(github_token) > 12 else "***"
        logger.info(f"   Using token: {masked_token}")
    
    try:
        api = GitHubAPI()
        logger.info("✅ GitHubAPI initialized successfully")
        
        # Test the get_issue method
        result = api.get_issue(owner, repo, issue_number)
        
        if result:
            logger.info(f"✅ Issue fetched successfully:")
            logger.info(f"   External ID: {result.external_id}")
            logger.info(f"   Title: {result.title}")
            logger.info(f"   Status: {result.status}")
            logger.info(f"   URL: {result.url}")
            logger.info(f"   Last Updated: {result.last_updated}")
            logger.info(f"   Assignee: {result.assignee}")
            logger.info(f"   Labels: {result.labels}")
            logger.info(f"   Description: {result.description[:100] if result.description else 'None'}...")
        else:
            logger.warning(f"⚠️  Issue fetch returned None (issue may be private, deleted, or unauthorized)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ GitHub API failed with exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def test_github_raw_access(owner: str, repo: str, issue_number: str):
    """Test raw HTTP access to understand the GitHub response structure."""
    logger.info(f"Testing raw HTTP access for issue: {owner}/{repo}#{issue_number}")
    
    try:
        import requests
        import json
        
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        logger.info(f"Making request to: {url}")
        
        # Set up headers
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "test-observer-debug"
        }
        
        # Add authentication if available
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
            logger.info("✅ Using Bearer token authentication")
        else:
            logger.info("ℹ️  Making unauthenticated request")
        
        response = requests.get(url, headers=headers, timeout=30)
        
        logger.info(f"📡 Response status: {response.status_code}")
        logger.info(f"📡 Response headers: {dict(response.headers)}")
        
        # Check rate limit headers
        if 'X-RateLimit-Limit' in response.headers:
            limit = response.headers.get('X-RateLimit-Limit')
            remaining = response.headers.get('X-RateLimit-Remaining')
            reset_time = response.headers.get('X-RateLimit-Reset')
            logger.info(f"📊 Rate Limit: {remaining}/{limit} (resets at {reset_time})")
        
        if response.status_code == 401:
            logger.error("❌ Authentication failed - check GITHUB_TOKEN")
            return
        elif response.status_code == 403:
            if 'rate limit' in response.text.lower():
                logger.error("❌ Rate limit exceeded - try again later or use GITHUB_TOKEN")
            else:
                logger.error("❌ Access forbidden - user may not have permission to view this issue")
            return
        elif response.status_code == 404:
            logger.error("❌ Issue not found - check owner/repo/issue_number")
            return
        elif response.status_code != 200:
            logger.error(f"❌ Unexpected status code: {response.status_code}")
            logger.error(f"Response body: {response.text[:500]}")
            return
        
        # Parse JSON response
        try:
            data = response.json()
            logger.info("✅ JSON response parsed successfully")
            
            # Inspect the response structure
            logger.info("🔍 Inspecting GitHub issue structure:")
            logger.info(f"   Issue Number: {data.get('number', 'N/A')}")
            logger.info(f"   Issue ID: {data.get('id', 'N/A')}")
            logger.info(f"   Node ID: {data.get('node_id', 'N/A')}")
            logger.info(f"   HTML URL: {data.get('html_url', 'N/A')}")
            logger.info(f"   API URL: {data.get('url', 'N/A')}")
            
            # Check important fields
            field_mappings = {
                'title': 'Title',
                'body': 'Description/Body',
                'state': 'State',
                'state_reason': 'State Reason',
                'assignee': 'Assignee',
                'assignees': 'Assignees',
                'user': 'Creator/User',
                'labels': 'Labels',
                'milestone': 'Milestone',
                'created_at': 'Created At',
                'updated_at': 'Updated At',
                'closed_at': 'Closed At',
                'pull_request': 'Pull Request Info',
                'draft': 'Draft Status',
                'locked': 'Locked Status'
            }
            
            logger.info("🔍 Inspecting issue fields:")
            for field_key, field_name in field_mappings.items():
                if field_key in data:
                    value = data[field_key]
                    if isinstance(value, dict):
                        # For complex objects, show key properties
                        if field_key == 'assignee' and value:
                            logger.info(f"   {field_name}: {value.get('login', 'N/A')} ({value.get('html_url', 'N/A')})")
                        elif field_key == 'assignees':
                            assignee_logins = [a.get('login', 'N/A') for a in value] if value else []
                            logger.info(f"   {field_name}: {assignee_logins}")
                        elif field_key == 'user' and value:
                            logger.info(f"   {field_name}: {value.get('login', 'N/A')} ({value.get('html_url', 'N/A')})")
                        elif field_key == 'milestone' and value:
                            logger.info(f"   {field_name}: {value.get('title', 'N/A')}")
                        elif field_key == 'pull_request' and value:
                            logger.info(f"   {field_name}: This is a pull request - {value}")
                        else:
                            logger.info(f"   {field_name}: {value}")
                    elif isinstance(value, list):
                        if field_key == 'labels':
                            label_names = [label.get('name', 'N/A') for label in value] if value else []
                            logger.info(f"   {field_name}: {label_names}")
                        else:
                            logger.info(f"   {field_name}: {value}")
                    else:
                        # For simple values, truncate if too long
                        value_str = str(value)
                        if field_key == 'body' and value_str and len(value_str) > 200:
                            value_str = value_str[:197] + "..."
                        logger.info(f"   {field_name}: {value_str}")
                else:
                    logger.info(f"   {field_name}: [NOT AVAILABLE]")
            
            # Check if this is actually a pull request
            if data.get('pull_request'):
                logger.warning("⚠️  This is a Pull Request, not an Issue!")
                logger.info("   GitHub API treats PRs as issues, but they have additional PR-specific data")
            
            # Show raw JSON for debugging (truncated)
            json_str = json.dumps(data, indent=2)
            if len(json_str) > 2000:
                json_str = json_str[:1997] + "..."
            logger.info(f"🔍 Raw JSON response (truncated):\n{json_str}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"Response body: {response.text[:500]}")
            
    except Exception as e:
        logger.error(f"❌ Raw HTTP access failed: {type(e).__name__}: {e}")
        traceback.print_exc()


def parse_github_input(input_str: str) -> tuple[str, str, str] | None:
    """Parse various GitHub input formats to extract owner, repo, issue_number."""
    
    # First try URL parsing
    if input_str.startswith('http'):
        parsed = test_url_parsing(input_str)
        if parsed:
            return parsed
    
    # Try owner/repo/issues/number format
    if '/' in input_str and 'issues' in input_str:
        parts = input_str.strip('/').split('/')
        if len(parts) >= 4 and parts[-2] == 'issues':
            owner, repo, _, issue_number = parts[-4:]
            return (owner, repo, issue_number)
    
    # Try owner/repo#number format  
    if '#' in input_str:
        repo_part, issue_number = input_str.split('#', 1)
        if '/' in repo_part:
            owner, repo = repo_part.rsplit('/', 1)
            return (owner, repo, issue_number)
    
    # If just a number, we can't determine the repository
    if input_str.isdigit():
        return None
    
    return None


def main():
    """Main test function."""
    # Default test URLs and issues
    test_cases = [
        {
            'url': 'https://github.com/canonical/checkbox/issues/1627',
            'owner': 'canonical',
            'repo': 'checkbox', 
            'issue_number': '1627',
            'description': 'Canonical Checkbox issue (main test case)'
        },
        {
            'url': 'https://github.com/octocat/Hello-World/issues/1',
            'owner': 'octocat',
            'repo': 'Hello-World',
            'issue_number': '1', 
            'description': 'Classic GitHub test repo issue'
        },
        {
            'url': 'https://github.com/torvalds/linux/issues/1',
            'owner': 'torvalds',
            'repo': 'linux',
            'issue_number': '1',
            'description': 'Linux kernel repo (issues may be disabled)'
        }
    ]
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        input_str = sys.argv[1]
        parsed = parse_github_input(input_str)
        
        if parsed:
            owner, repo, issue_number = parsed
            test_cases = [{
                'url': f'https://github.com/{owner}/{repo}/issues/{issue_number}',
                'owner': owner,
                'repo': repo,
                'issue_number': issue_number,
                'description': 'Command line provided issue'
            }]
        else:
            logger.error(f"❌ Could not parse input: {input_str}")
            logger.error("Expected formats:")
            logger.error("  - https://github.com/owner/repo/issues/123")
            logger.error("  - owner/repo/issues/123") 
            logger.error("  - owner/repo#123")
            sys.exit(1)
    
    logger.info("🚀 Starting GitHub issue fetching debug session")
    logger.info("=" * 60)
    
    # Show environment configuration
    logger.info("🔧 Environment Configuration:")
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        masked_token = github_token[:8] + "..." + github_token[-4:] if len(github_token) > 12 else "***"
        logger.info(f"   GITHUB_TOKEN: {masked_token}")
    else:
        logger.info(f"   GITHUB_TOKEN: Not set")
    logger.info("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📋 Test Case {i}: {test_case['description']}")
        logger.info(f"URL: {test_case['url']}")
        logger.info(f"Repository: {test_case['owner']}/{test_case['repo']}")
        logger.info(f"Issue Number: {test_case['issue_number']}")
        logger.info("-" * 40)
        
        # Test URL parsing
        parsed_info = test_url_parsing(test_case['url'])
        
        # Test GitHub API
        owner = test_case['owner']
        repo = test_case['repo'] 
        issue_number = test_case['issue_number']
        
        # Use parsed info if available and different
        if parsed_info:
            parsed_owner, parsed_repo, parsed_issue = parsed_info
            if (parsed_owner, parsed_repo, parsed_issue) != (owner, repo, issue_number):
                logger.info(f"Using parsed values: {parsed_owner}/{parsed_repo}#{parsed_issue}")
                owner, repo, issue_number = parsed_owner, parsed_repo, parsed_issue
        
        api_result = test_github_api_direct(owner, repo, issue_number)
        
        # Test raw HTTP access for more detailed debugging
        test_github_raw_access(owner, repo, issue_number)
        
        logger.info("=" * 60)
    
    logger.info("🏁 Debug session completed")
    logger.info("\n💡 Tips:")
    logger.info("   - Set GITHUB_TOKEN environment variable for higher rate limits and private repo access")
    logger.info("   - GitHub API treats Pull Requests as issues with additional PR data")
    logger.info("   - Rate limits: 60 requests/hour without token, 5000 requests/hour with token")
    logger.info("   - Check repository exists and has issues enabled")


if __name__ == "__main__":
    main()