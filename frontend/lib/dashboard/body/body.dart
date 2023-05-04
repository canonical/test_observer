import 'package:flutter/material.dart';

import '../../spacing.dart';
import 'stage_column.dart';

class Body extends StatelessWidget {
  const Body({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, __) => const StageColumn(),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: 2,
    );
  }
}
