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

part 'execution_metadata.freezed.dart';

@freezed
abstract class ExecutionMetadata with _$ExecutionMetadata {
  const ExecutionMetadata._();
  const factory ExecutionMetadata({
    @Default({}) Map<String, Set<String>> data,
  }) = _ExecutionMetadata;

  factory ExecutionMetadata.fromJson(Map<String, Object?> json) {
    return ExecutionMetadata(
      data: json.map(
        (k, v) => MapEntry(
          k,
          (v as List).map((e) => e.toString()).toSet(),
        ),
      ),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'data': data,
    };
  }

  factory ExecutionMetadata.fromRows(Set<(String, String)> rows) {
    final Map<String, Set<String>> data = {};
    for (final (category, value) in rows) {
      data.putIfAbsent(category, () => {}).add(value);
    }
    return ExecutionMetadata(data: data);
  }

  Set<(String, String)> toRows() {
    final Set<(String, String)> rows = {};
    data.forEach((category, values) {
      for (final value in values) {
        rows.add((category, value));
      }
    });
    return rows;
  }

  factory ExecutionMetadata.fromQueryParams(List<String>? params) {
    final Set<(String, String)> rows = {};
    for (final param in params ?? <String>[]) {
      final pairs = param.split(',').where((s) => s.isNotEmpty);
      for (final pair in pairs) {
        final parts = pair.split(':');
        if (parts.length == 2) {
          final category = Uri.decodeComponent(parts[0]);
          final value = Uri.decodeComponent(parts[1]);
          if (category.isNotEmpty && value.isNotEmpty) {
            rows.add((category, value));
          }
        }
      }
    }
    return ExecutionMetadata.fromRows(rows);
  }

  List<String> toQueryParams() {
    return toRows()
        .map(
          (row) =>
              '${Uri.encodeComponent(row.$1)}:${Uri.encodeComponent(row.$2)}',
        )
        .toList();
  }

  List<String> toStrings() {
    return toRows().map((row) => '${row.$1} ${row.$2}').toList();
  }

  (String, String) findFromString(String s) {
    return toRows().firstWhere((row) => '${row.$1} ${row.$2}' == s);
  }

  bool get isEmpty => data.isEmpty;
  bool get isNotEmpty => !isEmpty;
}
