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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../../models/user_notification.dart';
import '../../providers/api.dart';
import '../../providers/notifications.dart';
import '../spacing.dart';

class NotificationsPage extends ConsumerWidget {
  const NotificationsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notificationsAsync = ref.watch(notificationsProvider);

    return Padding(
      padding: const EdgeInsets.all(Spacing.level5),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Notifications',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: Spacing.level4),
          Expanded(
            child: notificationsAsync.when(
              data: (notifications) {
                if (notifications.notifications.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          YaruIcons.notification,
                          size: 64,
                          color: Theme.of(context).colorScheme.outline,
                        ),
                        const SizedBox(height: Spacing.level3),
                        Text(
                          'No notifications',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ],
                    ),
                  );
                }

                return ListView.separated(
                  itemCount: notifications.notifications.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(height: Spacing.level3),
                  itemBuilder: (context, index) {
                    final notification = notifications.notifications[index];
                    return _NotificationCard(notification: notification);
                  },
                );
              },
              loading: () => const Center(child: YaruCircularProgressIndicator()),
              error: (error, stack) => Center(
                child: Text('Error loading notifications: $error'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NotificationCard extends ConsumerWidget {
  final UserNotification notification;

  const _NotificationCard({required this.notification});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isRead = notification.dismissedAt != null;

    return Card(
      color: isRead
          ? Theme.of(context).colorScheme.surfaceContainerLow
          : Theme.of(context).colorScheme.tertiaryContainer.withValues(alpha: 0.3),
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      if (!isRead)
                        Container(
                          width: 8,
                          height: 8,
                          margin: const EdgeInsets.only(right: Spacing.level2),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primary,
                            shape: BoxShape.circle,
                          ),
                        ),
                      Expanded(
                        child: InkWell(
                          onTap: notification.targetUrl != null
                              ? () => context.go(notification.targetUrl!)
                              : null,
                          child: Text(
                            notification.notificationType.displayTitle,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: isRead ? FontWeight.normal : FontWeight.bold,
                                  decoration: notification.targetUrl != null
                                      ? TextDecoration.underline
                                      : null,
                                ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: Spacing.level2),
                  Text(
                    _formatDate(notification.createdAt),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            const SizedBox(width: Spacing.level3),
            if (!isRead)
              ElevatedButton.icon(
                icon: const Icon(YaruIcons.ok, size: 20),
                label: const Text('Dismiss'),
                onPressed: () async {
                  await ref.read(apiProvider).markNotificationAsRead(notification.id);
                  ref.invalidate(notificationsProvider);
                  ref.invalidate(unreadNotificationCountProvider);
                },
              ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays > 0) {
      return '${difference.inDays} day${difference.inDays == 1 ? '' : 's'} ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} hour${difference.inHours == 1 ? '' : 's'} ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} minute${difference.inMinutes == 1 ? '' : 's'} ago';
    } else {
      return 'Just now';
    }
  }
}
