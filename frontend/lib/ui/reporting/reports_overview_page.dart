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
import 'package:go_router/go_router.dart';

import '../../routing.dart';
import '../spacing.dart';

class ReportsOverviewPage extends StatelessWidget {
  const ReportsOverviewPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: Spacing.level5),
          Text(
            'Reports',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const SizedBox(height: Spacing.level4),
          Text(
            'Select a report type to view detailed information:',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: Spacing.level5),
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              crossAxisSpacing: Spacing.level4,
              mainAxisSpacing: Spacing.level4,
              childAspectRatio: 2.5,
              children: [
                _buildReportCard(
                  context,
                  'Success Rate by Test Case',
                  'View success rates and statistics by test case',
                  Icons.analytics,
                  AppRoutes.testSummaryReport,
                ),
                _buildReportCard(
                  context,
                  'Test Case Issues',
                  'Browse and filter known test case issues',
                  Icons.bug_report,
                  AppRoutes.knownIssuesReport,
                ),
                _buildReportCard(
                  context,
                  'Environment Issues',
                  'Review environment-specific issues and confirmations',
                  Icons.computer,
                  AppRoutes.environmentIssuesReport,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReportCard(
    BuildContext context,
    String title,
    String description,
    IconData icon,
    String route,
  ) {
    return Card(
      elevation: 2,
      child: InkWell(
        onTap: () => context.go(route),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    icon,
                    size: 32,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: Spacing.level3),
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(context).textTheme.titleLarge,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: Spacing.level3),
              Expanded(
                child: Text(
                  description,
                  style: Theme.of(context).textTheme.bodyMedium,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}