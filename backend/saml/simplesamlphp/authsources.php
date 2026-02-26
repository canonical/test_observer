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

$config = array(

    'admin' => array(
        'core:AdminPassword',
    ),

    // Creates a user with username: 'certbot' and password: 'password'
    // includes fullname and lp_teams keys just as Ubuntu One schema would
    'example-userpass' => array(
        'exampleauth:UserPass',
        'certbot:password' => array(
            'fullname' => 'Certification Bot',
            'lp_teams' => array('canonical-hw-cert'),
            'email' => 'certbot@canonical.com'
        ),
        'mark:password' => array(
            'fullname' => 'Mark',
            'lp_teams' => array('canonical'),
            'email' => 'mark@electricdemon.com'
        ),
    ),

);