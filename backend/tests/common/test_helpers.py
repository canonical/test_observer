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

from test_observer.common.helpers import normalize_contains_terms


def test_normalize_contains_terms_strips_and_drops_empty_values():
    assert normalize_contains_terms(["  desktop  ", "", "   ", "jammy"]) == ["desktop", "jammy"]


def test_normalize_contains_terms_escapes_like_metacharacters():
    assert normalize_contains_terms([r"foo%bar_baz\\qux"]) == [r"foo\%bar\_baz\\\\qux"]


def test_normalize_contains_terms_handles_none_or_empty_input():
    assert normalize_contains_terms(None) == []
    assert normalize_contains_terms([]) == []
