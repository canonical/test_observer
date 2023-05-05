import 'package:freezed_annotation/freezed_annotation.dart';

part 'family.freezed.dart';

@freezed
class Family with _$Family {
  const factory Family({
    required String name,
  }) = _Family;
}

const dummyFamily = Family(name: 'Family');
