part of 'artefacts_list_view.dart';

class _Headers extends StatelessWidget {
  const _Headers({required this.columnsMetaData});

  final List<ColumnMetadata> columnsMetaData;

  const _Headers.debs({super.key}) : columnsMetaData = _debColumnsMetadata;

  const _Headers.snaps({super.key}) : columnsMetaData = _snapColumnsMetadata;

  const _Headers.charms({super.key}) : columnsMetaData = _charmColumnsMetadata;

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
                  onTap: () => _handleFilterTap(context, uri, data),
                  child: Row(
                    children: [
                      Flexible(
                        child: Text(
                          data.name,
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                      ),
                      if (sortBy == data.queryParam.name)
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

  void _handleFilterTap(
    BuildContext context,
    Uri pageUri,
    ColumnMetadata columnData,
  ) {
    final queryParameters = pageUri.queryParameters;
    final existingSortBy = queryParameters[CommonQueryParameters.sortBy];
    final existingDirection =
        queryParameters[CommonQueryParameters.sortDirection];

    final newSortBy = columnData.queryParam.name;
    final isSameSortBy = existingSortBy == newSortBy;
    final wasAscending = existingDirection == SortDirection.asc.name;
    final newDirection = isSameSortBy && wasAscending
        ? SortDirection.desc.name
        : SortDirection.asc.name;

    final newQueryParameters = {
      ...queryParameters,
      CommonQueryParameters.sortBy: newSortBy,
      CommonQueryParameters.sortDirection: newDirection,
    };

    context.go(pageUri.replace(queryParameters: newQueryParameters).toString());
  }
}
