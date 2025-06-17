#!/usr/bin/env python3
"""
Dedicated test program for debugging Launchpad issue fetching.

This script allows for isolated testing and debugging of the Launchpad API
integration without affecting the main application.

Usage:
    python debug_launchpad.py [bug_number]
    
Examples:
    python debug_launchpad.py 2091878
    python debug_launchpad.py 1979671
    python debug_launchpad.py 2089015
    
Credentials:
    Set LAUNCHPAD_CONSUMER_NAME, LAUNCHPAD_OAUTH_TOKEN, and LAUNCHPAD_OAUTH_TOKEN_SECRET
    environment variables for authenticated access to private bugs.
"""

import sys
import os
import logging
import traceback
from typing import Optional

# Set up logging to see debug information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our Launchpad API classes
try:
    from test_observer.external_apis.issue_tracking.launchpad_bug_api import LaunchpadBugAPI
    from test_observer.external_apis.issue_tracking.url_parser import IssueURLParser
    from test_observer.external_apis.issue_tracking.models import IssueInfo, ParsedIssueURL
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this from the backend directory with the proper environment")
    sys.exit(1)


def test_url_parsing(url: str) -> Optional[str]:
    """Test URL parsing for a given Launchpad URL."""
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


def test_launchpad_api_direct(bug_number: str) -> Optional[IssueInfo]:
    """Test direct Launchpad API access for a bug number."""
    logger.info(f"Testing direct Launchpad API access for bug: {bug_number}")
    
    # Check for credentials
    consumer_name = os.getenv("LAUNCHPAD_CONSUMER_NAME")
    oauth_token = os.getenv("LAUNCHPAD_OAUTH_TOKEN")
    oauth_token_secret = os.getenv("LAUNCHPAD_OAUTH_TOKEN_SECRET")
    
    if consumer_name and oauth_token and oauth_token_secret:
        logger.info("🔐 Using authenticated Launchpad access")
        logger.info(f"   Consumer: {consumer_name}")
        logger.info(f"   Token: {oauth_token[:10]}...")
    else:
        logger.info("👤 Using anonymous Launchpad access")
        logger.info("   Set LAUNCHPAD_CONSUMER_NAME, LAUNCHPAD_OAUTH_TOKEN, and LAUNCHPAD_OAUTH_TOKEN_SECRET for authenticated access")
    
    try:
        api = LaunchpadBugAPI()
        logger.info("✅ LaunchpadBugAPI initialized successfully")
        
        # Test the get_bug method
        result = api.get_bug(bug_number)
        
        if result:
            logger.info(f"✅ Bug fetched successfully:")
            logger.info(f"   External ID: {result.external_id}")
            logger.info(f"   Title: {result.title}")
            logger.info(f"   Status: {result.status}")
            logger.info(f"   URL: {result.url}")
            logger.info(f"   Last Updated: {result.last_updated}")
            logger.info(f"   Assignee: {result.assignee}")
            logger.info(f"   Labels: {result.labels}")
            logger.info(f"   Description: {result.description[:100] if result.description else 'None'}...")
        else:
            logger.warning(f"⚠️  Bug fetch returned None (bug may be private or deleted)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Launchpad API failed with exception: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


def test_launchpad_raw_access(bug_number: str):
    """Test raw launchpadlib access to understand the bug object structure."""
    logger.info(f"Testing raw launchpadlib access for bug: {bug_number}")
    
    # Check for credentials
    consumer_name = os.getenv("LAUNCHPAD_CONSUMER_NAME")
    oauth_token = os.getenv("LAUNCHPAD_OAUTH_TOKEN")
    oauth_token_secret = os.getenv("LAUNCHPAD_OAUTH_TOKEN_SECRET")
    
    try:
        from launchpadlib.launchpad import Launchpad
        from lazr.restfulclient.errors import NotFound
        
        # Connect with credentials if available
        if consumer_name and oauth_token and oauth_token_secret:
            logger.info("🔐 Using authenticated Launchpad connection")
            try:
                launchpad = Launchpad.login(
                    consumer_name=consumer_name,
                    token_string=oauth_token,
                    access_secret=oauth_token_secret,
                    service_root="production",
                    version="devel"
                )
                logger.info("✅ Authenticated Launchpad connection established")
            except Exception as e:
                logger.warning(f"Failed to authenticate: {e}")
                logger.info("Falling back to anonymous connection")
                launchpad = Launchpad.login_anonymously(
                    "test-observer-debug", "production", version="devel"
                )
        else:
            logger.info("👤 Using anonymous Launchpad connection")
            launchpad = Launchpad.login_anonymously(
                "test-observer-debug", "production", version="devel"
            )
            
        logger.info("✅ Raw Launchpad connection established")
        
        # Try to access the bug directly
        try:
            bug = launchpad.bugs[bug_number]
            logger.info(f"✅ Bug object retrieved: {bug}")
            
            # Inspect available attributes
            logger.info("🔍 Inspecting bug object attributes:")
            
            # Check common attributes safely
            attributes_to_check = [
                'status', 'title', 'description', 'date_created', 'date_last_updated',
                'assignee', 'tags', 'importance', 'heat', 'duplicate_of', 'private'
            ]
            
            for attr in attributes_to_check:
                try:
                    if hasattr(bug, attr):
                        value = getattr(bug, attr)
                        logger.info(f"   {attr}: {value}")
                    else:
                        logger.info(f"   {attr}: [NOT AVAILABLE]")
                except Exception as e:
                    logger.warning(f"   {attr}: [ERROR: {type(e).__name__}: {e}]")
            
            # Try to access bug tasks (this might be where status information is)
            try:
                logger.info("🔍 Inspecting bug tasks:")
                for task in bug.bug_tasks:
                    logger.info(f"   Task: {task}")
                    task_attrs = ['status', 'importance', 'assignee', 'target']
                    for attr in task_attrs:
                        try:
                            value = getattr(task, attr)
                            logger.info(f"     {attr}: {value}")
                        except Exception as e:
                            logger.warning(f"     {attr}: [ERROR: {type(e).__name__}: {e}]")
            except Exception as e:
                logger.warning(f"Could not access bug_tasks: {type(e).__name__}: {e}")
            
        except (KeyError, NotFound) as e:
            logger.warning(f"⚠️  Bug not found or not accessible: {type(e).__name__}: {e}")
        except Exception as e:
            logger.error(f"❌ Raw bug access failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            
    except Exception as e:
        logger.error(f"❌ Raw Launchpad connection failed: {type(e).__name__}: {e}")
        traceback.print_exc()


def main():
    """Main test function."""
    # Default test URLs and bug numbers
    test_cases = [
        {
            'url': 'https://bugs.launchpad.net/ubuntu/+source/linux-signed-hwe-6.8/+bug/2091878',
            'bug_number': '2091878',
            'description': 'Complex URL with +source (main test case)'
        },
        {
            'url': 'https://bugs.launchpad.net/ubuntu/+bug/1979671',
            'bug_number': '1979671', 
            'description': 'Simple ubuntu bug'
        },
        {
            'url': 'https://bugs.launchpad.net/bugs/2089015',
            'bug_number': '2089015',
            'description': 'Direct bugs URL format'
        }
    ]
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        bug_number = sys.argv[1]
        test_cases = [{
            'url': f'https://bugs.launchpad.net/bugs/{bug_number}',
            'bug_number': bug_number,
            'description': 'Command line provided bug'
        }]
    
    logger.info("🚀 Starting Launchpad issue fetching debug session")
    logger.info("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📋 Test Case {i}: {test_case['description']}")
        logger.info(f"URL: {test_case['url']}")
        logger.info(f"Bug Number: {test_case['bug_number']}")
        logger.info("-" * 40)
        
        # Test URL parsing
        parsed_bug_number = test_url_parsing(test_case['url'])
        
        # Test Launchpad API (use parsed bug number if available, otherwise fallback)
        bug_number_to_test = parsed_bug_number or test_case['bug_number']
        api_result = test_launchpad_api_direct(bug_number_to_test)
        
        # Test raw launchpadlib access for more detailed debugging
        test_launchpad_raw_access(bug_number_to_test)
        
        logger.info("=" * 60)
    
    logger.info("🏁 Debug session completed")


if __name__ == "__main__":
    main()