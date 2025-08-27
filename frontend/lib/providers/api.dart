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

// ignore_for_file: avoid_web_libraries_in_flutter

import 'dart:js_interop';
import 'dart:js_interop_unsafe';

import 'package:web/web.dart' as web;

import 'package:dio/dio.dart';
import 'package:dio_smart_retry/dio_smart_retry.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../repositories/api_repository.dart';
import 'global_error_message.dart';

part 'api.g.dart';

final apiUrl = web.window.getProperty('testObserverAPIBaseURI'.toJS).toString();

@riverpod
ApiRepository api(Ref ref) {
  final dio = Dio(BaseOptions(baseUrl: apiUrl));
  // Send cookies with requests
  dio.options.extra['withCredentials'] = true;
  dio.interceptors.add(RetryInterceptor(dio: dio));
  dio.interceptors.add(
    InterceptorsWrapper(
      onError: (e, handler) {
        final errorDetails = e.response?.data?['detail'];
        if (errorDetails != null) {
          ref
              .read(globalErrorMessageProvider.notifier)
              .set(errorDetails.toString());
        } else {
          return handler.next(e);
        }
      },
    ),
  );
  return ApiRepository(dio: dio);
}
