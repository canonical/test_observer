import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'dio.g.dart';

@riverpod
Dio dio(DioRef ref) {
  final dio = Dio(BaseOptions(baseUrl: 'http://localhost:3000'));
  return dio;
}
