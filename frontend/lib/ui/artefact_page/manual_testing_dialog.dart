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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_typeahead/flutter_typeahead.dart';
import 'package:go_router/go_router.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../../models/family_name.dart';
import '../../models/test_execution.dart';
import '../../providers/api.dart';
import '../../providers/artefact.dart' hide Artefact;
import '../../providers/artefact_builds.dart';
import '../spacing.dart';

class StartManualTestingDialog extends ConsumerStatefulWidget {
  const StartManualTestingDialog({
    super.key,
    required this.artefactId,
  });

  final int artefactId;

  @override
  ConsumerState<StartManualTestingDialog> createState() =>
      _StartManualTestingDialogState();
}

class _StartManualTestingDialogState
    extends ConsumerState<StartManualTestingDialog> {
  final _formKey = GlobalKey<FormState>();
  final _environmentController = TextEditingController();
  final _relevantLinks = <_RelevantLink>[];
  TestExecutionStatus _selectedStatus = TestExecutionStatus.notStarted;
  bool _isSubmitting = false;

  static const String _manualTestPlan = 'Manual Testing';

  @override
  void dispose() {
    _environmentController.dispose();
    for (final link in _relevantLinks) {
      link.dispose();
    }
    super.dispose();
  }

  Future<void> _handleSubmit(
    Artefact artefact,
    List<ArtefactBuild> builds,
  ) async {
    if (!_formKey.currentState!.validate() || _isSubmitting) {
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final api = ref.read(apiProvider);

      // Build family-specific fields
      final familySpecificFields = _buildFamilySpecificFields(artefact);

      // Build relevant links
      final relevantLinks = _relevantLinks
          .where(
            (link) =>
                link.labelController.text.isNotEmpty &&
                link.urlController.text.isNotEmpty,
          )
          .map(
            (link) => {
              'label': link.labelController.text,
              'url': link.urlController.text,
            },
          )
          .toList();

      String statusString;
      switch (_selectedStatus) {
        case TestExecutionStatus.notStarted:
          statusString = 'NOT_STARTED';
          break;
        case TestExecutionStatus.inProgress:
          statusString = 'IN_PROGRESS';
          break;
        default:
          statusString = 'NOT_STARTED';
      }

      await api.startManualTestExecution(
        family: artefact.family,
        name: artefact.name,
        version: artefact.version,
        arch: builds.first.architecture,
        environment: _environmentController.text,
        testPlan: _manualTestPlan,
        initialStatus: statusString,
        familySpecificFields: familySpecificFields,
        relevantLinks: relevantLinks.isEmpty ? null : relevantLinks,
      );

      // Invalidate the artefact builds to refresh the page
      if (mounted) {
        ref.invalidate(artefactBuildsProvider(widget.artefactId));
        context.pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Manual test execution started successfully'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to start manual test: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Map<String, dynamic> _buildFamilySpecificFields(Artefact artefact) {
    final fields = <String, dynamic>{};

    final family = FamilyName.values.firstWhere(
      (f) => f.name == artefact.family,
      orElse: () => FamilyName.snap,
    );

    switch (family) {
      case FamilyName.snap:
        final artefactBuildsAsync =
            ref.read(artefactBuildsProvider(widget.artefactId));
        final revision = artefactBuildsAsync.value?.first.revision;
        fields['revision'] = revision ?? 0;
        fields['track'] = artefact.track;
        fields['store'] = artefact.store;
        if (artefact.branch.isNotEmpty) {
          fields['branch'] = artefact.branch;
        }
        fields['execution_stage'] = artefact.stage.name;
        break;

      case FamilyName.deb:
        fields['series'] = artefact.series;
        fields['repo'] = artefact.repo;
        if (artefact.source.isNotEmpty) {
          fields['source'] = artefact.source;
        }
        fields['execution_stage'] = artefact.stage.name;
        break;

      case FamilyName.charm:
        final artefactBuildsAsync =
            ref.read(artefactBuildsProvider(widget.artefactId));
        final revision = artefactBuildsAsync.value?.first.revision;
        fields['revision'] = revision ?? 0;
        fields['track'] = artefact.track;
        if (artefact.branch.isNotEmpty) {
          fields['branch'] = artefact.branch;
        }
        fields['execution_stage'] = artefact.stage.name;
        break;

      case FamilyName.image:
        fields['os'] = artefact.os;
        fields['release'] = artefact.release;
        fields['sha256'] = artefact.sha256;
        fields['owner'] = artefact.owner;
        fields['image_url'] = artefact.imageUrl;
        fields['execution_stage'] = artefact.stage.name;
        break;
    }

    return fields;
  }

  Future<List<String>> _searchEnvironments(String pattern) async {
    if (pattern.trim().length < 2) {
      return [];
    }

    try {
      final api = ref.read(apiProvider);
      final artefact = ref.read(artefactProvider(widget.artefactId)).value;
      if (artefact == null) return [];

      return await api.searchEnvironments(
        query: pattern.trim(),
        families: [artefact.family],
        limit: 20,
      );
    } catch (e) {
      return [];
    }
  }

  void _addRelevantLink() {
    setState(() {
      _relevantLinks.add(_RelevantLink());
    });
  }

  void _removeRelevantLink(int index) {
    setState(() {
      _relevantLinks[index].dispose();
      _relevantLinks.removeAt(index);
    });
  }

  @override
  Widget build(BuildContext context) {
    final artefactAsync = ref.watch(artefactProvider(widget.artefactId));
    final buildsAsync = ref.watch(artefactBuildsProvider(widget.artefactId));

    return artefactAsync.when(
      data: (artefact) => buildsAsync.when(
        data: (builds) => AlertDialog(
          scrollable: true,
          title: const Text('Add Manual Testing'),
          contentPadding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
          content: Form(
            key: _formKey,
            child: SizedBox(
              width: 600,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Artefact: ${artefact.name}',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                  const SizedBox(height: Spacing.level5),
                  // Environment autocomplete
                  TypeAheadField<String>(
                    controller: _environmentController,
                    builder: (context, controller, focusNode) {
                      return TextFormField(
                        controller: controller,
                        focusNode: focusNode,
                        decoration: const InputDecoration(
                          labelText: 'Environment *',
                          hintText: 'Type to search environments...',
                          border: OutlineInputBorder(),
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Environment is required';
                          }
                          return null;
                        },
                      );
                    },
                    suggestionsCallback: _searchEnvironments,
                    itemBuilder: (context, suggestion) {
                      return ListTile(
                        title: Text(suggestion),
                      );
                    },
                    onSelected: (suggestion) {
                      _environmentController.text = suggestion;
                    },
                    emptyBuilder: (context) => const Padding(
                      padding: EdgeInsets.all(8.0),
                      child: Text(
                        'No environments found. You can type a custom name.',
                      ),
                    ),
                  ),
                  const SizedBox(height: Spacing.level4),
                  // Test plan name (read-only)
                  TextFormField(
                    initialValue: _manualTestPlan,
                    decoration: const InputDecoration(
                      labelText: 'Test Plan',
                      border: OutlineInputBorder(),
                      filled: true,
                      fillColor: Color(0xFFEEEEEE),
                    ),
                    enabled: false,
                  ),
                  const SizedBox(height: Spacing.level4),
                  // Initial status dropdown
                  DropdownButtonFormField<TestExecutionStatus>(
                    value: _selectedStatus,
                    decoration: const InputDecoration(
                      labelText: 'Initial Status *',
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      TestExecutionStatus.notStarted,
                      TestExecutionStatus.inProgress,
                    ].map((status) {
                      return DropdownMenuItem(
                        value: status,
                        child: Text(_formatStatusName(status)),
                      );
                    }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        setState(() => _selectedStatus = value);
                      }
                    },
                  ),
                  const SizedBox(height: Spacing.level5),
                  // Relevant links section
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Relevant Links (Optional)',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      TextButton.icon(
                        onPressed: _addRelevantLink,
                        icon: const Icon(Icons.add),
                        label: const Text('Add Link'),
                      ),
                    ],
                  ),
                  if (_relevantLinks.isEmpty)
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text(
                        'No relevant links added',
                        style: TextStyle(
                          fontStyle: FontStyle.italic,
                          color: Colors.grey,
                        ),
                      ),
                    ),
                  const SizedBox(height: 12),
                  ..._relevantLinks.asMap().entries.map(
                    (entry) {
                      final index = entry.key;
                      final link = entry.value;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: _RelevantLinkRow(
                          link: link,
                          onRemove: () => _removeRelevantLink(index),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
          actionsPadding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
          actions: [
            TextButton(
              onPressed: _isSubmitting ? null : () => context.pop(),
              child: const Text('Cancel'),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed:
                  _isSubmitting ? null : () => _handleSubmit(artefact, builds),
              child: _isSubmitting
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Start Manual Testing'),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, __) => AlertDialog(
          title: const Text('Error'),
          content: Text('Failed to load artefact data: $e'),
          actions: [
            TextButton(
              onPressed: () => context.pop(),
              child: const Text('Close'),
            ),
          ],
        ),
      ),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, __) => AlertDialog(
        title: const Text('Error'),
        content: Text('Failed to load artefact: $e'),
        actions: [
          TextButton(
            onPressed: () => context.pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  String _formatStatusName(TestExecutionStatus status) {
    switch (status) {
      case TestExecutionStatus.notStarted:
        return 'Not Started';
      case TestExecutionStatus.inProgress:
        return 'In Progress';
      default:
        return status.name;
    }
  }
}

class _RelevantLink {
  final TextEditingController labelController;
  final TextEditingController urlController;

  _RelevantLink()
      : labelController = TextEditingController(),
        urlController = TextEditingController();

  void dispose() {
    labelController.dispose();
    urlController.dispose();
  }
}

class _RelevantLinkRow extends StatelessWidget {
  const _RelevantLinkRow({
    required this.link,
    required this.onRemove,
  });

  final _RelevantLink link;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          flex: 2,
          child: TextFormField(
            controller: link.labelController,
            decoration: const InputDecoration(
              labelText: 'Label',
              hintText: 'Doc, Logs, etc.',
              border: OutlineInputBorder(),
              isDense: true,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 3,
          child: TextFormField(
            controller: link.urlController,
            decoration: const InputDecoration(
              labelText: 'URL',
              hintText: 'https://example.com',
              border: OutlineInputBorder(),
              isDense: true,
            ),
            validator: (value) {
              if (link.labelController.text.isNotEmpty &&
                  (value == null || value.isEmpty)) {
                return 'URL is required when label is provided';
              }
              if (value != null && value.isNotEmpty) {
                final uri = Uri.tryParse(value);
                if (uri == null || !uri.hasScheme) {
                  return 'Please enter a valid URL';
                }
              }
              return null;
            },
          ),
        ),
        const SizedBox(width: 8),
        IconButton(
          icon: const Icon(Icons.delete, color: Colors.red),
          onPressed: onRemove,
          tooltip: 'Remove link',
        ),
      ],
    );
  }
}
