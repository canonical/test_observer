// ignore_for_file: avoid_web_libraries_in_flutter

import 'dart:html';
import 'dart:js_util' as js_util;

import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'dio.g.dart';

@riverpod
Dio dio(DioRef ref) {
  final baseUrl = js_util.getProperty(window, 'testObserverAPIBaseURI');
  final dio = Dio(BaseOptions(baseUrl: baseUrl ?? 'http://localhost:30000'));
  return dio;
}
