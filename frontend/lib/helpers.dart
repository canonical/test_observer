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
