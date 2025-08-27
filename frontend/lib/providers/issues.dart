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

import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/issue.dart';
import 'api.dart';

part 'issues.g.dart';

@riverpod
Future<Issue> createIssue(
  Ref ref, {
  required String url,
  String? title,
  String? description,
  String? status,
}) async {
  final api = ref.read(apiProvider);
  return await api.createIssue(
    url: url,
    title: title,
    description: description,
    status: status,
  );
}
