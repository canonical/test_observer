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

import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/view_modes.dart';

part 'view_mode.g.dart';

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
