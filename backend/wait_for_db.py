#!/usr/bin/env python3
"""
Database readiness check script for Test Observer backend.
Waits for the database to be ready before allowing the application to start.
"""

import os
import sys
import time
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def wait_for_database():
    """Wait for database to be ready with retry logic."""
    db_url = os.getenv(
        'DB_URL', 
        'postgresql+pg8000://test_observer_user:test_observer_password@test-observer-db:5432/test_observer_db'
    )
    
    print(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")
    engine = create_engine(db_url)
    
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            print('Database is ready!')
            return True
            
        except (OperationalError, Exception) as e:
            if attempt == max_retries - 1:
                print(f'Database connection failed after {max_retries} attempts: {e}')
                return False
                
            print(f'Database not ready, retrying... ({attempt + 1}/{max_retries})')
            time.sleep(retry_interval)
    
    return False


if __name__ == '__main__':
    success = wait_for_database()
    sys.exit(0 if success else 1)