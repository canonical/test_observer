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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../../models/family_name.dart';
import '../../models/rerun_details.dart';
import '../../providers/api.dart';
import '../../providers/rerun_details.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'rerun_priority_chart.dart';

class RerunsPage extends ConsumerWidget {
  const RerunsPage({super.key});

  // Default product shown before the user picks one.
  static const _defaultFamily = FamilyName.charm;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uri = AppRoutes.uriFromContext(context);
    final family = _familyFromUri(uri);
    final priority = _intParam(uri, 'priority');
    final page = _intParam(uri, 'page') ?? 1;

    final detailsAsync = ref.watch(
      rerunDetailsProvider(family: family, priority: priority, page: page),
    );

    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.only(
          left: Spacing.pageHorizontalPadding,
          right: Spacing.pageHorizontalPadding,
          top: Spacing.level5,
          bottom: Spacing.level5,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: Spacing.level4,
          children: [
            Row(
              children: [
                Text(
                  'Reruns',
                  style: Theme.of(context).textTheme.headlineLarge,
                ),
                const SizedBox(width: Spacing.level5),
                _FamilyDropdown(
                  family: family,
                  onChanged: (newFamily) => _goWith(
                    context,
                    uri,
                    family: newFamily,
                    priority: null,
                    page: 1,
                  ),
                ),
              ],
            ),
            detailsAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(Spacing.level6),
                child: Center(child: YaruCircularProgressIndicator()),
              ),
              error: (error, _) => _ErrorView(error: error),
              data: (data) => _RerunsContent(
                data: data,
                onSelectPriority: (p) => _goWith(
                  context,
                  uri,
                  family: family,
                  priority: p,
                  page: 1,
                ),
                onPageChanged: (p) => _goWith(
                  context,
                  uri,
                  family: family,
                  priority: data.selectedPriority,
                  page: p,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  static FamilyName _familyFromUri(Uri uri) {
    final raw = uri.queryParameters['family'];
    return FamilyName.values.firstWhere(
      (f) => f.name == raw,
      orElse: () => _defaultFamily,
    );
  }

  static int? _intParam(Uri uri, String key) {
    final raw = uri.queryParameters[key];
    return raw == null ? null : int.tryParse(raw);
  }

  void _goWith(
    BuildContext context,
    Uri uri, {
    required FamilyName family,
    required int? priority,
    required int page,
  }) {
    final params = <String, String>{
      'family': family.name,
      if (priority != null) 'priority': priority.toString(),
      if (page > 1) 'page': page.toString(),
    };
    context.go(uri.replace(queryParameters: params).toString());
  }
}

class _FamilyDropdown extends StatelessWidget {
  const _FamilyDropdown({required this.family, required this.onChanged});

  final FamilyName family;
  final void Function(FamilyName family) onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButton<FamilyName>(
      value: family,
      onChanged: (value) {
        if (value != null) onChanged(value);
      },
      items: [
        for (final f in FamilyName.values)
          DropdownMenuItem(value: f, child: Text(_familyLabel(f))),
      ],
    );
  }

  static String _familyLabel(FamilyName family) {
    final name = family.name;
    return name.isEmpty ? name : name[0].toUpperCase() + name.substring(1);
  }
}

class _RerunsContent extends StatelessWidget {
  const _RerunsContent({
    required this.data,
    required this.onSelectPriority,
    required this.onPageChanged,
  });

  final RerunDetailsResponse data;
  final void Function(int priority) onSelectPriority;
  final void Function(int page) onPageChanged;

  @override
  Widget build(BuildContext context) {
    if (data.prioritySummaries.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(Spacing.level6),
        child: Center(child: Text('No reruns found for this product.')),
      );
    }

    final selected = data.selectedPriority;
    final totalPages = data.selectedCount == 0
        ? 1
        : ((data.selectedCount + data.limit - 1) ~/ data.limit);
    final rawPage = (data.offset ~/ data.limit) + 1;
    final currentPage = rawPage.clamp(1, totalPages);

    if (rawPage != currentPage) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        onPageChanged(currentPage);
      });
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${data.count} pending rerun(s)',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level4),
        RerunPriorityChart(
          summaries: data.prioritySummaries,
          selectedPriority: selected,
          onBarTap: onSelectPriority,
        ),
        const SizedBox(height: Spacing.level5),
        if (selected != null) ...[
          Text(
            'Priority $selected — ${data.selectedCount} rerun(s)',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: Spacing.level3),
          if (data.reruns.isEmpty)
            const Padding(
              padding: EdgeInsets.all(Spacing.level5),
              child: Text('No reruns for the selected priority.'),
            )
          else
            _RerunsTable(reruns: data.reruns),
          const SizedBox(height: Spacing.level4),
          _PaginationControls(
            currentPage: currentPage,
            totalPages: totalPages,
            onPageChanged: onPageChanged,
          ),
        ],
      ],
    );
  }
}

class _RerunsTable extends ConsumerWidget {
  const _RerunsTable({required this.reruns});

  final List<RerunDetail> reruns;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      // The app wraps pages in a SelectionArea; disable selection here so row
      // taps aren't swallowed by text selection.
      child: SelectionContainer.disabled(
        child: DataTable(
          showCheckboxColumn: false,
          columns: const [
            DataColumn(label: Text('Test plan')),
            DataColumn(label: Text('Created at')),
            DataColumn(label: Text('Priority')),
            DataColumn(label: Text('Architecture')),
            DataColumn(label: Text('Environment')),
          ],
          rows: [
            for (final r in reruns)
              DataRow(
                onSelectChanged: (selected) {
                  if (selected == true) {
                    _openLatestExecution(context, ref, r.testPlanName);
                  }
                },
                cells: [
                  DataCell(Text(r.testPlanName)),
                  DataCell(Text(_formatDate(r.createdAt))),
                  DataCell(Text('${r.priority}')),
                  DataCell(Text(r.architecture)),
                  DataCell(Text(r.environmentName)),
                ],
              ),
          ],
        ),
      ),
    );
  }

  // Query only runs on click: find the latest execution for the row's test plan.
  Future<void> _openLatestExecution(
    BuildContext context,
    WidgetRef ref,
    String testPlanName,
  ) async {
    final router = GoRouter.of(context);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final result = await ref
          .read(apiProvider)
          .getLatestTestExecutionForTestPlan(testPlanName);
      if (!context.mounted) return;
      if (result == null) {
        messenger.showSnackBar(
          const SnackBar(
            content: Text('No test execution found for this test plan.'),
          ),
        );
        return;
      }
      router.go(
        getArtefactPagePathForFamily(
          result.family,
          result.artefactId,
          testExecutionId: result.testExecutionId,
        ),
      );
    } catch (e) {
      debugPrint('Failed to open test execution: $e');
      if (!context.mounted) return;
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Could not open the test execution. Please try again.'),
        ),
      );
    }
  }

  static String _formatDate(DateTime dt) {
    final local = dt.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${local.year}-${two(local.month)}-${two(local.day)} '
        '${two(local.hour)}:${two(local.minute)}';
  }
}

class _PaginationControls extends StatelessWidget {
  const _PaginationControls({
    required this.currentPage,
    required this.totalPages,
    required this.onPageChanged,
  });

  final int currentPage;
  final int totalPages;
  final void Function(int page) onPageChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          icon: const Icon(Icons.chevron_left),
          onPressed:
              currentPage > 1 ? () => onPageChanged(currentPage - 1) : null,
        ),
        Text('Page $currentPage of $totalPages'),
        IconButton(
          icon: const Icon(Icons.chevron_right),
          onPressed: currentPage < totalPages
              ? () => onPageChanged(currentPage + 1)
              : null,
        ),
      ],
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error});

  final Object error;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(Spacing.level6),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.error_outline, size: 48, color: Colors.red),
            SizedBox(height: Spacing.level3),
            Text('Could not load reruns. Please try again later.'),
          ],
        ),
      ),
    );
  }
}
