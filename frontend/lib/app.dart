// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import 'routing.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return YaruTheme(
      builder: (context, yaru, child) {
        final theme = yaru.theme?.copyWith(
          cardTheme: CardThemeData(color: Colors.white),
          datePickerTheme: const DatePickerThemeData(
            headerHeadlineStyle: TextStyle(fontSize: 20),
          ),
          timePickerTheme: const TimePickerThemeData(
            hourMinuteTextStyle: TextStyle(fontSize: 52),
          ),
        );

        return MaterialApp.router(
          theme: theme,
          routerConfig: appRouter,
        );
      },
    );
  }
}
