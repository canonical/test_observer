// Copyright (C) 2024 Canonical Ltd.
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

import '../models/artefact.dart' as artefact_model;
import 'api.dart';

part 'artefact.g.dart';

@riverpod
class Artefact extends _$Artefact {
  @override
  Future<artefact_model.Artefact> build(int artefactId) {
    final api = ref.watch(apiProvider);
    return api.getArtefact(artefactId);
  }

  Future<void> changeArtefactStatus(
    id,
    artefact_model.ArtefactStatus status,
  ) async {
    final api = ref.read(apiProvider);
    final artefact = await api.changeArtefactStatus(artefactId, status);
    state = AsyncData(artefact);
  }

  Future<void> updateCompletedEnvironmentReviewsCount(int count) async {
    final artefact = await future;
    state =
        AsyncData(artefact.copyWith(completedEnvironmentReviewsCount: count));
  }
}
