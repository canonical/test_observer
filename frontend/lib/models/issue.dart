// Copyright (C) 2023 Canonical Ltd.
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

import 'attachment_rule.dart';

part 'issue.freezed.dart';
part 'issue.g.dart';

@freezed
abstract class Issue with _$Issue {
  const Issue._();
  const factory Issue({
    required int id,
    required IssueSource source,
    required String project,
    required String key,
    required String title,
    required IssueStatus status,
    required String url,
  }) = _Issue;

  factory Issue.fromJson(Map<String, Object?> json) => _$IssueFromJson(json);
}

@freezed
abstract class IssueWithContext with _$IssueWithContext {
  const IssueWithContext._();
  const factory IssueWithContext({
    required int id,
    required IssueSource source,
    required String project,
    required String key,
    required String title,
    required IssueStatus status,
    required String url,
    @JsonKey(name: 'attachment_rules')
    required List<AttachmentRule> attachmentRules,
  }) = _IssueWithContext;

  factory IssueWithContext.fromJson(Map<String, Object?> json) =>
      _$IssueWithContextFromJson(json);

  Issue toIssue() {
    return Issue(
      id: id,
      source: source,
      project: project,
      key: key,
      title: title,
      status: status,
      url: url,
    );
  }
}

enum IssueSource {
  github,
  jira,
  launchpad;
}

enum IssueStatus {
  unknown,
  closed,
  open;
}
