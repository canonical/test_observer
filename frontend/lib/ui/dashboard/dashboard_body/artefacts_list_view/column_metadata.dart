part of 'artefacts_list_view.dart';

typedef ColumnMetadata = ({
  String name,
  ArtefactSortingQuery queryParam,
  int flex,
  Widget Function(BuildContext, Artefact) cellBuilder
});

const _snapColumnsMetadata = <ColumnMetadata>[
  (
    name: 'Name',
    queryParam: ArtefactSortingQuery.name,
    flex: 2,
    cellBuilder: _buildNameCell,
  ),
  (
    name: 'Version',
    queryParam: ArtefactSortingQuery.version,
    flex: 2,
    cellBuilder: _buildVersionCell,
  ),
  (
    name: 'Track',
    queryParam: ArtefactSortingQuery.track,
    flex: 1,
    cellBuilder: _buildTrackCell,
  ),
  (
    name: 'Risk',
    queryParam: ArtefactSortingQuery.risk,
    flex: 1,
    cellBuilder: _buildStageCell,
  ),
  (
    name: 'Due date',
    queryParam: ArtefactSortingQuery.dueDate,
    flex: 1,
    cellBuilder: _buildDueDateCell,
  ),
  (
    name: 'Reviews remaining',
    queryParam: ArtefactSortingQuery.reviewsRemaining,
    flex: 1,
    cellBuilder: _buildReviewsRemainingCell,
  ),
  (
    name: 'Status',
    queryParam: ArtefactSortingQuery.status,
    flex: 1,
    cellBuilder: _buildStatusCell,
  ),
  (
    name: 'Assignee',
    queryParam: ArtefactSortingQuery.assignee,
    flex: 1,
    cellBuilder: _buildAssigneeCell,
  ),
];

const _debColumnsMetadata = <ColumnMetadata>[
  (
    name: 'Name',
    queryParam: ArtefactSortingQuery.name,
    flex: 2,
    cellBuilder: _buildNameCell,
  ),
  (
    name: 'Version',
    queryParam: ArtefactSortingQuery.version,
    flex: 2,
    cellBuilder: _buildVersionCell,
  ),
  (
    name: 'Series',
    queryParam: ArtefactSortingQuery.series,
    flex: 1,
    cellBuilder: _buildSeriesCell,
  ),
  (
    name: 'Repo',
    queryParam: ArtefactSortingQuery.repo,
    flex: 1,
    cellBuilder: _buildRepoCell,
  ),
  (
    name: 'Pocket',
    queryParam: ArtefactSortingQuery.pocket,
    flex: 1,
    cellBuilder: _buildStageCell,
  ),
  (
    name: 'Due date',
    queryParam: ArtefactSortingQuery.dueDate,
    flex: 1,
    cellBuilder: _buildDueDateCell,
  ),
  (
    name: 'Reviews remaining',
    queryParam: ArtefactSortingQuery.reviewsRemaining,
    flex: 1,
    cellBuilder: _buildReviewsRemainingCell,
  ),
  (
    name: 'Status',
    queryParam: ArtefactSortingQuery.status,
    flex: 1,
    cellBuilder: _buildStatusCell,
  ),
  (
    name: 'Assignee',
    queryParam: ArtefactSortingQuery.assignee,
    flex: 1,
    cellBuilder: _buildAssigneeCell,
  ),
];

const _charmColumnsMetadata = <ColumnMetadata>[
  (
    name: 'Name',
    queryParam: ArtefactSortingQuery.name,
    flex: 2,
    cellBuilder: _buildNameCell,
  ),
  (
    name: 'Version',
    queryParam: ArtefactSortingQuery.version,
    flex: 2,
    cellBuilder: _buildVersionCell,
  ),
  (
    name: 'Track',
    queryParam: ArtefactSortingQuery.track,
    flex: 1,
    cellBuilder: _buildTrackCell,
  ),
  (
    name: 'Risk',
    queryParam: ArtefactSortingQuery.risk,
    flex: 1,
    cellBuilder: _buildStageCell,
  ),
  (
    name: 'Due date',
    queryParam: ArtefactSortingQuery.dueDate,
    flex: 1,
    cellBuilder: _buildDueDateCell,
  ),
  (
    name: 'Reviews remaining',
    queryParam: ArtefactSortingQuery.reviewsRemaining,
    flex: 1,
    cellBuilder: _buildReviewsRemainingCell,
  ),
  (
    name: 'Status',
    queryParam: ArtefactSortingQuery.status,
    flex: 1,
    cellBuilder: _buildStatusCell,
  ),
  (
    name: 'Assignee',
    queryParam: ArtefactSortingQuery.assignee,
    flex: 1,
    cellBuilder: _buildAssigneeCell,
  ),
];

const _imageColumnsMetadata = <ColumnMetadata>[
  (
    name: 'Name',
    queryParam: ArtefactSortingQuery.name,
    flex: 2,
    cellBuilder: _buildNameCell,
  ),
  (
    name: 'Version',
    queryParam: ArtefactSortingQuery.version,
    flex: 1,
    cellBuilder: _buildVersionCell,
  ),
  (
    name: 'OS',
    queryParam: ArtefactSortingQuery.os,
    flex: 1,
    cellBuilder: _buildOSCell,
  ),
  (
    name: 'Release',
    queryParam: ArtefactSortingQuery.release,
    flex: 1,
    cellBuilder: _buildReleaseCell,
  ),
  (
    name: 'Owner',
    queryParam: ArtefactSortingQuery.owner,
    flex: 1,
    cellBuilder: _buildOwnerCell,
  ),
  (
    name: 'Due date',
    queryParam: ArtefactSortingQuery.dueDate,
    flex: 1,
    cellBuilder: _buildDueDateCell,
  ),
  (
    name: 'Reviews remaining',
    queryParam: ArtefactSortingQuery.reviewsRemaining,
    flex: 1,
    cellBuilder: _buildReviewsRemainingCell,
  ),
  (
    name: 'Status',
    queryParam: ArtefactSortingQuery.status,
    flex: 1,
    cellBuilder: _buildStatusCell,
  ),
  (
    name: 'Assignee',
    queryParam: ArtefactSortingQuery.assignee,
    flex: 1,
    cellBuilder: _buildAssigneeCell,
  ),
];

Widget _buildNameCell(BuildContext context, Artefact artefact) =>
    Text(artefact.name);

Widget _buildVersionCell(BuildContext context, Artefact artefact) =>
    Text(artefact.version);

Widget _buildTrackCell(BuildContext context, Artefact artefact) =>
    Text(artefact.track);

Widget _buildStageCell(BuildContext context, Artefact artefact) =>
    Text(artefact.stage.name);

Widget _buildSeriesCell(BuildContext context, Artefact artefact) =>
    Text(artefact.series);

Widget _buildRepoCell(BuildContext context, Artefact artefact) =>
    Text(artefact.repo);

Widget _buildDueDateCell(BuildContext context, Artefact artefact) =>
    Text(artefact.dueDateString ?? '');

Widget _buildReviewsRemainingCell(BuildContext context, Artefact artefact) =>
    Text(artefact.remainingTestExecutionCount.toString());

Widget _buildStatusCell(BuildContext context, Artefact artefact) {
  final status = artefact.status;
  return Text(
    status.name,
    style: Theme.of(context).textTheme.bodyMedium?.apply(color: status.color),
  );
}

Widget _buildAssigneeCell(BuildContext context, Artefact artefact) =>
    Text(artefact.assignee.name);

Widget _buildOSCell(BuildContext context, Artefact artefact) =>
    Text(artefact.os);

Widget _buildReleaseCell(BuildContext context, Artefact artefact) =>
    Text(artefact.release);

Widget _buildOwnerCell(BuildContext context, Artefact artefact) =>
    Text(artefact.owner);
