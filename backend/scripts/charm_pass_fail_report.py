#!/usr/bin/env python3
"""
Script to compile pass/fail rates for latest Charm family artifacts.
Uses the Test Observer API to fetch data and displays results in a pretty table.
"""

import argparse
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


API_BASE_URL = "https://test-observer-api.canonical.com/v1"


def fetch_charm_artefacts(api_url: str) -> list[dict[str, Any]]:
    """Fetch all latest charm artifacts from the API."""
    url = f"{api_url}/artefacts?family=charm"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching artifacts: {e}")
        sys.exit(1)


def fetch_artefact_builds(api_url: str, artefact_id: int) -> list[dict[str, Any]]:
    """Fetch builds for a specific artifact."""
    url = f"{api_url}/artefacts/{artefact_id}/builds"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not fetch builds for artifact {artefact_id}: {e}")
        return []


def filter_latest_builds(builds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter builds to keep only the latest for each (revision, architecture) combination."""
    if not builds:
        return []

    # Group builds by (revision, architecture)
    build_groups = defaultdict(list)

    for build in builds:
        revision = build.get("revision", "")
        architecture = build.get("architecture", "")
        key = (revision, architecture)
        build_groups[key].append(build)

    # For each group, keep only the latest build (by created_at or id)
    latest_builds = []
    for key, group_builds in build_groups.items():
        # Sort by created_at (descending) or by id if created_at not available
        sorted_builds = sorted(
            group_builds,
            key=lambda b: (
                b.get("created_at", ""),
                b.get("id", 0)
            ),
            reverse=True
        )
        latest_builds.append(sorted_builds[0])

    return latest_builds


def calculate_artefact_stats(
    artefact: dict[str, Any],
    builds: list[dict[str, Any]],
    exclude_not_started: bool = False
) -> dict[str, Any]:
    """Calculate pass/fail statistics for a single artifact."""
    total_executions = 0
    passed = 0
    failed = 0
    in_progress = 0
    not_started = 0
    not_tested = 0
    ended_prematurely = 0

    for build in builds:
        for test_execution in build.get("test_executions", []):
            status = test_execution.get("status", "")

            # Skip NOT_STARTED tests if flag is set
            if exclude_not_started and status == "NOT_STARTED":
                not_started += 1
                continue

            total_executions += 1

            if status == "PASSED":
                passed += 1
            elif status == "FAILED":
                failed += 1
            elif status == "IN_PROGRESS":
                in_progress += 1
            elif status == "NOT_STARTED":
                not_started += 1
            elif status == "NOT_TESTED":
                not_tested += 1
            elif status == "ENDED_PREMATURELY":
                ended_prematurely += 1

    # Calculate pass/fail rate only on completed tests (PASSED or FAILED)
    completed = passed + failed
    pass_rate = (passed / completed * 100) if completed > 0 else 0.0
    fail_rate = (failed / completed * 100) if completed > 0 else 0.0

    return {
        "name": artefact.get("name", "Unknown"),
        "version": artefact.get("version", "Unknown"),
        "track": artefact.get("track", "Unknown"),
        "stage": artefact.get("stage", "Unknown"),
        "status": artefact.get("status", "Unknown"),
        "created_at": artefact.get("created_at", "Unknown"),
        "total_executions": total_executions,
        "passed": passed,
        "failed": failed,
        "in_progress": in_progress,
        "not_started": not_started,
        "not_tested": not_tested,
        "ended_prematurely": ended_prematurely,
        "completed": completed,
        "pass_rate": pass_rate,
        "fail_rate": fail_rate,
    }


def print_table(data: list[dict[str, Any]]):
    """Print data in a pretty table format."""
    if not data:
        print("No data to display.")
        return
    
    # Table headers
    headers = [
        "Name",
        "Version",
        "Track",
        "Stage",
        "Status",
        "Total",
        "Pass",
        "Fail",
        "Pass %",
        "Fail %",
    ]
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    
    for row in data:
        col_widths[0] = max(col_widths[0], len(row["name"]))
        col_widths[1] = max(col_widths[1], len(row["version"]))
        col_widths[2] = max(col_widths[2], len(row["track"]))
        col_widths[3] = max(col_widths[3], len(row["stage"]))
        col_widths[4] = max(col_widths[4], len(row["status"]))
        col_widths[5] = max(col_widths[5], len(str(row["total_executions"])))
        col_widths[6] = max(col_widths[6], len(str(row["passed"])))
        col_widths[7] = max(col_widths[7], len(str(row["failed"])))
        col_widths[8] = max(col_widths[8], 6)  # "100.0%"
        col_widths[9] = max(col_widths[9], 6)  # "100.0%"
    
    # Print separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    
    # Print header
    print(separator)
    header_row = "|"
    for i, header in enumerate(headers):
        header_row += f" {header:<{col_widths[i]}} |"
    print(header_row)
    print(separator)
    
    # Print data rows
    for row in data:
        data_row = "|"
        data_row += f" {row['name']:<{col_widths[0]}} |"
        data_row += f" {row['version']:<{col_widths[1]}} |"
        data_row += f" {row['track']:<{col_widths[2]}} |"
        data_row += f" {row['stage']:<{col_widths[3]}} |"
        data_row += f" {row['status']:<{col_widths[4]}} |"
        data_row += f" {row['total_executions']:>{col_widths[5]}} |"
        data_row += f" {row['passed']:>{col_widths[6]}} |"
        data_row += f" {row['failed']:>{col_widths[7]}} |"
        data_row += f" {row['pass_rate']:>{col_widths[8]}.1f}% |"
        data_row += f" {row['fail_rate']:>{col_widths[9]}.1f}% |"
        print(data_row)
    
    print(separator)


def print_summary(data: list[dict[str, Any]]):
    """Print overall summary statistics."""
    if not data:
        return
    
    total_executions = sum(row["total_executions"] for row in data)
    total_passed = sum(row["passed"] for row in data)
    total_failed = sum(row["failed"] for row in data)
    total_completed = total_passed + total_failed
    
    overall_pass_rate = (total_passed / total_completed * 100) if total_completed > 0 else 0.0
    overall_fail_rate = (total_failed / total_completed * 100) if total_completed > 0 else 0.0
    
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total Artifacts:        {len(data)}")
    print(f"Total Test Executions:  {total_executions}")
    print(f"Total Passed:           {total_passed}")
    print(f"Total Failed:           {total_failed}")
    print(f"Total Completed:        {total_completed}")
    print(f"Overall Pass Rate:      {overall_pass_rate:.1f}%")
    print(f"Overall Fail Rate:      {overall_fail_rate:.1f}%")
    print("=" * 80)


def parse_month_from_date(date_str: str) -> str:
    """Parse date string and return YYYY-MM format."""
    try:
        # Handle ISO format datetime strings
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m")
    except (ValueError, AttributeError):
        return "Unknown"


def calculate_monthly_stats(data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Calculate pass/fail statistics grouped by month."""
    monthly_data = defaultdict(lambda: {
        "artifacts": 0,
        "total_executions": 0,
        "passed": 0,
        "failed": 0,
        "completed": 0,
    })

    for row in data:
        month = parse_month_from_date(row["created_at"])
        monthly_data[month]["artifacts"] += 1
        monthly_data[month]["total_executions"] += row["total_executions"]
        monthly_data[month]["passed"] += row["passed"]
        monthly_data[month]["failed"] += row["failed"]
        monthly_data[month]["completed"] += row["completed"]

    # Calculate rates
    for month in monthly_data:
        completed = monthly_data[month]["completed"]
        if completed > 0:
            monthly_data[month]["pass_rate"] = (monthly_data[month]["passed"] / completed * 100)
            monthly_data[month]["fail_rate"] = (monthly_data[month]["failed"] / completed * 100)
        else:
            monthly_data[month]["pass_rate"] = 0.0
            monthly_data[month]["fail_rate"] = 0.0

    return monthly_data


def print_monthly_summary(data: list[dict[str, Any]]):
    """Print month-by-month summary statistics."""
    if not data:
        return

    monthly_stats = calculate_monthly_stats(data)

    if not monthly_stats:
        return

    # Sort by month
    sorted_months = sorted(monthly_stats.keys())

    print("\n" + "=" * 80)
    print("MONTH-BY-MONTH SUMMARY")
    print("=" * 80)

    # Table headers
    headers = ["Month", "Artifacts", "Total", "Pass", "Fail", "Pass %", "Fail %"]

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    col_widths[0] = max(col_widths[0], 7)  # YYYY-MM format

    for month in sorted_months:
        stats = monthly_stats[month]
        col_widths[1] = max(col_widths[1], len(str(stats["artifacts"])))
        col_widths[2] = max(col_widths[2], len(str(stats["total_executions"])))
        col_widths[3] = max(col_widths[3], len(str(stats["passed"])))
        col_widths[4] = max(col_widths[4], len(str(stats["failed"])))
        col_widths[5] = max(col_widths[5], 6)  # "100.0%"
        col_widths[6] = max(col_widths[6], 6)  # "100.0%"

    # Print separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

    # Print header
    print(separator)
    header_row = "|"
    for i, header in enumerate(headers):
        header_row += f" {header:<{col_widths[i]}} |"
    print(header_row)
    print(separator)

    # Print data rows
    for month in sorted_months:
        stats = monthly_stats[month]
        data_row = "|"
        data_row += f" {month:<{col_widths[0]}} |"
        data_row += f" {stats['artifacts']:>{col_widths[1]}} |"
        data_row += f" {stats['total_executions']:>{col_widths[2]}} |"
        data_row += f" {stats['passed']:>{col_widths[3]}} |"
        data_row += f" {stats['failed']:>{col_widths[4]}} |"
        data_row += f" {stats['pass_rate']:>{col_widths[5]}.1f}% |"
        data_row += f" {stats['fail_rate']:>{col_widths[6]}.1f}% |"
        print(data_row)

    print(separator)


def process_artefact(
    artefact: dict[str, Any],
    api_url: str,
    exclude_not_started: bool,
    latest_builds_only: bool
) -> dict[str, Any]:
    """Process a single artifact: fetch builds and calculate statistics."""
    builds = fetch_artefact_builds(api_url, artefact["id"])

    # Apply build filter if requested
    if latest_builds_only:
        builds = filter_latest_builds(builds)

    return calculate_artefact_stats(artefact, builds, exclude_not_started)


def generate_html_report(data: list[dict[str, Any]], filters_info: dict[str, Any]) -> str:
    """Generate a self-contained HTML report with embedded CSS."""

    # Calculate overall summary
    total_executions = sum(row["total_executions"] for row in data)
    total_passed = sum(row["passed"] for row in data)
    total_failed = sum(row["failed"] for row in data)
    total_completed = total_passed + total_failed
    overall_pass_rate = (total_passed / total_completed * 100) if total_completed > 0 else 0.0
    overall_fail_rate = (total_failed / total_completed * 100) if total_completed > 0 else 0.0

    # Calculate monthly stats
    monthly_stats = calculate_monthly_stats(data)
    sorted_months = sorted(monthly_stats.keys())

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Charm Pass/Fail Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .header .timestamp {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .filters {{
            background: #f8f9fa;
            padding: 20px 40px;
            border-bottom: 2px solid #e9ecef;
        }}

        .filters h3 {{
            margin-bottom: 10px;
            color: #495057;
        }}

        .filters .filter-item {{
            display: inline-block;
            background: white;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 20px;
            border: 1px solid #dee2e6;
            font-size: 0.9em;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section h2 {{
            color: #495057;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            font-size: 1.8em;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .summary-card h3 {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .summary-card .label {{
            font-size: 0.95em;
            opacity: 0.8;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}

        th.number {{
            text-align: right;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}

        td.number {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}

        tbody tr:hover {{
            background: #f8f9fa;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .pass-rate {{
            color: #28a745;
            font-weight: 600;
        }}

        .fail-rate {{
            color: #dc3545;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-approved {{
            background: #d4edda;
            color: #155724;
        }}

        .badge-pending {{
            background: #fff3cd;
            color: #856404;
        }}

        .badge-rejected {{
            background: #f8d7da;
            color: #721c24;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
            border-top: 2px solid #e9ecef;
        }}

        /* Sortable table styles */
        th.sortable {{
            cursor: pointer;
            user-select: none;
            position: relative;
            padding-right: 25px;
        }}

        th.sortable:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}

        th.sortable::after {{
            content: '⇅';
            position: absolute;
            right: 8px;
            opacity: 0.3;
            font-size: 0.9em;
        }}

        th.sortable.asc::after {{
            content: '↑';
            opacity: 1;
        }}

        th.sortable.desc::after {{
            content: '↓';
            opacity: 1;
        }}
    </style>
    <script>
        function setupSortableTables() {{
            // Get all tables
            const tables = document.querySelectorAll('table');

            tables.forEach(table => {{
                const headers = table.querySelectorAll('th');
                const tbody = table.querySelector('tbody');

                if (!tbody) return;

                headers.forEach((header, index) => {{
                    // Make header sortable
                    header.classList.add('sortable');

                    header.addEventListener('click', () => {{
                        const rows = Array.from(tbody.querySelectorAll('tr'));
                        const isNumeric = header.classList.contains('number');
                        const currentSort = header.classList.contains('asc') ? 'asc' :
                                           header.classList.contains('desc') ? 'desc' : 'none';

                        // Remove sort classes from all headers
                        headers.forEach(h => h.classList.remove('asc', 'desc'));

                        // Determine new sort direction
                        const newSort = currentSort === 'asc' ? 'desc' : 'asc';
                        header.classList.add(newSort);

                        // Sort rows
                        rows.sort((a, b) => {{
                            const aCell = a.children[index];
                            const bCell = b.children[index];

                            if (!aCell || !bCell) return 0;

                            let aValue = aCell.textContent.trim();
                            let bValue = bCell.textContent.trim();

                            // Handle numeric values
                            if (isNumeric) {{
                                // Remove commas and percentage signs
                                aValue = parseFloat(aValue.replace(/[,%]/g, '')) || 0;
                                bValue = parseFloat(bValue.replace(/[,%]/g, '')) || 0;
                                return newSort === 'asc' ? aValue - bValue : bValue - aValue;
                            }}

                            // Handle string values
                            const comparison = aValue.localeCompare(bValue, undefined, {{
                                numeric: true,
                                sensitivity: 'base'
                            }});
                            return newSort === 'asc' ? comparison : -comparison;
                        }});

                        // Re-append sorted rows
                        rows.forEach(row => tbody.appendChild(row));
                    }});
                }});
            }});
        }}

        // Initialize sorting when page loads
        document.addEventListener('DOMContentLoaded', setupSortableTables);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Charm Pass/Fail Report</h1>
            <div class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        </div>
"""

    # Add filters section if any filters are applied
    if any(filters_info.values()):
        html += """
        <div class="filters">
            <h3>Active Filters</h3>
"""
        for filter_name, filter_value in filters_info.items():
            if filter_value:
                html += f'            <span class="filter-item">{filter_name}: {filter_value}</span>\n'
        html += """
        </div>
"""

    html += """
        <div class="content">
            <div class="section">
                <h2>Overall Summary</h2>
                <div class="summary-grid">
"""

    html += f"""
                    <div class="summary-card">
                        <h3>Total Artifacts</h3>
                        <div class="value">{len(data)}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Test Executions</h3>
                        <div class="value">{total_executions:,}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Pass Rate</h3>
                        <div class="value">{overall_pass_rate:.1f}%</div>
                        <div class="label">{total_passed:,} passed</div>
                    </div>
                    <div class="summary-card">
                        <h3>Fail Rate</h3>
                        <div class="value">{overall_fail_rate:.1f}%</div>
                        <div class="label">{total_failed:,} failed</div>
                    </div>
"""

    html += """
                </div>
            </div>
"""

    # Monthly summary section
    if monthly_stats:
        html += """
            <div class="section">
                <h2>Month-by-Month Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th class="number">Artifacts</th>
                            <th class="number">Total</th>
                            <th class="number">Pass</th>
                            <th class="number">Fail</th>
                            <th class="number">Pass %</th>
                            <th class="number">Fail %</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for month in sorted_months:
            stats = monthly_stats[month]
            html += f"""
                        <tr>
                            <td>{month}</td>
                            <td class="number">{stats['artifacts']}</td>
                            <td class="number">{stats['total_executions']:,}</td>
                            <td class="number">{stats['passed']:,}</td>
                            <td class="number">{stats['failed']:,}</td>
                            <td class="number pass-rate">{stats['pass_rate']:.1f}%</td>
                            <td class="number fail-rate">{stats['fail_rate']:.1f}%</td>
                        </tr>
"""
        html += """
                    </tbody>
                </table>
            </div>
"""

    # Detailed artifacts table
    html += """
            <div class="section">
                <h2>Detailed Artifact Results</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Version</th>
                            <th>Track</th>
                            <th>Stage</th>
                            <th>Status</th>
                            <th class="number">Total</th>
                            <th class="number">Pass</th>
                            <th class="number">Fail</th>
                            <th class="number">Pass %</th>
                            <th class="number">Fail %</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for row in data:
        status_class = "badge-approved" if row['status'] == "APPROVED" else "badge-pending"
        html += f"""
                        <tr>
                            <td><strong>{row['name']}</strong></td>
                            <td>{row['version']}</td>
                            <td>{row['track']}</td>
                            <td>{row['stage']}</td>
                            <td><span class="badge {status_class}">{row['status']}</span></td>
                            <td class="number">{row['total_executions']}</td>
                            <td class="number">{row['passed']}</td>
                            <td class="number">{row['failed']}</td>
                            <td class="number pass-rate">{row['pass_rate']:.1f}%</td>
                            <td class="number fail-rate">{row['fail_rate']:.1f}%</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>
        </div>
        <div class="footer">
            <p>Generated by Charm Pass/Fail Report Tool</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate pass/fail rate report for latest Charm family artifacts"
    )
    parser.add_argument(
        "--api-url",
        default=API_BASE_URL,
        help=f"API base URL (default: {API_BASE_URL})"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information including in-progress and not-started tests"
    )
    parser.add_argument(
        "--sort-by",
        choices=["name", "pass_rate", "fail_rate", "total"],
        default="name",
        help="Sort artifacts by field (default: name)"
    )
    parser.add_argument(
        "--exclude-not-started",
        action="store_true",
        help="Exclude NOT_STARTED tests from statistics"
    )
    parser.add_argument(
        "--latest-builds-only",
        action="store_true",
        help="Only include the latest build for each (revision, architecture) combination"
    )
    parser.add_argument(
        "--parallelism",
        "-p",
        type=int,
        default=5,
        help="Number of parallel workers for processing artifacts (default: 5)"
    )
    parser.add_argument(
        "--stages",
        "-s",
        type=str,
        help="Comma-separated list of stages to include (e.g., 'beta,candidate,stable')"
    )
    parser.add_argument(
        "--exclude-pattern",
        "-x",
        type=str,
        help="Regular expression pattern to exclude artifacts by name (e.g., 'test-.*' or '.*-dev$')"
    )
    parser.add_argument(
        "--html-output",
        "-o",
        type=str,
        help="Export report to HTML file (e.g., 'report.html')"
    )

    args = parser.parse_args()

    # Parse stages filter if provided
    stage_filter = None
    if args.stages:
        stage_filter = set(stage.strip() for stage in args.stages.split(","))
        print(f"Note: Filtering to include only stages: {', '.join(sorted(stage_filter))}")

    # Compile exclude pattern if provided
    exclude_pattern = None
    if args.exclude_pattern:
        try:
            exclude_pattern = re.compile(args.exclude_pattern)
            print(f"Note: Excluding artifacts matching pattern: '{args.exclude_pattern}'")
        except re.error as e:
            print(f"Error: Invalid regular expression pattern: {e}")
            sys.exit(1)

    if args.exclude_not_started:
        print("Note: Excluding NOT_STARTED tests from statistics")

    if args.latest_builds_only:
        print("Note: Only including latest build for each (revision, architecture) combination")

    print("Fetching Charm family artifacts...")
    artefacts = fetch_charm_artefacts(args.api_url)

    if not artefacts:
        print("No Charm artifacts found.")
        return

    # Filter artifacts by stage if requested
    if stage_filter:
        original_count = len(artefacts)
        artefacts = [a for a in artefacts if a.get("stage", "") in stage_filter]
        print(f"Filtered {original_count} artifacts to {len(artefacts)} matching selected stages")

        if not artefacts:
            print("No Charm artifacts found matching the selected stages.")
            return

    # Exclude artifacts by name pattern if requested
    if exclude_pattern:
        original_count = len(artefacts)
        excluded_names = []
        filtered_artefacts = []

        for a in artefacts:
            name = a.get("name", "")
            if exclude_pattern.search(name):
                excluded_names.append(name)
            else:
                filtered_artefacts.append(a)

        artefacts = filtered_artefacts
        print(f"Excluded {len(excluded_names)} artifacts matching pattern (remaining: {len(artefacts)})")

        if excluded_names and len(excluded_names) <= 10:
            print(f"  Excluded: {', '.join(excluded_names)}")
        elif excluded_names:
            print(f"  Excluded: {', '.join(excluded_names[:10])}, ... and {len(excluded_names) - 10} more")

        if not artefacts:
            print("No Charm artifacts remaining after exclusion pattern.")
            return

    print(f"Found {len(artefacts)} Charm artifacts. Fetching test execution data...")
    print(f"Using {args.parallelism} parallel workers...")

    results = []
    completed_count = 0
    total_count = len(artefacts)

    # Process artifacts in parallel
    with ThreadPoolExecutor(max_workers=args.parallelism) as executor:
        # Submit all tasks
        future_to_artefact = {
            executor.submit(
                process_artefact,
                artefact,
                args.api_url,
                args.exclude_not_started,
                args.latest_builds_only
            ): artefact
            for artefact in artefacts
        }

        # Collect results as they complete
        for future in as_completed(future_to_artefact):
            artefact = future_to_artefact[future]
            completed_count += 1
            print(f"Processing {completed_count}/{total_count}: {artefact['name']}...", end="\r")

            try:
                stats = future.result()
                results.append(stats)
            except Exception as exc:
                print(f"\nError processing {artefact['name']}: {exc}")

    # Clear the progress line
    print(" " * 80, end="\r")
    print()
    
    # Sort results
    if args.sort_by == "name":
        results.sort(key=lambda x: x["name"])
    elif args.sort_by == "pass_rate":
        results.sort(key=lambda x: x["pass_rate"], reverse=True)
    elif args.sort_by == "fail_rate":
        results.sort(key=lambda x: x["fail_rate"], reverse=True)
    elif args.sort_by == "total":
        results.sort(key=lambda x: x["total_executions"], reverse=True)
    
    print_table(results)
    print_summary(results)
    print_monthly_summary(results)

    if args.verbose:
        print("\nDETAILED BREAKDOWN")
        print("=" * 80)
        for row in results:
            if row["in_progress"] > 0 or row["not_started"] > 0 or row["not_tested"] > 0 or row["ended_prematurely"] > 0:
                print(f"\n{row['name']} ({row['version']}):")
                if row["in_progress"] > 0:
                    print(f"  In Progress:       {row['in_progress']}")
                if row["not_started"] > 0:
                    print(f"  Not Started:       {row['not_started']}")
                if row["not_tested"] > 0:
                    print(f"  Not Tested:        {row['not_tested']}")
                if row["ended_prematurely"] > 0:
                    print(f"  Ended Prematurely: {row['ended_prematurely']}")

    # Export to HTML if requested
    if args.html_output:
        print(f"\nGenerating HTML report: {args.html_output}")

        # Collect filter information for the report
        filters_info = {}
        if stage_filter:
            filters_info["Stages"] = ', '.join(sorted(stage_filter))
        if exclude_pattern:
            filters_info["Exclude Pattern"] = args.exclude_pattern
        if args.exclude_not_started:
            filters_info["Exclude Not Started"] = "Yes"
        if args.latest_builds_only:
            filters_info["Latest Builds Only"] = "Yes"
        if args.sort_by != "name":
            filters_info["Sort By"] = args.sort_by.replace("_", " ").title()

        # Generate HTML
        html_content = generate_html_report(results, filters_info)

        # Write to file
        try:
            with open(args.html_output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✓ HTML report successfully saved to: {args.html_output}")
        except Exception as e:
            print(f"Error writing HTML file: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
