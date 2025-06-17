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
import 'package:url_launcher/url_launcher.dart';

import '../../providers/reports.dart';
import '../spacing.dart';

class KnownIssuesReportPage extends ConsumerStatefulWidget {
  const KnownIssuesReportPage({super.key});

  @override
  ConsumerState<KnownIssuesReportPage> createState() => _KnownIssuesReportPageState();
}

class _KnownIssuesReportPageState extends ConsumerState<KnownIssuesReportPage> {
  // Sorting states for Known Issues table
  int? _knownIssuesSortColumnIndex;
  bool _knownIssuesSortAscending = true;
  String _knownIssuesFilterText = '';

  @override
  Widget build(BuildContext context) {
    final knownIssuesReportAsync = ref.watch(knownIssuesReportProvider);

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: Spacing.level5),
          Text(
            'Test Case Issues',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const SizedBox(height: Spacing.level4),
          Expanded(
            child: SingleChildScrollView(
              child: _buildKnownIssuesSection(knownIssuesReportAsync),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterTextField({
    required String hintText,
    required String value,
    required ValueChanged<String> onChanged,
  }) {
    return SizedBox(
      width: 300,
      child: TextField(
        decoration: InputDecoration(
          hintText: hintText,
          prefixIcon: const Icon(Icons.search),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildKnownIssuesSection(AsyncValue<Map<String, dynamic>> knownIssuesReportAsync) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Test Case Issues',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            _buildFilterTextField(
              hintText: 'Filter issues...',
              value: _knownIssuesFilterText,
              onChanged: (value) {
                setState(() {
                  _knownIssuesFilterText = value;
                });
              },
            ),
          ],
        ),
        const SizedBox(height: Spacing.level4),
        knownIssuesReportAsync.when(
          data: (data) => _buildKnownIssuesContent(data),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, stack) => Center(
            child: Text('Error: $error'),
          ),
        ),
      ],
    );
  }

  Widget _buildKnownIssuesContent(Map<String, dynamic> data) {
    var issues = data['issues'] as List<dynamic>? ?? [];
    final totalCount = data['total_count'] ?? 0;

    if (issues.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No known issues found'),
        ),
      );
    }

    // Apply filtering
    if (_knownIssuesFilterText.isNotEmpty) {
      final filterLower = _knownIssuesFilterText.toLowerCase();
      issues = issues.where((issue) {
        return (issue['template_id']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['case_name']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['description']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['url']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['issue_status']?.toString().toLowerCase().contains(filterLower) ?? false);
      }).toList();
    }

    // Apply sorting
    if (_knownIssuesSortColumnIndex != null) {
      issues.sort((a, b) {
        dynamic aValue, bValue;
        switch (_knownIssuesSortColumnIndex) {
          case 0:
            aValue = a['id'] ?? 0;
            bValue = b['id'] ?? 0;
            break;
          case 1:
            aValue = a['template_id'] ?? '';
            bValue = b['template_id'] ?? '';
            break;
          case 2:
            aValue = a['case_name'] ?? '';
            bValue = b['case_name'] ?? '';
            break;
          case 3:
            aValue = a['description'] ?? '';
            bValue = b['description'] ?? '';
            break;
          case 4:
            aValue = a['url'] ?? '';
            bValue = b['url'] ?? '';
            break;
          case 5:
            aValue = a['issue_status'] ?? 'UNKNOWN';
            bValue = b['issue_status'] ?? 'UNKNOWN';
            break;
          case 6:
            aValue = DateTime.parse(a['created_at'] ?? DateTime.now().toIso8601String());
            bValue = DateTime.parse(b['created_at'] ?? DateTime.now().toIso8601String());
            break;
          case 7:
            aValue = DateTime.parse(a['updated_at'] ?? DateTime.now().toIso8601String());
            bValue = DateTime.parse(b['updated_at'] ?? DateTime.now().toIso8601String());
            break;
          default:
            return 0;
        }
        
        final comparison = aValue.compareTo(bValue);
        return _knownIssuesSortAscending ? comparison : -comparison;
      });
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Total Issues: $totalCount (Showing ${issues.length})',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level3),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            sortColumnIndex: _knownIssuesSortColumnIndex,
            sortAscending: _knownIssuesSortAscending,
            columnSpacing: 12.0,
            horizontalMargin: 8.0,
            columns: [
              DataColumn(
                label: const Text('ID', style: TextStyle(fontWeight: FontWeight.bold)),
                numeric: true,
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Template ID', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Case Name', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Description', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('URL', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Status', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Created At', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Updated At', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _knownIssuesSortColumnIndex = columnIndex;
                    _knownIssuesSortAscending = ascending;
                  });
                },
              ),
            ],
            rows: issues.map((issue) {
              final createdAt = DateTime.parse(issue['created_at']);
              final updatedAt = DateTime.parse(issue['updated_at']);

              return DataRow(cells: [
                DataCell(Text(issue['id']?.toString() ?? '')),
                DataCell(
                  SizedBox(
                    width: 200,
                    child: Text(
                      issue['template_id'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      maxLines: 2,
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 200,
                    child: Text(
                      issue['case_name'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      maxLines: 2,
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 300,
                    child: Text(
                      issue['description'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      maxLines: 3,
                    ),
                  ),
                ),
                DataCell(
                  InkWell(
                    onTap: () => _launchUrl(issue['url'] ?? ''),
                    child: Text(
                      issue['url'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ),
                DataCell(_buildStatusChip(issue['issue_status'])),
                DataCell(Text(_formatDateTime(createdAt))),
                DataCell(Text(_formatDateTime(updatedAt))),
              ]);
            }).toList(),
          ),
        ),
      ],
    );
  }

  String _formatDateTime(DateTime? dateTime) {
    if (dateTime == null) return 'N/A';
    return '${dateTime.year}-${dateTime.month.toString().padLeft(2, '0')}-${dateTime.day.toString().padLeft(2, '0')} ${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}:${dateTime.second.toString().padLeft(2, '0')}';
  }

  Widget _buildStatusChip(String? status) {
    final statusValue = status ?? 'UNKNOWN';
    Color chipColor;
    Color textColor;
    
    switch (statusValue.toUpperCase()) {
      case 'OPEN':
        chipColor = Theme.of(context).colorScheme.errorContainer;
        textColor = Theme.of(context).colorScheme.onErrorContainer;
        break;
      case 'CLOSED':
        chipColor = Theme.of(context).colorScheme.primaryContainer;
        textColor = Theme.of(context).colorScheme.onPrimaryContainer;
        break;
      case 'UNKNOWN':
      default:
        chipColor = Theme.of(context).colorScheme.surfaceContainerHighest;
        textColor = Theme.of(context).colorScheme.onSurface;
        break;
    }
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        statusValue,
        style: TextStyle(
          color: textColor,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}