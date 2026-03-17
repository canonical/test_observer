// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:freezed_annotation/freezed_annotation.dart';

import 'issue.dart';
import 'attachment_rule.dart';

part 'issue_attachment.freezed.dart';
part 'issue_attachment.g.dart';

@freezed
abstract class IssueAttachment with _$IssueAttachment {
  const factory IssueAttachment({
    required Issue issue,
    @JsonKey(name: 'attachment_rule') AttachmentRule? attachmentRule,
  }) = _IssueAttachment;

  factory IssueAttachment.fromJson(Map<String, Object?> json) =>
      _$IssueAttachmentFromJson(json);
}
