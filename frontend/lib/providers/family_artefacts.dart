// Copyright (C) 2023-2025 Canonical Ltd.
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

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'api.dart';

part 'family_artefacts.g.dart';

@riverpod
Future<Map<int, Artefact>> familyArtefacts(
  FamilyArtefactsRef ref,
  FamilyName family,
) {
  final api = ref.watch(apiProvider);
  return api.getFamilyArtefacts(family);
}
