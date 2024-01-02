// ignore_for_file: avoid_web_libraries_in_flutter

import 'dart:html';
import 'dart:js_util' as js_util;

import 'package:dio/dio.dart';
import 'package:dio_smart_retry/dio_smart_retry.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'dio.g.dart';

@riverpod
Dio dio(DioRef ref) {
  final baseUrl = js_util.getProperty<String>(window, 'testObserverAPIBaseURI');
  final dio = Dio(BaseOptions(baseUrl: baseUrl));
  dio.interceptors.add(RetryInterceptor(dio: dio));
  return dio;
}
