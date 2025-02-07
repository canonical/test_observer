// Copyright (C) 2023-2025 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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

  const _Row.charm({super.key, required this.artefact})
      : columnsMetaData = _charmColumnsMetadata;

  const _Row.image({super.key, required this.artefact})
      : columnsMetaData = _imageColumnsMetadata;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {
        final currentRoute = GoRouterState.of(context).fullPath;
        context.go('$currentRoute/${artefact.id}');
      },
      child: SizedBox(
        height: 48,
        child: DefaultTextStyle.merge(
          overflow: TextOverflow.ellipsis,
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
      ),
    );
  }
}
