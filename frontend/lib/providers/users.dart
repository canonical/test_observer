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
import '../models/user.dart';
import 'api.dart';

part 'users.g.dart';

// Simple cache for User objects
// This allows us to display users without repeated fetching
@Riverpod(keepAlive: true)
class SimpleUser extends _$SimpleUser {
  @override
  User? build(int id) {
    // Return null initially - will be populated from search or fetched
    return null;
  }

  void setUser(User user) {
    state = user;
  }

  User? getUser() {
    return state;
  }

  Future<User> fetchIfNeeded() async {
    if (state != null) return state!;

    // Fetch from API if not in cache
    final api = ref.read(apiProvider);
    final user = await api.getUser(id);
    state = user;
    return user;
  }
}

@Riverpod(keepAlive: true)
class Users extends _$Users {
  @override
  Future<List<User>> build({
    int? limit,
    int? offset,
    String? q,
  }) async {
    final api = ref.watch(apiProvider);
    final users = await api.getUsers(
      limit: limit,
      offset: offset,
      q: q,
    );

    // Populate the simple user cache with these results
    for (final user in users) {
      ref.read(simpleUserProvider(user.id).notifier).setUser(user);
    }

    return users;
  }
}
