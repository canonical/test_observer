// Copyright (C) 2024 Canonical Ltd.
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

import 'constants.dart';

String? validateIssueUrl(String? url) {
  if (url == null || url.isEmpty) {
    return 'Must provide a bug/jira link to the issue';
  }

  final parsedUrl = Uri.tryParse(url);
  if (parsedUrl == null) {
    return 'Provided url is not valid';
  } else if (!validIssueHosts.contains(parsedUrl.host)) {
    final validUrlPrefixes = validIssueHosts.map((host) => 'https://$host');
    return 'Issue url must must start with one of $validUrlPrefixes';
  }
  return null;
}
