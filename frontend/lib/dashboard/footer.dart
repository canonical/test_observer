import 'package:flutter/material.dart';

import '../spacing.dart';

class Footer extends StatelessWidget {
  const Footer({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const BottomAppBar(
      padding: EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
      child: Text('Footer'),
    );
  }
}
