import 'package:freezed_annotation/freezed_annotation.dart';

part 'stage.freezed.dart';

@freezed
class Stage with _$Stage {
  const factory Stage({
    required String name,
  }) = _Stage;
}

const dummyStage = Stage(name: 'Stage');
