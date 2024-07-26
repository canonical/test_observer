part of 'artefacts_list_view.dart';

class _Headers extends StatelessWidget {
  const _Headers({required this.columnsMetaData});

  final List<ColumnMetadata> columnsMetaData;

  const _Headers.debs({super.key}) : columnsMetaData = _debColumnsMetadata;

  const _Headers.snaps({super.key}) : columnsMetaData = _snapColumnsMetadata;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 56,
      child: Row(
        children: columnsMetaData
            .map(
              (data) => Expanded(
                flex: data.flex,
                child: Text(
                  data.name,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}
