import 'package:flutter/material.dart';

import '../../models/artefact.dart';
import '../../spacing.dart';

class ArtefactCard extends StatelessWidget {
  const ArtefactCard({Key? key}) : super(key: key);

  static const double width = 320;

  @override
  Widget build(BuildContext context) {
    const artefact = dummyArtefact;

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: Theme.of(context).colorScheme.outline),
        borderRadius: BorderRadius.circular(2.25),
      ),
      child: Container(
        width: width,
        height: 156,
        padding: const EdgeInsets.all(Spacing.level4),
        child: Text(
          artefact.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
      ),
    );
  }
}
