// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:freezed_annotation/freezed_annotation.dart';

part 'family.freezed.dart';
part 'family.g.dart';

@freezed
abstract class Family with _$Family {
  const factory Family({
    required String name,
  }) = _Family;

  factory Family.fromJson(Map<String, Object?> json) => _$FamilyFromJson(json);
}
