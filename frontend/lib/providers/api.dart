// ignore_for_file: avoid_web_libraries_in_flutter

import 'dart:html';
import 'dart:js_util' as js_util;

import 'package:dio/dio.dart';
import 'package:dio_smart_retry/dio_smart_retry.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../repositories/api_repository.dart';
import 'global_error_message.dart';

part 'api.g.dart';

@riverpod
ApiRepository api(ApiRef ref) {
  final baseUrl = js_util.getProperty<String>(window, 'testObserverAPIBaseURI');
  final dio = Dio(BaseOptions(baseUrl: baseUrl));
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
