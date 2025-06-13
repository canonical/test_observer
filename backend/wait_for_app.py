#!/usr/bin/env python3
"""
Application readiness check script for Test Observer backend.
Waits for the FastAPI application to be ready to accept requests.
"""

import time
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def wait_for_application(base_url: str = "http://localhost:30000", max_retries: int = 30, retry_interval: int = 2):
    """Wait for the FastAPI application to be ready."""
    health_url = f"{base_url}/v1/version"
    
    print(f"Checking application readiness at: {health_url}")
    
    # Configure requests session with retries
    session = requests.Session()
    retry_strategy = Retry(
        total=0,  # We'll handle retries manually for better logging
        connect=0,
        read=0,
        status=0,
        backoff_factor=0
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    for attempt in range(max_retries):
        try:
            response = session.get(health_url, timeout=5)
            if response.status_code == 200:
                print("Application is ready!")
                return True
                
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout, 
                requests.exceptions.RequestException) as e:
            if attempt == max_retries - 1:
                print(f"Application readiness check failed after {max_retries} attempts: {e}")
                return False
                
            print(f"Application not ready, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(retry_interval)
    
    return False


if __name__ == '__main__':
    success = wait_for_application()
    sys.exit(0 if success else 1)