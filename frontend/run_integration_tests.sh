#!/bin/bash

# Copyright 2024 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

# Find all integration test files
TEST_FILES=$(find integration_test -name "*_test.dart")

# Run each test file
for TEST_FILE in $TEST_FILES; do
    flutter drive --target="$TEST_FILE" --driver test_driver/integration_test.dart -d web-server
done
