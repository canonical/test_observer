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
  pocket,
  os,
  release,
  owner,
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

  final compare = _getArtefactCompareFunction(sortByParsed);

  if (sortDirection == SortDirection.desc.name) {
    artefacts.sort((a1, a2) => compare(a2, a1));
  } else {
    artefacts.sort(compare);
  }
}

int Function(Artefact, Artefact) _getArtefactCompareFunction(
  ArtefactSortingQuery sortByParsed,
) {
  switch (sortByParsed) {
    case ArtefactSortingQuery.name:
      return (a1, a2) => a1.name.compareTo(a2.name);
    case ArtefactSortingQuery.version:
      return (a1, a2) => a1.version.compareTo(a2.version);
    case ArtefactSortingQuery.track:
      return (a1, a2) => a1.track.compareTo(a2.track);
    case ArtefactSortingQuery.risk:
      return (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
    case ArtefactSortingQuery.dueDate:
      return (a1, a2) {
        final a1DueDate = a1.dueDate;
        final a2DueDate = a2.dueDate;
        // no due date is always larger
        if (a1DueDate == null) return 1;
        if (a2DueDate == null) return -1;
        return a1DueDate.compareTo(a2DueDate);
      };
    case ArtefactSortingQuery.reviewsRemaining:
      return (a1, a2) => a1.remainingTestExecutionCount
          .compareTo(a2.remainingTestExecutionCount);
    case ArtefactSortingQuery.status:
      return (a1, a2) => a1.status.name.compareTo(a2.status.name);
    case ArtefactSortingQuery.assignee:
      return (a1, a2) {
        final a1Assignee = a1.assignee?.name;
        final a2Assignee = a2.assignee?.name;
        // no assignee is always larger
        if (a1Assignee == null) return 1;
        if (a2Assignee == null) return -1;
        return a1Assignee.compareTo(a2Assignee);
      };
    case ArtefactSortingQuery.series:
      return (a1, a2) => a1.series.compareTo(a2.series);
    case ArtefactSortingQuery.repo:
      return (a1, a2) => a1.repo.compareTo(a2.repo);
    case ArtefactSortingQuery.pocket:
      return (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
    case ArtefactSortingQuery.os:
      return (a1, a2) => a1.os.compareTo(a2.os);
    case ArtefactSortingQuery.release:
      return (a1, a2) => a1.release.compareTo(a2.release);
    case ArtefactSortingQuery.owner:
      return (a1, a2) => a1.owner.compareTo(a2.owner);
  }
}
