part of 'artefacts_list_view.dart';

typedef ColumnMetadata = ({
  String name,
  int flex,
  Widget Function(BuildContext, Artefact) cellBuilder
});

const _snapColumnsMetadata = <ColumnMetadata>[
  (name: 'Name', flex: 2, cellBuilder: _buildNameCell),
  (name: 'Version', flex: 2, cellBuilder: _buildVersionCell),
  (name: 'Track', flex: 1, cellBuilder: _buildTrackCell),
  (name: 'Risk', flex: 1, cellBuilder: _buildStageCell),
  (name: 'Due date', flex: 1, cellBuilder: _buildDueDateCell),
  (name: 'Status', flex: 1, cellBuilder: _buildStatusCell),
  (name: 'Assignee', flex: 1, cellBuilder: _buildAssigneeCell),
];

const _debColumnsMetadata = <ColumnMetadata>[
  (name: 'Name', flex: 2, cellBuilder: _buildNameCell),
  (name: 'Version', flex: 2, cellBuilder: _buildVersionCell),
  (name: 'Series', flex: 1, cellBuilder: _buildSeriesCell),
  (name: 'Repo', flex: 1, cellBuilder: _buildRepoCell),
  (name: 'Pocket', flex: 1, cellBuilder: _buildStageCell),
  (name: 'Due date', flex: 1, cellBuilder: _buildDueDateCell),
  (name: 'Status', flex: 1, cellBuilder: _buildStatusCell),
  (name: 'Assignee', flex: 1, cellBuilder: _buildAssigneeCell),
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

Widget _buildStatusCell(BuildContext context, Artefact artefact) {
  final status = artefact.status;
  return Text(
    status.name,
    style: Theme.of(context).textTheme.bodyMedium?.apply(color: status.color),
  );
}

Widget _buildAssigneeCell(BuildContext context, Artefact artefact) {
  final assignee = artefact.assignee;
  return assignee == null
      ? const SizedBox.shrink()
      : Align(
          alignment: Alignment.centerLeft,
          child: UserAvatar(
            user: assignee,
            allTestExecutionsCount: artefact.allTestExecutionsCount,
            completedTestExecutionsCount: artefact.completedTestExecutionsCount,
          ),
        );
}
