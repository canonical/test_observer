part of 'artefacts_list_view.dart';

class _Headers extends StatelessWidget {
  const _Headers({required this.columnsMetaData});

  final List<ColumnMetadata> columnsMetaData;

  const _Headers.debs({super.key}) : columnsMetaData = _debColumnsMetadata;

  const _Headers.snaps({super.key}) : columnsMetaData = _snapColumnsMetadata;

  @override
  Widget build(BuildContext context) {
    final uri = AppRoutes.uriFromContext(context);
    final sortBy = uri.queryParameters[CommonQueryParameters.sortBy];
    final sortDirection =
        uri.queryParameters[CommonQueryParameters.sortDirection];

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
                        if (sortDirection == SortDirection.asc.name)
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
    final direction = queryParameters[CommonQueryParameters.sortBy] == sortBy &&
            queryParameters[CommonQueryParameters.sortDirection] ==
                SortDirection.asc.name
        ? SortDirection.desc.name
        : SortDirection.asc.name;
    final newQueryParameters = {
      ...queryParameters,
      CommonQueryParameters.sortBy: sortBy,
      CommonQueryParameters.sortDirection: direction,
    };
    context.go(pageUri.replace(queryParameters: newQueryParameters).toString());
  }
}
