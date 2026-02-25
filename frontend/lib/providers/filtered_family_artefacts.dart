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

import 'dart:collection';

import 'package:dartx/dartx.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../filtering/artefact_filters.dart';
import '../models/artefact.dart';
import '../routing.dart';
import '../utils/artefact_sorting.dart';
import 'family_artefacts.dart';

part 'filtered_family_artefacts.g.dart';

@riverpod
LinkedHashMap<int, Artefact> filteredFamilyArtefacts(Ref ref, Uri pageUri) {
  final family = AppRoutes.familyFromUri(pageUri);
  final searchValue =
      pageUri.queryParameters[CommonQueryParameters.searchQuery] ?? '';
  final parameters = pageUri.queryParametersAll;

  var artefacts =
      ref.watch(familyArtefactsProvider(family)).value?.values.toList() ?? [];

  for (var filter in getArtefactFiltersFor(family)) {
    final filterOptions = parameters[filter.name];
    if (filterOptions != null) {
      artefacts = filter.filter(artefacts, filterOptions.toSet());
    }
  }

  artefacts = artefacts
      .filter((a) => a.name.toLowerCase().contains(searchValue.toLowerCase()))
      .toList();

  sortArtefacts(pageUri.queryParameters, artefacts);

  return LinkedHashMap.fromIterable(
    artefacts,
    key: (a) => a.id,
    value: (a) => a,
  );
}
