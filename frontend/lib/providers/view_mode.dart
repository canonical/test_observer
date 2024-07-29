import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';

part 'view_mode.g.dart';

enum ViewModes { dashboard, list }

@riverpod
class ViewMode extends _$ViewMode {
  @override
  Future<ViewModes> build() async {
    final prefs = await SharedPreferences.getInstance();

    var viewMode = ViewModes.dashboard;
    final storedViewMode = prefs.getString('viewMode');

    if (storedViewMode != null) {
      try {
        viewMode = ViewModes.values.byName(storedViewMode);
      } on ArgumentError {
        // go with the default
      }
    }

    return viewMode;
  }

  Future<void> set(ViewModes viewMode) async {
    final prefs = await SharedPreferences.getInstance();
    prefs.setString('viewMode', viewMode.name);
    ref.invalidateSelf();
    await future;
  }
}
