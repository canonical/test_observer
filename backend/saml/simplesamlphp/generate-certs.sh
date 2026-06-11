#!/bin/bash

# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

# Generate a self-signed SAML keypair for local development if not already present.
set -e

CERT_DIR=/var/simplesamlphp/cert

if [ ! -f "${CERT_DIR}/server.pem" ]; then
    openssl req -newkey rsa:2048 -new -x509 -days 3652 -nodes \
        -out "${CERT_DIR}/server.crt" \
        -keyout "${CERT_DIR}/server.pem" \
        -subj '/C=NA/ST=NA/L=NA/O=TestObserver/OU=Dev/CN=localhost'
    chmod 644 "${CERT_DIR}/server.crt"
    chmod 640 "${CERT_DIR}/server.pem"
    chown root:www-data "${CERT_DIR}/server.pem"
fi
