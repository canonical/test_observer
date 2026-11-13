// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/filtering/artefact_filters.dart';
import 'package:testcase_dashboard/models/family_name.dart';

import '../dummy_data.dart';

void main() {
  test('legacy pocket links match empty stages, not unrelated filters', () {
    final params = <String, List<String>>{
      'Pocket': ['empty'],
      'Series': ['empty'],
    };
    final pocket = getArtefactFiltersFor(FamilyName.deb)
        .firstWhere((f) => f.name == 'Pocket');
    final empty = dummyArtefact.copyWith(stage: '');
    final literal = dummyArtefact.copyWith(id: 2, stage: 'empty');
    expect(
      pocket.filter(
        [empty, literal],
        selectedArtefactFilterOptions('Pocket', params),
      ),
      [empty],
    );
    expect(selectedArtefactFilterOptions('Series', params), {'empty'});

    params[stageFilterFormat] = ['2'];
    expect(
      pocket.filter(
        [empty, literal],
        selectedArtefactFilterOptions('Pocket', params),
      ),
      [literal],
    );
  });
}
