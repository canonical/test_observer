// Copyright (C) 2023 Canonical Ltd.
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

import 'package:flutter/material.dart';

import '../../providers/artefact.dart';
import '../blocking_provider_preloader.dart';
import '../spacing.dart';
import 'artefact_page_body.dart';
import 'artefact_page_header.dart';
import 'artefact_page_side.dart';

class ArtefactPage extends StatelessWidget {
  const ArtefactPage({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: BlockingProviderPreloader(
        provider: artefactProvider(artefactId),
        builder: (_, artefact) => Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ArtefactPageHeader(artefact: artefact),
            const SizedBox(height: Spacing.level4),
            Expanded(
              child: Row(
                children: [
                  ArtefactPageSide(artefact: artefact),
                  Expanded(child: ArtefactPageBody(artefact: artefact)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
