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

// ignore_for_file: avoid_web_libraries_in_flutter

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../utils/dio.dart';
import '../repositories/api_repository.dart';
import 'global_error_message.dart';

part 'api.g.dart';

@riverpod
ApiRepository api(Ref ref) {
  final dio = createConfiguredDio(
    onErrorDetails: (details) {
      ref.read(globalErrorMessageProvider.notifier).set(details);
    },
  );
  return ApiRepository(dio: dio);
}
