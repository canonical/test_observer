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
 * SAML 2.0 remote SP metadata for SimpleSAMLphp.
 *
 * Registers the Test Observer backend as a Service Provider so the IdP will
 * issue assertions for it.
 *
 * See: https://simplesamlphp.org/docs/stable/simplesamlphp-reference-sp-remote
 */

$metadata['http://localhost:30000'] = [
    'AssertionConsumerService' => [
        [
            'index' => 1,
            'isDefault' => true,
            'Location' => 'http://localhost:30000/v1/auth/saml/acs',
            'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
        ],
    ],
    'SingleLogoutService' => [
        [
            'Location' => 'http://localhost:30000/v1/auth/saml/sls',
            'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
        ],
    ],
];
