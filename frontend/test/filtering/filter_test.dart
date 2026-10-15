// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:test/test.dart';
import 'package:testcase_dashboard/filtering/filter.dart';

void main() {
  const items = [
    _FilterItem('first', ['alice', 'bob']),
    _FilterItem('second', ['bob', 'carol']),
    _FilterItem('third', ['dave']),
  ];

  final filter = createFilterFromListExtractor<_FilterItem>(
    'Reviewer',
    (item) => item.options,
  );

  test('extractOptions returns the union of options across all items', () {
    expect(
      filter.extractOptions(items),
      equals({'alice', 'bob', 'carol', 'dave'}),
    );
  });

  test('filter returns items when any extracted option is selected', () {
    expect(
      filter.filter(items, {'bob', 'dave'}),
      equals([items[0], items[1], items[2]]),
    );
  });

  test('filter excludes items that have no matching option', () {
    expect(
      filter.filter(items, {'alice'}),
      equals([items[0]]),
    );
  });

  test('filter returns an empty list when no items match', () {
    expect(filter.filter(items, {'eve'}), isEmpty);
  });

  test('filter returns all items when all items have a matching option', () {
    expect(
      filter.filter(items, {'alice', 'carol', 'dave'}),
      equals(items),
    );
  });
}

class _FilterItem {
  const _FilterItem(this.name, this.options);

  final String name;
  final List<String> options;
}
