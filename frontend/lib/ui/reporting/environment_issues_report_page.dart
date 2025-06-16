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

class EnvironmentIssuesReportPage extends ConsumerStatefulWidget {
  const EnvironmentIssuesReportPage({super.key});

  @override
  ConsumerState<EnvironmentIssuesReportPage> createState() => _EnvironmentIssuesReportPageState();
}

class _EnvironmentIssuesReportPageState extends ConsumerState<EnvironmentIssuesReportPage> {
  // Sorting states for Environment Issues table
  int? _environmentIssuesSortColumnIndex;
  bool _environmentIssuesSortAscending = true;
  String _environmentIssuesFilterText = '';

  @override
  Widget build(BuildContext context) {
    final environmentIssuesReportAsync = ref.watch(environmentIssuesReportProvider);

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: Spacing.level5),
          Text(
            'Environment Issues',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const SizedBox(height: Spacing.level4),
          Expanded(
            child: SingleChildScrollView(
              child: _buildEnvironmentIssuesSection(environmentIssuesReportAsync),
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

  Widget _buildEnvironmentIssuesSection(AsyncValue<Map<String, dynamic>> environmentIssuesReportAsync) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Environment Issues',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            _buildFilterTextField(
              hintText: 'Filter issues...',
              value: _environmentIssuesFilterText,
              onChanged: (value) {
                setState(() {
                  _environmentIssuesFilterText = value;
                });
              },
            ),
          ],
        ),
        const SizedBox(height: Spacing.level4),
        environmentIssuesReportAsync.when(
          data: (data) => _buildEnvironmentIssuesContent(data),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, stack) => Center(
            child: Text('Error: $error'),
          ),
        ),
      ],
    );
  }

  Widget _buildEnvironmentIssuesContent(Map<String, dynamic> data) {
    var issues = data['issues'] as List<dynamic>? ?? [];
    final totalCount = data['total_count'] ?? 0;

    if (issues.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No known environment issues found'),
        ),
      );
    }

    // Apply filtering
    if (_environmentIssuesFilterText.isNotEmpty) {
      final filterLower = _environmentIssuesFilterText.toLowerCase();
      issues = issues.where((issue) {
        return (issue.environmentName?.toLowerCase().contains(filterLower) ?? false) ||
               (issue.description?.toLowerCase().contains(filterLower) ?? false) ||
               (issue.url?.toString().toLowerCase().contains(filterLower) ?? false);
      }).toList();
    }

    // Apply sorting
    if (_environmentIssuesSortColumnIndex != null) {
      issues.sort((a, b) {
        dynamic aValue, bValue;
        switch (_environmentIssuesSortColumnIndex) {
          case 0:
            aValue = a.id ?? 0;
            bValue = b.id ?? 0;
            break;
          case 1:
            aValue = a.environmentName ?? '';
            bValue = b.environmentName ?? '';
            break;
          case 2:
            aValue = a.description ?? '';
            bValue = b.description ?? '';
            break;
          case 3:
            aValue = a.url?.toString() ?? '';
            bValue = b.url?.toString() ?? '';
            break;
          case 4:
            aValue = a.isConfirmed ? 1 : 0;
            bValue = b.isConfirmed ? 1 : 0;
            break;
          default:
            return 0;
        }
        
        final comparison = aValue.compareTo(bValue);
        return _environmentIssuesSortAscending ? comparison : -comparison;
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
            sortColumnIndex: _environmentIssuesSortColumnIndex,
            sortAscending: _environmentIssuesSortAscending,
            columnSpacing: 12.0,
            horizontalMargin: 8.0,
            columns: [
              DataColumn(
                label: const Text('ID', style: TextStyle(fontWeight: FontWeight.bold)),
                numeric: true,
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _environmentIssuesSortColumnIndex = columnIndex;
                    _environmentIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Environment', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _environmentIssuesSortColumnIndex = columnIndex;
                    _environmentIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Description', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _environmentIssuesSortColumnIndex = columnIndex;
                    _environmentIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('URL', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _environmentIssuesSortColumnIndex = columnIndex;
                    _environmentIssuesSortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Confirmed', style: TextStyle(fontWeight: FontWeight.bold)),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _environmentIssuesSortColumnIndex = columnIndex;
                    _environmentIssuesSortAscending = ascending;
                  });
                },
              ),
            ],
            rows: issues.map((issue) {
              return DataRow(cells: [
                DataCell(Text(issue.id.toString())),
                DataCell(
                  SizedBox(
                    width: 150,
                    child: Text(
                      issue.environmentName,
                      overflow: TextOverflow.ellipsis,
                      maxLines: 2,
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 300,
                    child: Text(
                      issue.description,
                      overflow: TextOverflow.ellipsis,
                      maxLines: 3,
                    ),
                  ),
                ),
                DataCell(
                  issue.url != null && issue.url.toString().isNotEmpty
                      ? InkWell(
                          onTap: () => _launchUrl(issue.url.toString()),
                          child: Text(
                            issue.url.toString(),
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.primary,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                        )
                      : const Text(''),
                ),
                DataCell(
                  Icon(
                    issue.isConfirmed ? Icons.check_circle : Icons.help_outline,
                    color: issue.isConfirmed ? Colors.green : Colors.orange,
                    size: 20,
                  ),
                ),
              ]);
            }).toList(),
          ),
        ),
      ],
    );
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}