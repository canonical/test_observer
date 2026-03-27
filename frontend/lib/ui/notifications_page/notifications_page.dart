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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.all(Spacing.level5),
          child: Text(
            'Notifications',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
        ),
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
                        color: YaruColors.warmGrey,
                      ),
                      const SizedBox(height: Spacing.level3),
                      Text(
                        'No notifications',
                        style: Theme.of(context).textTheme.titleMedium?.apply(
                              color: YaruColors.warmGrey,
                            ),
                      ),
                    ],
                  ),
                );
              }

              return ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: Spacing.level5),
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
    );
  }
}

class _NotificationCard extends ConsumerStatefulWidget {
  final UserNotification notification;

  const _NotificationCard({required this.notification});

  @override
  ConsumerState<_NotificationCard> createState() => _NotificationCardState();
}

class _NotificationCardState extends ConsumerState<_NotificationCard> {
  bool _isDismissing = false;

  Future<void> _dismissNotification() async {
    setState(() => _isDismissing = true);

    try {
      await ref
          .read(apiProvider)
          .markNotificationAsRead(widget.notification.id);
      ref.invalidate(notificationsProvider);
      ref.invalidate(unreadNotificationCountProvider);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to dismiss notification: $error'),
            backgroundColor: Theme.of(context).colorScheme.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isDismissing = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isRead = widget.notification.dismissedAt != null;

    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: widget.notification.targetUrl != null
          ? () {
              try {
                context.go(widget.notification.targetUrl!);
              } catch (error) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(
                      'Invalid notification link: ${widget.notification.targetUrl}',
                    ),
                    backgroundColor: Theme.of(context).colorScheme.error,
                  ),
                );
              }
            }
          : null,
      child: Card(
        elevation: isRead ? 1 : 2,
        child: Padding(
          padding: const EdgeInsets.symmetric(
            vertical: Spacing.level3,
            horizontal: Spacing.level4,
          ),
          child: Row(
            children: [
              if (!isRead)
                Container(
                  width: 6,
                  height: 48,
                  margin: const EdgeInsets.only(right: Spacing.level4),
                  decoration: BoxDecoration(
                    color: YaruColors.orange,
                    borderRadius: BorderRadius.circular(3),
                  ),
                ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      widget.notification.notificationType.displayTitle,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight:
                                isRead ? FontWeight.normal : FontWeight.w500,
                          ),
                    ),
                    const SizedBox(height: Spacing.level1),
                    Text(
                      _formatDate(widget.notification.createdAt),
                      style: Theme.of(context).textTheme.bodySmall?.apply(
                            color: YaruColors.warmGrey,
                          ),
                    ),
                  ],
                ),
              ),
              if (!isRead) ...[
                const SizedBox(width: Spacing.level3),
                TextButton.icon(
                  icon: _isDismissing
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: YaruCircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(YaruIcons.ok, size: 16),
                  label: const Text('Dismiss'),
                  onPressed: _isDismissing ? null : _dismissNotification,
                ),
              ],
            ],
          ),
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
