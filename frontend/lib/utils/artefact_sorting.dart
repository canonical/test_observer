import 'package:dartx/dartx.dart';

import '../models/artefact.dart';
import '../routing.dart';

enum ArtefactSortingQuery {
  name,
  version,
  track,
  risk,
  dueDate,
  reviewsRemaining,
  status,
  assignee,
  series,
  repo,
  pocket
}

void sortArtefacts(
  Map<String, String> queryParameters,
  List<Artefact> artefacts,
) {
  final sortBy = queryParameters[CommonQueryParameters.sortBy] ?? '';
  final sortDirection = queryParameters[CommonQueryParameters.sortDirection];

  ArtefactSortingQuery sortByParsed = ArtefactSortingQuery.name;
  try {
    sortByParsed = ArtefactSortingQuery.values.byName(sortBy);
  } on ArgumentError {
    // use default
  }

  int Function(Artefact, Artefact) compare;
  switch (sortByParsed) {
    case ArtefactSortingQuery.name:
      compare = (a1, a2) => a1.name.compareTo(a2.name);
      break;
    case ArtefactSortingQuery.version:
      compare = (a1, a2) => a1.version.compareTo(a2.version);
      break;
    case ArtefactSortingQuery.track:
      compare = (a1, a2) => a1.track.compareTo(a2.track);
      break;
    case ArtefactSortingQuery.risk:
      compare = (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
      break;
    case ArtefactSortingQuery.dueDate:
      compare = (a1, a2) {
        final a1DueDate = a1.dueDate;
        final a2DueDate = a2.dueDate;
        // no due date is always larger
        if (a1DueDate == null) return 1;
        if (a2DueDate == null) return -1;
        return a1DueDate.compareTo(a2DueDate);
      };
      break;
    case ArtefactSortingQuery.reviewsRemaining:
      compare = (a1, a2) => a1.remainingTestExecutionCount
          .compareTo(a2.remainingTestExecutionCount);
      break;
    case ArtefactSortingQuery.status:
      compare = (a1, a2) => a1.status.name.compareTo(a2.status.name);
      break;
    case ArtefactSortingQuery.assignee:
      compare = (a1, a2) {
        final a1Assignee = a1.assignee?.name;
        final a2Assignee = a2.assignee?.name;
        // no assignee is always larger
        if (a1Assignee == null) return 1;
        if (a2Assignee == null) return -1;
        return a1Assignee.compareTo(a2Assignee);
      };
      break;
    case ArtefactSortingQuery.series:
      compare = (a1, a2) => a1.series.compareTo(a2.series);
      break;
    case ArtefactSortingQuery.repo:
      compare = (a1, a2) => a1.repo.compareTo(a2.repo);
      break;
    case ArtefactSortingQuery.pocket:
      compare = (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
      break;
  }

  if (sortDirection == SortDirection.desc.name) {
    artefacts.sort((a1, a2) => compare(a2, a1));
  } else {
    artefacts.sort(compare);
  }
}
