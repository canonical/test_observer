// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:test/test.dart';
import 'package:testcase_dashboard/routing.dart';
import 'package:testcase_dashboard/utils/artefact_sorting.dart';

import '../dummy_data.dart';

void main() {
  test('sortArtefacts sorts by reviewer query parameter', () {
    final artefacts = [
      dummyArtefact.copyWith(id: 1, name: 'zulu', reviewers: [dummyUser2]),
      dummyArtefact.copyWith(id: 2, name: 'alpha', reviewers: [dummyUser3]),
      dummyArtefact.copyWith(id: 3, name: 'middle', reviewers: []),
    ];

    sortArtefacts(
      {
        CommonQueryParameters.sortBy: ArtefactSortingQuery.reviewer.name,
      },
      artefacts,
    );

    expect(artefacts.map((artefact) => artefact.id).toList(), [2, 1, 3]);
  });
}
