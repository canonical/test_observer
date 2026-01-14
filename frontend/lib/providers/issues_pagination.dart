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

import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'issues_pagination.g.dart';

class IssuesPaginationState {
  final int limit;
  final int offset;

  const IssuesPaginationState({
    required this.limit,
    required this.offset,
  });

  IssuesPaginationState copyWith({
    int? limit,
    int? offset,
  }) {
    return IssuesPaginationState(
      limit: limit ?? this.limit,
      offset: offset ?? this.offset,
    );
  }
}

@riverpod
class IssuesPagination extends _$IssuesPagination {
  static const int defaultLimit = 50;
  static const int loadMoreIncrement = 50;

  @override
  IssuesPaginationState build(Uri pageUri) {
    return const IssuesPaginationState(
      limit: defaultLimit,
      offset: 0,
    );
  }

  void loadMore() {
    state = state.copyWith(
      offset: state.offset + loadMoreIncrement,
    );
  }

  void reset() {
    state = const IssuesPaginationState(
      limit: defaultLimit,
      offset: 0,
    );
  }
}
