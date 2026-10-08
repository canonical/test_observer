// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/artefact.dart';
import '../../providers/current_user.dart';
import '../../routing.dart';
import '../notification.dart';

class ArtefactDeleteButton extends ConsumerStatefulWidget {
  const ArtefactDeleteButton({super.key, required this.artefactId});

  final int artefactId;

  @override
  ConsumerState<ArtefactDeleteButton> createState() =>
      _ArtefactDeleteButtonState();
}

class _ArtefactDeleteButtonState extends ConsumerState<ArtefactDeleteButton> {
  bool _deleting = false;

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    if (user?.canDeleteArtefact != true) return const SizedBox.shrink();

    final colorScheme = Theme.of(context).colorScheme;
    return FilledButton(
      style: FilledButton.styleFrom(
        backgroundColor: colorScheme.error,
        foregroundColor: colorScheme.onError,
      ),
      onPressed: _deleting ? null : _confirmAndDelete,
      child: _deleting
          ? const SizedBox.square(
              dimension: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : const Text('Delete'),
    );
  }

  Future<void> _confirmAndDelete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete artefact?'),
        content: const Text(
          'This permanently deletes the artefact, its builds, test executions, and test results.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _deleting = true);
    try {
      await ref
          .read(artefactProvider(widget.artefactId).notifier)
          .deleteArtefact();
      if (!mounted) return;
      final uri = AppRoutes.uriFromContext(context);
      context.go('/${uri.pathSegments.first}');
    } catch (error) {
      if (!mounted) return;
      showNotification(context, 'Could not delete artefact: $error');
    } finally {
      if (mounted) setState(() => _deleting = false);
    }
  }
}
