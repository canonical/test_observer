part of 'artefacts_list_view.dart';

class _Headers extends StatelessWidget {
  const _Headers({required this.columnsMetaData});

  final List<ColumnMetadata> columnsMetaData;

  const _Headers.debs({super.key}) : columnsMetaData = _debColumnsMetadata;

  const _Headers.snaps({super.key}) : columnsMetaData = _snapColumnsMetadata;

  @override
  Widget build(BuildContext context) {
    final uri = AppRoutes.uriFromContext(context);
    final sortBy = uri.queryParameters['sortBy'];
    final sortDirection = uri.queryParameters['direction'];

    return SizedBox(
      height: 56,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: columnsMetaData
            .map(
              (data) => Expanded(
                flex: data.flex,
                child: InkWell(
                  onTap: () => _handleFilterTap(context, uri, data.name),
                  child: Row(
                    children: [
                      Flexible(
                        child: Text(
                          data.name,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ),
                      if (sortBy == data.name)
                        if (sortDirection == 'ASC')
                          const Icon(Icons.arrow_upward)
                        else
                          const Icon(Icons.arrow_downward),
                    ],
                  ),
                ),
              ),
            )
            .toList(),
      ),
    );
  }

  void _handleFilterTap(BuildContext context, Uri pageUri, String columnName) {
    final queryParameters = pageUri.queryParameters;
    final sortBy = columnName;
    final direction = queryParameters['sortBy'] == sortBy &&
            queryParameters['direction'] == 'ASC'
        ? 'DESC'
        : 'ASC';
    final newQueryParameters = {
      ...queryParameters,
      'sortBy': sortBy,
      'direction': direction,
    };
    context.go(pageUri.replace(queryParameters: newQueryParameters).toString());
  }
}
