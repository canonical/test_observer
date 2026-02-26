<?php

// Copyright 2025 Canonical Ltd.

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

/**
 * SAML 2.0 IdP configuration for SimpleSAMLphp.
 *
 * See: https://simplesamlphp.org/docs/stable/simplesamlphp-reference-idp-hosted
 */

$metadata['__DYNAMIC:1__'] = array(
        'host' => '__DEFAULT__',

        'privatekey' => 'server.pem',
        'certificate' => 'server.crt',

        'auth' => 'example-userpass',

        // Use emailAddress NameIdFormat
        'authproc' => [
            100 => [
                'class' => 'saml:AttributeNameID',
                'attribute' => 'email',
                'Format' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
            ],
        ],
);