<?php

// Copyright 2026 Canonical Ltd.

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: AGPL-3.0-only

$config['production'] = false;
$config['theme.header'] = 'Test Observer IdP';
$config['enable.saml20-idp'] = true;
$config['module.enable']['exampleauth'] = true;

// Local development is served over plain HTTP, so cookies must not be flagged
// secure (the browser would otherwise drop them on http:// connections).
$config['session.cookie.secure'] = false;

// The default config uses SameSite=None, which browsers only accept on secure
// (HTTPS) cookies. Since local dev serves the IdP over plain HTTP with
// non-secure cookies, SameSite=None would be rejected and the session cookie
// silently dropped (causing SimpleSAMLphp's "Missing cookie" error). Use Lax,
// which is valid for non-secure cookies and sufficient for the SAML flow.
$config['session.cookie.samesite'] = 'Lax';
