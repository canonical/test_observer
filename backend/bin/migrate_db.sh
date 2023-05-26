#!/bin/bash

# 1. Bring application units to maintenance mode
# 2. Update application image resource (api-image resource)
# 3. Run migration action on one of the units
# 4. Scale unit count back up
# 5. Bring application units back to normal mode
