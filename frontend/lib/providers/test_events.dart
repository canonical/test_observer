// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_event.dart';
import 'api.dart';

part 'test_events.g.dart';

@riverpod
Future<List<TestEvent>> testEvents(Ref ref, int testExecutionId) async {
  final api = ref.watch(apiProvider);
  return await api.getTestExecutionEvents(testExecutionId);
}
