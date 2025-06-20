#!/usr/bin/env python3
# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Database readiness check script for Test Observer backend.
Waits for the database to be ready before allowing the application to start.
"""

import logging
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
    
    logger = logging.getLogger("test-observer-backend")
    logger.info(
        "Connecting to database: %s",
        db_url.split('@')[1] if '@' in db_url else 'unknown'
    )
    engine = create_engine(db_url)
    
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            logger.info('Database is ready!')
            return True
            
        except (OperationalError, Exception) as e:
            if attempt == max_retries - 1:
                logger.error(
                    'Database connection failed after %d attempts: %s',
                    max_retries, e
                )
                return False
                
            logger.info(
                'Database not ready, retrying... (%d/%d)',
                attempt + 1, max_retries
            )
            time.sleep(retry_interval)
    
    return False


if __name__ == '__main__':
    success = wait_for_database()
    sys.exit(0 if success else 1)