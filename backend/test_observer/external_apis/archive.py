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
import tempfile
from urllib.error import HTTPError
from debian.deb822 import Packages
import requests


def get_data_from_archive(arch: str, series: str, pocket: str, apt_repo: str) -> dict:
    """
    Get json data abourt deb packages from archive
    """
    if arch == "arm":
        archive_url = "ports.ubuntu.com/ubuntu-ports/dists"
    else:
        archive_url = "us.archive.ubuntu.com/ubuntu/dists"
    url = f"http://{archive_url}/{series}-{pocket}/{apt_repo}/binary-{arch}/Packages.gz"
    filepath = download_and_decompress_file(url)
    return filepath
    # return convert_packages_json(filepath)
    # return convert_meta_package_to_kernel_image("", filepath)


def download_and_decompress_file(url: str) -> str:
    """
    Download file from a specified url

    :url: the archive full url
    :return: filepath of the decompressed file
    """
    # Creating a temporary directory
    temp_dir = tempfile.gettempdir()

    filepath = url.split("/")[-1]
    gz_file_path = os.path.join(temp_dir, filepath)
    # Remove .gz extension
    decompressed_file_path = os.path.join(temp_dir, filepath[:-3])

    response = requests.get(url, stream=True)

    if not response.ok:
        raise HTTPError(
            url,
            code=response.status_code,
            msg=f"Cannot retrieve file from {url}",
            hdrs={},
            fp=StringIO(),
        )

    with open(gz_file_path, "wb") as file:
        file.write(response.content)

    with gzip.open(gz_file_path, "rb") as f_in:
        with open(decompressed_file_path, "wb") as f_out:
            f_out.write(f_in.read())

    os.remove(gz_file_path)
    return decompressed_file_path


def convert_packages_json(filepath) -> dict:
    """
    Convert Packages file from archive
    This function corresponds the method used by jenkins from the hwcert-jenkins-tools
    See https://git.launchpad.net/hwcert-jenkins-tools/tree/convert-packages-json

    :filepath: path to the Packages file
    :return: parsed dict (json)
    """
    json_data = {}

    with open(filepath, encoding="utf-8") as p_file:
        pkg_data = p_file.read()

    pkg_list = pkg_data.split("\n\n")
    for pkg in pkg_list:
        pkg_name = re.search("Package: (.+)", pkg)
        pkg_ver = re.search("Version: (.+)", pkg)
        if pkg_name and pkg_ver:
            # Periods in json keys are bad, convert them to _
            pkg_name_key = pkg_name.group(1).replace(".", "_")
            json_data[pkg_name_key] = pkg_ver.group(1)
    return json_data


def convert_meta_package_to_kernel_image(meta_pkg_name, filepath):
    """Convert package to its kernel image"""

    def get_package(pkg_name, filepath):
        """Extract package from decompressed Package file"""
        with open(filepath) as deb822_data:
            for package in Packages.iter_paragraphs(deb822_data):
                if package["Package"] == pkg_name:
                    return package
        return None

    def get_depends(package):
        """Get depends key from extracted package"""
        if "Depends" in package.keys():
            return [
                re.sub(r"\([^()]*\)", "", d).strip()
                for d in package["Depends"].split(",")
            ]
        return None

    def image_package(depends):
        for pack in depends:
            if pack.startswith("linux-image"):
                return pack
        return None

    def get_top_image(package, filepath):
        while True:
            deps = get_depends(package)
            imagepack = image_package(deps)
            if imagepack:
                break
            package = get_package(deps[0], filepath)
        return imagepack

    meta_package = get_package(meta_pkg_name, filepath)
    if not meta_package:
        raise ValueError("Did not find meta-package in repo package_data")
    top_image_pkg = get_top_image(meta_package, filepath)
    kernel_image_pkg = image_package(get_depends(get_package(top_image_pkg, filepath)))
    return kernel_image_pkg
