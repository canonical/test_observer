// Copyright (C) 2023-2025 Canonical Ltd.
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
