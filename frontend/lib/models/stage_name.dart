// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'family_name.dart';

List<String> familyStages(FamilyName family) {
  switch (family) {
    case FamilyName.snap:
      return [
        'edge',
        'beta',
        'candidate',
        'stable',
      ];
    case FamilyName.deb:
      return [
        'proposed',
        'updates',
        '',
      ];
    case FamilyName.charm:
      return [
        'edge',
        'beta',
        'candidate',
        'stable',
      ];
    case FamilyName.image:
      return [
        'pending',
        'current',
      ];
    case FamilyName.solution:
      return [
        'edge',
        'beta',
        'candidate',
        'stable',
      ];
  }
}

const noStageLabel = '(no stage)';

String stageFilterLabel(String stage) {
  if (stage.isEmpty) return noStageLabel;
  // Quote a literal stage named like the empty-stage label to tell them apart.
  if (stage == noStageLabel) return '"$stage"';
  return stage;
}
