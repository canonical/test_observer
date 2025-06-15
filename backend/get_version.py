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

import subprocess
import shutil


def get_git_version_info(fallback_version="0.0.0"):
    """
    Retrieves version information for the package from git.

    Args:
        fallback_version (str): The version to return if git is unavailable or an error occurs.

    Returns:
        str: The version string in the format 'latest_tag.commit_count.short_rev',
             or '0.0.0.0.short_rev' if no tags are found, or the fallback version if git is unavailable.

    Example:
        >>> import subprocess
        >>> subprocess.check_output = lambda cmd, stderr=None: b'v1.2.3\\n' if 'tag' in cmd else b'5' if 'rev-list' in cmd else b'abc123'
        >>> get_git_version_info()
        '1.2.3-5+abc123'
    """
    if shutil.which("git"):
        # Get the most recent version tag
        tags = (
            subprocess.check_output(
                ["git", "tag", "--list", "v*"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
            .split("\n")
        )

        if tags and tags[0]:
            latest_tag = sorted(
                tags,
                key=lambda t: [
                    int(n) if n.isdigit() else n
                    for n in t.lstrip("v").replace("-", ".").split(".")
                ],
            )[-1]

            # Get commit count since the tag
            commit_count = (
                subprocess.check_output(
                    ["git", "rev-list", "--count", f"{latest_tag}..HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )

            # Get short revision
            short_rev = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )

            return f"{latest_tag.lstrip('v')}-{commit_count}+{short_rev}"
        else:
            # Fallback if no tags found
            short_rev = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            return f"0.0.0-{short_rev}"
    else:
        return fallback_version


if __name__ == "__main__":
    import sys

    fallback = sys.argv[1] if len(sys.argv) > 1 else "0.0.0"
    print(get_git_version_info(fallback))
