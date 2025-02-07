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
    final buttonStyle = ButtonStyle(
      foregroundColor: const WidgetStatePropertyAll(VanillaColors.textDefault),
      overlayColor: const WidgetStatePropertyAll(Colors.transparent),
      backgroundColor: WidgetStateProperty.resolveWith<Color?>(
        (Set<WidgetState> states) {
          if (states.contains(WidgetState.selected)) {
            return VanillaColors.backgroundActive;
          }
          if (states.contains(WidgetState.hovered)) {
            return VanillaColors.backgroundHover;
          }
          return VanillaColors.backgroundDefault;
        },
      ),
      shape: const WidgetStatePropertyAll(RoundedRectangleBorder()),
      side: const WidgetStatePropertyAll(
        BorderSide(
          color: VanillaColors.borderHighContrast,
          width: 1,
        ),
      ),
    );

    return MaterialApp.router(
      theme: ThemeData(
        scaffoldBackgroundColor: VanillaColors.backgroundNeutralDefault,
        segmentedButtonTheme: SegmentedButtonThemeData(
          selectedIcon: const SizedBox.shrink(),
          style: buttonStyle,
        ),
        checkboxTheme: CheckboxThemeData(
          splashRadius: 0,
          fillColor: WidgetStateProperty.resolveWith<Color?>(
            (Set<WidgetState> states) {
              if (states.contains(WidgetState.selected)) {
                return VanillaColors.backgroundCheckboxChecked;
              }
              if (states.contains(WidgetState.hovered)) {
                return VanillaColors.backgroundHover;
              }
              return VanillaColors.backgroundDefault;
            },
          ),
          shape: const RoundedRectangleBorder(),
          side: const BorderSide(
            color: VanillaColors.borderHighContrast,
            width: 1,
          ),
        ),
      ),
      routerConfig: appRouter,
    );
  }
}
