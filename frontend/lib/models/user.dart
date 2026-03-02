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

import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'user.freezed.dart';
part 'user.g.dart';

@freezed
abstract class User with _$User {
  const User._();

  const factory User({
    required int id,
    required String name,
    required String email,
    @Default(null) @JsonKey(name: 'launchpad_handle') String? launchpadHandle,
    @Default(false) bool isEmpty,
  }) = _User;

  factory User.fromJson(Map<String, Object?> json) => _$UserFromJson(json);

  String get initials {
    if (isEmpty) return 'N/A';

    final names = name.split(' ');
    final numOfNames = names.length;
    switch (numOfNames) {
      case 0:
        throw Exception('User is missing a name');
      case 1:
        return names[0][0].capitalize();
      default:
        return names[0][0].capitalize() + names[numOfNames - 1][0].capitalize();
    }
  }
}

const emptyUser = User(
  id: -1,
  name: 'N/A',
  email: '',
  launchpadHandle: '',
  isEmpty: true,
);
