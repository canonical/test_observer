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

import 'family_name.dart';

enum StageName {
  edge,
  beta,
  candidate,
  stable,
  proposed,
  updates,
  pending,
  current
}

List<StageName> familyStages(FamilyName family) {
  switch (family) {
    case FamilyName.snap:
      return [
        StageName.edge,
        StageName.beta,
        StageName.candidate,
        StageName.stable,
      ];
    case FamilyName.deb:
      return [
        StageName.proposed,
        StageName.updates,
      ];
    case FamilyName.charm:
      return [
        StageName.edge,
        StageName.beta,
        StageName.candidate,
        StageName.stable,
      ];
    case FamilyName.image:
      return [
        StageName.pending,
        StageName.current,
      ];
  }
}
