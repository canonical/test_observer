part of 'artefacts_list_view.dart';

class _Row extends StatelessWidget {
  const _Row({
    required this.artefact,
    required this.columnsMetaData,
  });

  final Artefact artefact;
  final List<ColumnMetadata> columnsMetaData;

  const _Row.deb({super.key, required this.artefact})
      : columnsMetaData = _debColumnsMetadata;

  const _Row.snap({super.key, required this.artefact})
      : columnsMetaData = _snapColumnsMetadata;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {
        final currentRoute = GoRouterState.of(context).fullPath;
        context.go('$currentRoute/${artefact.id}');
      },
      child: SizedBox(
        height: 48,
        child: Row(
          children: columnsMetaData
              .map(
                (data) => Expanded(
                  flex: data.flex,
                  child: data.cellBuilder(context, artefact),
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}
