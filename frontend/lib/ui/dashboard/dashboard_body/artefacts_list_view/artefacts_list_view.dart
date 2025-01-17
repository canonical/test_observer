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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../models/artefact.dart';
import '../../../../providers/filtered_family_artefacts.dart';
import '../../../../routing.dart';
import '../../../../utils/artefact_sorting.dart';

part 'row.dart';
part 'headers.dart';
part 'column_metadata.dart';

class ArtefactsListView extends ConsumerWidget {
  const ArtefactsListView({
    super.key,
    required this.listHeader,
    required this.listItemBuilder,
  });

  final Widget listHeader;
  final Widget Function(Artefact) listItemBuilder;

  const ArtefactsListView.snaps({super.key})
      : listHeader = const _Headers.snaps(key: PageStorageKey('Header')),
        listItemBuilder = _snapsListItemBuilder;

  static Widget _snapsListItemBuilder(Artefact artefact) {
    return _Row.snap(key: PageStorageKey(artefact.id), artefact: artefact);
  }

  const ArtefactsListView.debs({super.key})
      : listHeader = const _Headers.debs(key: PageStorageKey('Header')),
        listItemBuilder = _debsListItemBuilder;

  static Widget _debsListItemBuilder(Artefact artefact) {
    return _Row.deb(key: PageStorageKey(artefact.id), artefact: artefact);
  }

  const ArtefactsListView.charms({super.key})
      : listHeader = const _Headers.charms(key: PageStorageKey('Header')),
        listItemBuilder = _charmsListItemBuilder;

  static Widget _charmsListItemBuilder(Artefact artefact) {
    return _Row.charm(key: PageStorageKey(artefact.id), artefact: artefact);
  }

  const ArtefactsListView.images({super.key})
      : listHeader = const _Headers.images(key: PageStorageKey('Header')),
        listItemBuilder = _imagesListItemBuilder;

  static Widget _imagesListItemBuilder(Artefact artefact) {
    return _Row.image(key: PageStorageKey(artefact.id), artefact: artefact);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final artefacts =
        ref.watch(filteredFamilyArtefactsProvider(pageUri)).values.toList();

    return Align(
      alignment: Alignment.topLeft,
      child: SizedBox(
        width: 1300,
        child: ListView.separated(
          itemCount: artefacts.length + 1,
          itemBuilder: (_, i) =>
              i == 0 ? listHeader : listItemBuilder(artefacts[i - 1]),
          separatorBuilder: (_, __) => Container(
            height: 1,
            width: double.infinity,
            color: Colors.grey,
          ),
        ),
      ),
    );
  }
}
