import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../models/artefact.dart';
import '../../../../providers/filtered_family_artefacts.dart';
import '../../../../routing.dart';

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

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final artefacts =
        ref.watch(filteredFamilyArtefactsProvider(pageUri)).values.toList();

    return Center(
      child: SizedBox(
        width: 1200,
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
