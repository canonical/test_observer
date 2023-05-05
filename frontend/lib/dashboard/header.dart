import 'package:flutter/material.dart';

import '../spacing.dart';

class Header extends StatelessWidget {
  const Header({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
      child: Text('Header'),
    );
  }
}
