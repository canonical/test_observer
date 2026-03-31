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

import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/user_notification.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/notifications.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../utilities.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {}

final _testNotifications = UserNotifications(
  notifications: [
    UserNotification(
      id: 1,
      userId: 1,
      notificationType: NotificationType.userAssignedArtefactReview,
      targetUrl: '/snaps/1',
      createdAt: DateTime(2025, 1, 1),
      dismissedAt: null,
    ),
    UserNotification(
      id: 2,
      userId: 1,
      notificationType: NotificationType.userAssignedEnvironmentReview,
      targetUrl: '/images/13',
      createdAt: DateTime(2025, 1, 2),
      dismissedAt: DateTime(2025, 1, 3),
    ),
  ],
);

void main() {
  test('notificationsProvider fetches notifications from API', () async {
    final mockApi = ApiRepositoryMock();
    when(() => mockApi.getNotifications())
        .thenAnswer((_) async => _testNotifications);

    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => mockApi)],
    );

    final notifications = await container.read(notificationsProvider.future);

    expect(notifications.notifications.length, 2);
    expect(notifications.notifications[0].id, 1);
    expect(
      notifications.notifications[0].notificationType,
      NotificationType.userAssignedArtefactReview,
    );
    expect(notifications.notifications[0].targetUrl, '/snaps/1');
    expect(notifications.notifications[0].dismissedAt, null);
    expect(notifications.notifications[1].id, 2);
    expect(
      notifications.notifications[1].notificationType,
      NotificationType.userAssignedEnvironmentReview,
    );
    expect(notifications.notifications[1].dismissedAt, isNotNull);
  });

  test('unreadNotificationCountProvider fetches count from API', () async {
    final mockApi = ApiRepositoryMock();
    when(() => mockApi.getUnreadNotificationCount()).thenAnswer((_) async => 1);

    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => mockApi)],
    );

    final count = await container.read(unreadNotificationCountProvider.future);

    expect(count, 1);
  });

  test('notificationsProvider caches result', () async {
    final mockApi = ApiRepositoryMock();
    when(() => mockApi.getNotifications())
        .thenAnswer((_) async => _testNotifications);

    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => mockApi)],
    );

    // First read
    await container.read(notificationsProvider.future);
    // Second read (should use cache)
    await container.read(notificationsProvider.future);

    // Should only call API once due to Riverpod caching
    verify(() => mockApi.getNotifications()).called(1);
  });

  test('unreadNotificationCountProvider caches result', () async {
    final mockApi = ApiRepositoryMock();
    when(() => mockApi.getUnreadNotificationCount()).thenAnswer((_) async => 1);

    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => mockApi)],
    );

    // First read
    await container.read(unreadNotificationCountProvider.future);
    // Second read (should use cache)
    await container.read(unreadNotificationCountProvider.future);

    // Should only call API once due to Riverpod caching
    verify(() => mockApi.getUnreadNotificationCount()).called(1);
  });

  test('invalidating notificationsProvider triggers refetch', () async {
    final mockApi = ApiRepositoryMock();
    when(() => mockApi.getNotifications())
        .thenAnswer((_) async => _testNotifications);

    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => mockApi)],
    );

    // First read
    await container.read(notificationsProvider.future);

    // Invalidate
    container.invalidate(notificationsProvider);

    // Second read (should refetch)
    await container.read(notificationsProvider.future);

    // Should call API twice (initial + after invalidation)
    verify(() => mockApi.getNotifications()).called(2);
  });

  test('invalidating unreadNotificationCountProvider triggers refetch',
      () async {
    final mockApi = ApiRepositoryMock();
    when(() => mockApi.getUnreadNotificationCount()).thenAnswer((_) async => 1);

    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => mockApi)],
    );

    // First read
    await container.read(unreadNotificationCountProvider.future);

    // Invalidate
    container.invalidate(unreadNotificationCountProvider);

    // Second read (should refetch)
    await container.read(unreadNotificationCountProvider.future);

    // Should call API twice (initial + after invalidation)
    verify(() => mockApi.getUnreadNotificationCount()).called(2);
  });
}
