#!/usr/bin/env python3
"""
Dedicated test program for debugging Jira issue fetching.

This script allows for isolated testing and debugging of the Jira API
integration without affecting the main application.

Usage:
    python debug_jira.py [issue_key]
    
Examples:
    python debug_jira.py LM-1723
    python debug_jira.py TEST-123
    python debug_jira.py PROJ-456
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

# Import our Jira API classes
try:
    from test_observer.external_apis.issue_tracking.jira_api import JiraAPI
    from test_observer.external_apis.issue_tracking.url_parser import IssueURLParser
    from test_observer.external_apis.issue_tracking.models import IssueInfo, ParsedIssueURL
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the backend directory with the proper environment")
    sys.exit(1)


def test_url_parsing(url: str) -> Optional[str]:
    """Test URL parsing for a given Jira URL."""
    logger.info(f"Testing URL parsing for: {url}")
    
    try:
        parsed = IssueURLParser.parse_url(url)
        if parsed:
            logger.info(f"✅ URL parsed successfully:")
            logger.info(f"   Platform: {parsed.platform}")
            logger.info(f"   Host: {parsed.host}")
            logger.info(f"   External ID: {parsed.external_id}")
            if hasattr(parsed, 'repo') and parsed.repo:
                logger.info(f"   Repository: {parsed.repo}")
            if hasattr(parsed, 'owner') and parsed.owner:
                logger.info(f"   Owner: {parsed.owner}")
            if hasattr(parsed, 'project') and parsed.project:
                logger.info(f"   Project: {parsed.project}")
            return parsed.external_id
        else:
            logger.error(f"❌ URL parsing failed - returned None")
            return None
    except Exception as e:
        logger.error(f"❌ URL parsing failed with exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def test_jira_api_direct(issue_key: str) -> Optional[IssueInfo]:
    """Test direct Jira API access for an issue key."""
    logger.info(f"Testing direct Jira API access for issue: {issue_key}")
    
    # Check for credentials
    jira_username = os.environ.get("JIRA_USERNAME")
    jira_token = os.environ.get("JIRA_TOKEN")
    jira_base_url = os.environ.get("JIRA_BASE_URL", "https://warthogs.atlassian.net")
    
    logger.info(f"Using Jira base URL: {jira_base_url}")
    logger.info(f"Username configured: {'Yes' if jira_username else 'No'}")
    logger.info(f"Token configured: {'Yes' if jira_token else 'No'}")
    
    if not jira_username or not jira_token:
        logger.warning("⚠️  No Jira credentials found in environment variables")
        logger.warning("   Set JIRA_USERNAME and JIRA_TOKEN to test authenticated requests")
        logger.info("   Proceeding with unauthenticated request (may fail for private issues)")
    
    try:
        api = JiraAPI()
        logger.info("✅ JiraAPI initialized successfully")
        
        # Test the get_issue method
        result = api.get_issue(issue_key)
        
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
        logger.error(f"❌ Jira API failed with exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def test_jira_raw_access(issue_key: str):
    """Test raw HTTP access to understand the Jira response structure."""
    logger.info(f"Testing raw HTTP access for issue: {issue_key}")
    
    try:
        import requests
        import json
        
        jira_base_url = os.environ.get("JIRA_BASE_URL", "https://warthogs.atlassian.net")
        jira_username = os.environ.get("JIRA_USERNAME")
        jira_token = os.environ.get("JIRA_TOKEN")
        
        url = f"{jira_base_url}/rest/api/3/issue/{issue_key}"
        logger.info(f"Making request to: {url}")
        
        # Set up headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Add authentication if available
        auth = None
        if jira_username and jira_token:
            auth = (jira_username, jira_token)
            logger.info("✅ Using HTTP Basic authentication")
        else:
            logger.info("ℹ️  Making unauthenticated request")
        
        response = requests.get(url, headers=headers, auth=auth, timeout=30)
        
        logger.info(f"📡 Response status: {response.status_code}")
        logger.info(f"📡 Response headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            logger.error("❌ Authentication failed - check JIRA_USERNAME and JIRA_TOKEN")
            return
        elif response.status_code == 403:
            logger.error("❌ Access forbidden - user may not have permission to view this issue")
            return
        elif response.status_code == 404:
            logger.error("❌ Issue not found - check issue key and Jira base URL")
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
            logger.info("🔍 Inspecting Jira issue structure:")
            logger.info(f"   Issue Key: {data.get('key', 'N/A')}")
            logger.info(f"   Issue ID: {data.get('id', 'N/A')}")
            logger.info(f"   Self URL: {data.get('self', 'N/A')}")
            
            # Check fields
            fields = data.get('fields', {})
            logger.info("🔍 Inspecting issue fields:")
            
            # Common fields to check
            field_mappings = {
                'summary': 'Title',
                'description': 'Description',
                'status': 'Status',
                'assignee': 'Assignee',
                'reporter': 'Reporter',
                'priority': 'Priority',
                'labels': 'Labels',
                'created': 'Created',
                'updated': 'Updated',
                'resolutiondate': 'Resolution Date'
            }
            
            for field_key, field_name in field_mappings.items():
                if field_key in fields:
                    value = fields[field_key]
                    if isinstance(value, dict):
                        # For complex objects, show key properties
                        if field_key == 'status':
                            logger.info(f"   {field_name}: {value.get('name', 'N/A')} (id: {value.get('id', 'N/A')})")
                        elif field_key in ['assignee', 'reporter']:
                            logger.info(f"   {field_name}: {value.get('displayName', 'N/A')} ({value.get('emailAddress', 'N/A')})")
                        elif field_key == 'priority':
                            logger.info(f"   {field_name}: {value.get('name', 'N/A')}")
                        else:
                            logger.info(f"   {field_name}: {value}")
                    elif isinstance(value, list):
                        logger.info(f"   {field_name}: {value}")
                    else:
                        # For simple values, truncate if too long
                        value_str = str(value)
                        if len(value_str) > 100:
                            value_str = value_str[:97] + "..."
                        logger.info(f"   {field_name}: {value_str}")
                else:
                    logger.info(f"   {field_name}: [NOT AVAILABLE]")
            
            # Show description structure if it's ADF format
            description = fields.get('description')
            if description and isinstance(description, dict):
                logger.info("🔍 Description is in Atlassian Document Format (ADF):")
                logger.info(f"   Type: {description.get('type', 'N/A')}")
                logger.info(f"   Version: {description.get('version', 'N/A')}")
                content = description.get('content', [])
                logger.info(f"   Content blocks: {len(content)}")
                for i, block in enumerate(content[:3]):  # Show first 3 blocks
                    if isinstance(block, dict):
                        logger.info(f"     Block {i+1}: type={block.get('type', 'N/A')}")
            
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


def main():
    """Main test function."""
    # Default test URLs and issue keys
    test_cases = [
        {
            'url': 'https://warthogs.atlassian.net/browse/LM-1723',
            'issue_key': 'LM-1723',
            'description': 'Warthogs Jira issue (main test case)'
        },
        {
            'url': 'https://atlassian.atlassian.net/browse/JRASERVER-69444',
            'issue_key': 'JRASERVER-69444', 
            'description': 'Public Atlassian Jira issue (should be accessible)'
        },
        {
            'url': 'https://example.atlassian.net/browse/TEST-123',
            'issue_key': 'TEST-123',
            'description': 'Generic Jira issue format (will fail)'
        }
    ]
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        issue_key = sys.argv[1]
        # Try to determine base URL from issue key
        if issue_key.startswith('LM-'):
            base_url = 'https://warthogs.atlassian.net'
        else:
            base_url = os.environ.get("JIRA_BASE_URL", "https://example.atlassian.net")
        
        test_cases = [{
            'url': f'{base_url}/browse/{issue_key}',
            'issue_key': issue_key,
            'description': 'Command line provided issue'
        }]
    
    logger.info("🚀 Starting Jira issue fetching debug session")
    logger.info("=" * 60)
    
    # Show environment configuration
    logger.info("🔧 Environment Configuration:")
    logger.info(f"   JIRA_BASE_URL: {os.environ.get('JIRA_BASE_URL', 'Not set (will use default)')}")
    logger.info(f"   JIRA_USERNAME: {'Set' if os.environ.get('JIRA_USERNAME') else 'Not set'}")
    logger.info(f"   JIRA_TOKEN: {'Set' if os.environ.get('JIRA_TOKEN') else 'Not set'}")
    logger.info("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📋 Test Case {i}: {test_case['description']}")
        logger.info(f"URL: {test_case['url']}")
        logger.info(f"Issue Key: {test_case['issue_key']}")
        logger.info("-" * 40)
        
        # Test URL parsing
        parsed_issue_key = test_url_parsing(test_case['url'])
        
        # Test Jira API (use parsed issue key if available, otherwise fallback)
        issue_key_to_test = parsed_issue_key or test_case['issue_key']
        api_result = test_jira_api_direct(issue_key_to_test)
        
        # Test raw HTTP access for more detailed debugging
        test_jira_raw_access(issue_key_to_test)
        
        logger.info("=" * 60)
    
    logger.info("🏁 Debug session completed")
    logger.info("\n💡 Tips:")
    logger.info("   - Set JIRA_USERNAME and JIRA_TOKEN environment variables for authenticated requests")
    logger.info("   - Set JIRA_BASE_URL to test against different Jira instances")
    logger.info("   - Check network connectivity if requests fail")
    logger.info("   - Verify issue key format matches your Jira project naming")


if __name__ == "__main__":
    main()