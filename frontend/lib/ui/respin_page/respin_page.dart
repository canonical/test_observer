// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher_string.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../models/user.dart';
import '../../providers/api.dart';
import '../../providers/current_user.dart';
import '../../providers/image_respin.dart';
import '../../utils/dio.dart';
import '../expandable.dart';
import '../spacing.dart';

/// Requests a respin of every image of a release by queuing rerun requests
/// on their cdimage build executions, which cdimage polls for.
///
/// Only reachable by link (e.g. from Ubuntu Mission Control): it has no
/// navbar entry, and it never submits anything without an explicit click.
class RespinPage extends ConsumerStatefulWidget {
  const RespinPage({super.key, required this.release});

  final String release;

  @override
  ConsumerState<RespinPage> createState() => _RespinPageState();
}

class _RespinPageState extends ConsumerState<RespinPage> {
  bool _submitting = false;
  ImageRespinOutcome? _outcome;

  String get _releaseTitle => widget.release.capitalize();

  @override
  Widget build(BuildContext context) {
    final targetsAsync = ref.watch(imageRespinTargetsProvider(widget.release));
    final user = ref.watch(currentUserProvider).valueOrNull;
    final textTheme = Theme.of(context).textTheme;

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.symmetric(
          horizontal: Spacing.pageHorizontalPadding,
          vertical: Spacing.level5,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: Spacing.level4,
          children: [
            Text(
              'Respin images — $_releaseTitle',
              style: textTheme.headlineLarge,
            ),
            const Text(
              'Queues a rebuild of the latest daily build of each image below. '
              'cdimage checks for requests every 5 minutes; '
              'some builds take hours.',
            ),
            if (widget.release.isEmpty)
              const Text('No release specified.')
            else
              targetsAsync.when(
                loading: () => const Center(
                  child: YaruCircularProgressIndicator(),
                ),
                error: (_, __) => const Text(
                  'Could not load images. Please try again later.',
                ),
                data: (data) => _buildContent(context, data, user),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    ImageRespinTargets data,
    User? user,
  ) {
    final targets = data.targets;
    if (targets.isEmpty && data.skipped.isEmpty) {
      return Text('No images found for $_releaseTitle.');
    }

    final queuedCount = targets.count((target) => target.isRerunRequested);
    final outcome = _outcome;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: Spacing.level4,
      children: [
        Text(
          '${_images(targets.length)} · $queuedCount '
          '${outcome == null ? 'already queued' : 'queued'} · '
          '${data.skipped.length} skipped',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        if (user == null) const _SignInCard(),
        Expandable(
          title: Text('Show images (${targets.length})'),
          tilePadding: EdgeInsets.zero,
          childrenPadding: EdgeInsets.zero,
          children: [
            // ExpansionTile centres its children; keep the list aligned left.
            Align(
              alignment: Alignment.centerLeft,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _TargetsTable(targets: targets, statusOf: _statusOf),
                  if (data.skipped.isNotEmpty)
                    _SkippedList(skipped: data.skipped),
                ],
              ),
            ),
          ],
        ),
        if (outcome != null)
          _OutcomeBanner(
            outcome: outcome,
            onRetry: user == null || _submitting
                ? null
                : () => _confirmAndSubmit(targets),
          )
        else
          Row(
            children: [
              if (user != null) Text('Signed in as ${user.name}'),
              const Spacer(),
              ElevatedButton(
                onPressed: user == null || _submitting || targets.isEmpty
                    ? null
                    : () => _confirmAndSubmit(targets),
                style: ElevatedButton.styleFrom(
                  backgroundColor: YaruColors.orange,
                  foregroundColor: Colors.white,
                ),
                child: Text(
                  _submitting
                      ? 'Requesting…'
                      : 'Request respin of ${_images(targets.length)}',
                ),
              ),
            ],
          ),
      ],
    );
  }

  String _statusOf(ImageRespinTarget target) {
    final outcome = _outcome;
    if (outcome is ImageRespinQueued &&
        outcome.notFoundBuildIds.contains(target.artefactBuildId)) {
      return 'Not found';
    }
    if (target.isRerunRequested) {
      return outcome == null ? 'Already queued' : 'Queued';
    }
    return '—';
  }

  Future<void> _confirmAndSubmit(List<ImageRespinTarget> targets) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm respin'),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Text(
            'Request respins of ${_images(targets.length, _releaseTitle)}?\n\n'
            'cdimage will rebuild each image (it checks every 5 minutes; some '
            'builds take hours). New builds appear as new versions; results '
            'on the current builds are kept.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('respin'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _submitting = true);
    final outcome = await requestImageRespins(
      api: ref.read(apiProvider),
      targets: targets,
      reloadCurrentUser: () {
        ref.invalidate(currentUserProvider);
        return ref.read(currentUserProvider.future);
      },
    );
    if (!mounted) return;

    setState(() {
      _submitting = false;
      _outcome = outcome;
    });
    // Show what Test Observer has queued rather than what we asked for.
    ref.invalidate(imageRespinTargetsProvider(widget.release));
  }
}

String _images(int count, [String kind = '']) =>
    '$count ${kind.isEmpty ? '' : '$kind '}${count == 1 ? 'image' : 'images'}';

class _SignInCard extends StatelessWidget {
  const _SignInCard();

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Row(
          spacing: Spacing.level4,
          children: [
            const Icon(YaruIcons.information),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sign in to request respins',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const Text(
                    'Needs a Test Observer account with respin rights '
                    '(admins, or teams with rerun permissions).',
                  ),
                ],
              ),
            ),
            FilledButton(
              onPressed: () {
                // Same flow as the navbar's "Log in", returning to this page.
                final loginUri = Uri.parse(apiUrl).replace(
                  path: '/v1/auth/saml/login',
                  queryParameters: {'return_to': Uri.base.toString()},
                );
                launchUrlString(
                  loginUri.toString(),
                  webOnlyWindowName: '_self',
                );
              },
              child: const Text('Log in'),
            ),
          ],
        ),
      ),
    );
  }
}

class _TargetsTable extends StatelessWidget {
  const _TargetsTable({required this.targets, required this.statusOf});

  final List<ImageRespinTarget> targets;
  final String Function(ImageRespinTarget target) statusOf;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: const [
          DataColumn(label: Text('Image')),
          DataColumn(label: Text('Flavour')),
          DataColumn(label: Text('Version')),
          DataColumn(label: Text('Arch')),
          DataColumn(label: Text('Status')),
        ],
        rows: [
          for (final target in targets)
            DataRow(
              cells: [
                DataCell(Text(target.artefact.name)),
                DataCell(Text(target.artefact.os)),
                DataCell(Text(target.artefact.version)),
                DataCell(Text(target.architecture)),
                DataCell(Text(statusOf(target))),
              ],
            ),
        ],
      ),
    );
  }
}

class _SkippedList extends StatelessWidget {
  const _SkippedList({required this.skipped});

  final List<Artefact> skipped;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: Spacing.level4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: Spacing.level2,
        children: [
          Text(
            'Cannot be respun (${skipped.length})',
            style: Theme.of(context).textTheme.titleSmall,
          ),
          for (final artefact in skipped)
            Text(
              '${artefact.name} (${artefact.os}): '
              'no cdimage image build found',
            ),
        ],
      ),
    );
  }
}

class _OutcomeBanner extends StatelessWidget {
  const _OutcomeBanner({required this.outcome, required this.onRetry});

  final ImageRespinOutcome outcome;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final (icon, color, message) = switch (outcome) {
      ImageRespinQueued(:final queuedBuildIds, :final notFoundBuildIds)
          when notFoundBuildIds.isEmpty =>
        (
          YaruIcons.ok,
          YaruColors.light.success,
          'Respin requested for ${_images(queuedBuildIds.length)}. '
              'You can close this tab.',
        ),
      ImageRespinQueued(:final queuedBuildIds, :final notFoundBuildIds) => (
          YaruIcons.error,
          YaruColors.orange,
          '${queuedBuildIds.length} queued · ${notFoundBuildIds.length} not '
              'found, nothing was queued for them (marked below).',
        ),
      ImageRespinNotSignedIn() => (
          YaruIcons.error,
          YaruColors.red,
          'You are not signed in. Nothing was queued.',
        ),
      ImageRespinForbidden(:final userName) => (
          YaruIcons.error,
          YaruColors.red,
          "Signed in as $userName, but this account can't request respins. "
              'Nothing was queued.',
        ),
      ImageRespinFailed(:final detail) => (
          YaruIcons.error,
          YaruColors.red,
          'Request failed: $detail',
        ),
    };

    return Row(
      spacing: Spacing.level3,
      children: [
        Icon(icon, color: color),
        Expanded(child: Text(message)),
        if (outcome is ImageRespinFailed)
          TextButton(onPressed: onRetry, child: const Text('Retry')),
      ],
    );
  }
}
