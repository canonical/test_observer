#!/bin/bash

# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

set -e

echo "Fetching Flutter dependencies..."
flutter pub get

echo "Generating code (blocking, so *.g.dart / *.freezed.dart are fresh before first compile)..."
dart run build_runner build --delete-conflicting-outputs

echo "Starting build_runner in watch mode (regenerates code on subsequent changes)..."
dart run build_runner watch --delete-conflicting-outputs &

# Feed the Flutter dev server's stdin through a FIFO so we can drive it
# non-interactively. A file watcher writes "R" (hot restart) to the FIFO
# whenever a source file changes, giving automatic reload on save without
# needing to attach a TTY to the container.
FIFO=/tmp/flutter-stdin
rm -f "$FIFO"
mkfifo "$FIFO"
# Hold the FIFO open for writing so it never receives EOF.
exec 3<>"$FIFO"

echo "Watching lib/ and web/ for changes to trigger automatic hot restart..."
(
    while inotifywait -q -r -e modify,create,delete,move \
        --include '\.(dart|yaml|json|html)$' lib web >/dev/null 2>&1; do
        # Debounce bursts of file events (e.g. build_runner regenerating files).
        sleep 1
        echo "R" >&3
    done
) &

echo "Starting Flutter web dev server (hot restart on save)..."
# --web-hostname 0.0.0.0 so the server is reachable from outside the container.
exec flutter run \
    -d web-server \
    --web-hostname 0.0.0.0 \
    --web-port 80 \
    <&3
