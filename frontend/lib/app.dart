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

import 'routing.dart';
import 'ui/vanilla/vanilla_colors.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      theme: ThemeData(
        scaffoldBackgroundColor: VanillaColors.backgroundNeutralDefault,
        cardTheme: const CardTheme(
          margin: EdgeInsets.all(0),
          elevation: 0,
          color: VanillaColors.backgroundDefault,
          shape: RoundedRectangleBorder(
            side: BorderSide(color: VanillaColors.borderDefault, width: 1.5),
          ),
        ),
        segmentedButtonTheme: SegmentedButtonThemeData(
          selectedIcon: const SizedBox.shrink(),
          style: ButtonStyle(
            iconColor: const WidgetStatePropertyAll(VanillaColors.textDefault),
            backgroundColor: WidgetStateProperty.resolveWith<Color?>(
              (Set<WidgetState> states) {
                if (states.contains(WidgetState.selected)) {
                  return VanillaColors.backgroundActive;
                }
                return VanillaColors.backgroundDefault;
              },
            ),
            shape: const WidgetStatePropertyAll(
              RoundedRectangleBorder(
                side: BorderSide(
                  color: VanillaColors.borderHighContrast,
                  width: 1.5,
                ),
              ),
            ),
          ),
        ),
      ),
      routerConfig: appRouter,
    );
  }
}
