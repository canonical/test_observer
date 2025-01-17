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

import 'package:freezed_annotation/freezed_annotation.dart';

part 'filter.freezed.dart';

@freezed
class Filter<T> with _$Filter<T> {
  const Filter._();

  const factory Filter({
    required String name,
    required String? Function(T) extractOption,
    @Default(<String>{}) Set<String> selectedOptions,
    @Default(<String>[]) List<String> detectedOptions,
  }) = _Filter<T>;

  bool doesObjectPassFilter(T object) {
    return selectedOptions.isEmpty ||
        selectedOptions.contains(extractOption(object));
  }
}
