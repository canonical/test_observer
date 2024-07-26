import 'package:freezed_annotation/freezed_annotation.dart';

part 'test_event.freezed.dart';
part 'test_event.g.dart';

@freezed
class TestEvent with _$TestEvent {
  const factory TestEvent({
    @JsonKey(name: 'event_name') required String eventName,
    required String timestamp,
    required String detail,
  }) = _TestEvent;

  factory TestEvent.fromJson(Map<String, Object?> json) =>
      _$TestEventFromJson(json);
}
