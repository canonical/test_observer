# Copyright 2023 Canonical Ltd.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Written by:
#        Nadzeya Hutsko <nadzeya.hutsko@canonical.com>
#        Jonathan Cave <jonathan.cave@canonical.com>
"""Functions for managing data from archive"""


import os
from io import StringIO
import re
import gzip
import random
import string
import tempfile
from urllib.error import HTTPError
import requests
from types import TracebackType
import logging


logger = logging.getLogger("test-observer-backend")


class ArchiveManager:
    """Class for working with deb packages from archive"""

    def __init__(self, arch: str, series: str, pocket: str, apt_repo: str):
        """
        Get json data abourt deb packages from archive

        :arch: deb architecture
        :series: deb series (e.g. focal, jammy)
        :pocket: deb pocket ("proposed" or "updates")
        :apt_repo: repo on archive (e.g. main, universe)
        """
        if arch == "arm":
            archive_url = "ports.ubuntu.com/ubuntu-ports/dists"
        else:
            archive_url = "us.archive.ubuntu.com/ubuntu/dists"
        self.url = f"http://{archive_url}/{series}-{pocket}/{apt_repo}/binary-{arch}/Packages.gz"
        logger.debug(self.url)

    def __enter__(self):
        self._create_download_and_extract_filepaths()
        self._download_data()
        self._decompress_data()
        return self

    def __exit__(
        self,
        exctype: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ):
        logger.error(value)
        os.remove(self.gz_filepath)
        os.remove(self.decompressed_filepath)

    def get_deb_version(self, debname: str) -> str:
        """
        Convert Packages file from archive to json and get version from it
        This function corresponds the method used by jenkins from the
        hwcert-jenkins-tools
        See https://git.launchpad.net/hwcert-jenkins-tools/tree/convert-packages-json

        :debname: name of the deb package
        :return: deb version
        """
        json_data = {}

        with open(self.decompressed_filepath, encoding="utf-8") as p_file:
            pkg_data = p_file.read()

        pkg_list = pkg_data.split("\n\n")
        for pkg in pkg_list:
            pkg_name = re.search("Package: (.+)", pkg)
            pkg_ver = re.search("Version: (.+)", pkg)
            if pkg_name and pkg_ver:
                # Periods in json keys are bad, convert them to _
                pkg_name_key = pkg_name.group(1).replace(".", "_")
                json_data[pkg_name_key] = pkg_ver.group(1)
        return json_data.get(debname)

    def _create_download_and_extract_filepaths(self) -> None:
        """
        Create filepaths in temp dir for downloading and extracting Packages.gz file
        """
        # Creating a temporary directory
        temp_dir = tempfile.gettempdir()

        filepath = self.url.split("/")[-1] + "".join(
            random.choice(string.ascii_lowercase) for i in range(10)
        )
        self.gz_filepath = os.path.join(temp_dir, filepath)
        # Remove .gz extension
        self.decompressed_filepath = os.path.join(
            temp_dir,
            filepath[:-3]
            + "".join(random.choice(string.ascii_lowercase) for i in range(10)),
        )
        logger.debug("Compressed filepath: %s", self.gz_filepath)
        logger.debug("Decompressed filepath: %s", self.decompressed_filepath)

    def _download_data(self) -> None:
        """Download Packages.gz file from archive"""
        response = requests.get(self.url, stream=True)
        if not response.ok:
            raise HTTPError(
                self.url,
                code=response.status_code,
                msg=f"Cannot retrieve file from {self.url}",
                hdrs={},
                fp=StringIO(),
            )

        with open(self.gz_filepath, "wb") as file:
            file.write(response.content)

    def _decompress_data(self) -> None:
        """Decompress the downloaded data"""
        with gzip.open(self.gz_filepath, "rb") as f_in, open(
            self.decompressed_filepath, "wb"
        ) as f_out:
            f_out.write(f_in.read())
