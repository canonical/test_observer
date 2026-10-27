-- Copyright 2026 Canonical Ltd.
--
-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU Affero General Public License version 3, as
-- published by the Free Software Foundation.
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU Affero General Public License for more details.
-- You should have received a copy of the GNU Affero General Public License
-- along with this program.  If not, see <https://www.gnu.org/licenses/>.
--
-- SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
-- SPDX-License-Identifier: AGPL-3.0-only

BEGIN;

-- Remove login sessions and replace personal identity data while preserving
-- users and their existing reviewer/team relationships in the snapshot.
DELETE FROM user_session;
UPDATE app_user
SET email = 'snapshot-user-' || id || '@example.invalid',
    name = 'Snapshot user ' || id,
    launchpad_handle = NULL;

-- Keep application names and permissions, but invalidate every restored key.
UPDATE application
SET api_key = 'to_' || replace(gen_random_uuid()::text, '-', '');

COMMIT;
