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

import '../../providers/artefact.dart';
import '../../providers/current_user.dart';
import '../notification.dart';

class ArtefactArchiveButton extends ConsumerStatefulWidget {
  const ArtefactArchiveButton({
    super.key,
    required this.artefactId,
    required this.archived,
  });

  final int artefactId;
  final bool archived;

  @override
  ConsumerState<ArtefactArchiveButton> createState() =>
      _ArtefactArchiveButtonState();
}

class _ArtefactArchiveButtonState extends ConsumerState<ArtefactArchiveButton> {
  bool _updating = false;

  @override
  Widget build(BuildContext context) {
    final user = ref.watch(currentUserProvider).valueOrNull;
    if (user?.canChangeArtefact != true) return const SizedBox.shrink();

    return TextButton(
      onPressed: _updating ? null : _toggleArchived,
      child: _updating
          ? const SizedBox.square(
              dimension: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Text(widget.archived ? 'Unarchive' : 'Archive'),
    );
  }

  Future<void> _toggleArchived() async {
    setState(() => _updating = true);
    try {
      await ref
          .read(artefactProvider(widget.artefactId).notifier)
          .setArchived(!widget.archived);
    } catch (error) {
      if (!mounted) return;
      final action = widget.archived ? 'unarchive' : 'archive';
      showNotification(context, 'Could not $action artefact: $error');
    } finally {
      if (mounted) setState(() => _updating = false);
    }
  }
}
