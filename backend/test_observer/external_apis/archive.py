"""Functions for managing data from archive"""

import gzip
import logging
import os
import random
import re
import string
import tempfile
from types import TracebackType

import requests

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
        if arch.startswith("arm"):
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

    def get_deb_version(self, debname: str) -> str | None:
        """
        Retrieve deb package version via the name

        :debname: name of the deb package (assumes that any '_' could be a '.')
        :return: deb version
        """
        with open(self.decompressed_filepath, encoding="utf-8") as p_file:
            pkg_data = p_file.read()

        # Names of deb packages could have swapped '.' with '_'
        # So this regex is to allow such scenarios
        name_regex = f"^{debname}$".replace("_", "[_\.]")

        pkg_list = pkg_data.split("\n\n")
        for pkg in pkg_list:
            pkg_name = re.search("Package: (.+)", pkg)
            pkg_ver = re.search("Version: (.+)", pkg)

            if pkg_name and pkg_ver and re.match(name_regex, pkg_name.group(1)):
                return pkg_ver.group(1)

        return None

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
        response = requests.get(self.url, stream=True, timeout=30)
        if not response.ok:
            response.raise_for_status()

        with open(self.gz_filepath, "wb") as file:
            file.write(response.content)

    def _decompress_data(self) -> None:
        """Decompress the downloaded data"""
        with (
            gzip.open(self.gz_filepath, "rb") as f_in,
            open(self.decompressed_filepath, "wb") as f_out,
        ):
            f_out.write(f_in.read())
