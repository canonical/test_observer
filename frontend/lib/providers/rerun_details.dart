// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/family_name.dart';
import '../models/rerun_details.dart';
import 'api.dart';

part 'rerun_details.g.dart';

const rerunsPageSize = 50;

@riverpod
Future<RerunDetailsResponse> rerunDetails(
  Ref ref, {
  required FamilyName family,
  int? priority,
  int page = 1,
}) async {
  final api = ref.watch(apiProvider);
  final safePage = page < 1 ? 1 : page;
  return api.getRerunDetails(
    family: family,
    priority: priority,
    limit: rerunsPageSize,
    offset: (safePage - 1) * rerunsPageSize,
  );
}
