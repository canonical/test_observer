import 'package:flutter/widgets.dart';
import 'package:go_router/go_router.dart';

import '../../../models/family_name.dart';
import '../../../routing.dart';
import 'artefacts_columns_view.dart';
import 'artefacts_list_view/artefacts_list_view.dart';

enum ViewMode { dashboard, list }

class ViewModeManager {
  ViewModeManager(this.context) : uri = AppRoutes.uriFromContext(context);

  static const ViewMode defaultView = ViewMode.dashboard;
  final BuildContext context;
  final Uri uri;

  Widget buildAppropriateView() {
    final family = AppRoutes.familyFromUri(uri);
    final viewMode = currentViewMode();

    return switch ((family, viewMode)) {
      (_, ViewMode.dashboard) => const ArtefactsColumnsView(),
      (FamilyName.snap, ViewMode.list) => const ArtefactsListView.snaps(),
      (FamilyName.deb, ViewMode.list) => const ArtefactsListView.debs(),
    };
  }

  void switchView(ViewMode viewMode) {
    context.go(
      uri.replace(
        queryParameters: {...uri.queryParameters, 'view': viewMode.name},
      ).toString(),
    );
  }

  ViewMode currentViewMode() {
    final viewQuery = uri.queryParameters['view'];

    var viewMode = ViewMode.dashboard;
    if (viewQuery != null) {
      try {
        viewMode = ViewMode.values.byName(viewQuery);
      } on ArgumentError {
        // go with the default
      }
    }

    return viewMode;
  }
}
