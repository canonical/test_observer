#!/bin/bash

# Find all integration test files
TEST_FILES=$(find integration_test -name "*_test.dart")

# Run each test file
for TEST_FILE in $TEST_FILES; do
    flutter drive --target="$TEST_FILE" --driver test_driver/integration_test.dart -d web-server
done
