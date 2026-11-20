// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the License along with this program.
// If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dio/dio.dart';
import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/family.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/families.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../utilities.dart';

void main() {
  test('API repository reads family names from the backend', () async {
    final dio = DioMock();
    when(() => dio.get('/v1/families')).thenAnswer(
      (_) async => Response(
        requestOptions: RequestOptions(path: '/v1/families'),
        data: [
          {'name': 'snap'},
          {'name': 'solution'},
        ],
      ),
    );

    final families = await ApiRepository(dio: dio).getFamilies();

    expect(
      families,
      [const Family(name: 'snap'), const Family(name: 'solution')],
    );
    verify(() => dio.get('/v1/families')).called(1);
  });

  test('families provider delegates to the API repository', () async {
    final api = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => api)],
    );

    final families = await container.read(familiesProvider.future);

    expect(families.map((family) => family.name), ['snap', 'solution']);
  });
}

class DioMock extends Mock implements Dio {}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<List<Family>> getFamilies() async => [
        const Family(name: 'snap'),
        const Family(name: 'solution'),
      ];
}
