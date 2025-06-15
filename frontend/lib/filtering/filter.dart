// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:dartx/dartx.dart';

class Filter<T> {
  const Filter({
    required this.name,
    required this.filter,
    required this.extractOptions,
  });

  final String name;
  final List<T> Function(List<T> items, Set<String> options) filter;
  final Set<String> Function(List<T> items) extractOptions;
}

Filter<T> createFilterFromExtractor<T>(
  String name,
  String Function(T) extractOption,
) =>
    Filter(
      name: name,
      extractOptions: (items) => items.map(extractOption).toSet(),
      filter: (items, options) => items
          .filter((item) => options.contains(extractOption(item)))
          .toList(),
    );
