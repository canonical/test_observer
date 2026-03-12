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

import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'environment.dart';
import 'environment_review.dart';
import 'test_execution.dart';

part 'artefact_environment.freezed.dart';

@freezed
abstract class ArtefactEnvironment with _$ArtefactEnvironment {
  const ArtefactEnvironment._();

  const factory ArtefactEnvironment({
    required SortedList<TestExecution> runsDescending,
    required EnvironmentReview review,
  }) = _ArtefactEnvironment;

  String get name => review.environment.name;
  String get architecture => review.environment.architecture;
  Environment get environment => review.environment;
}
