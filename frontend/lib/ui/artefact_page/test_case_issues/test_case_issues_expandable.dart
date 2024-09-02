import 'package:flutter/material.dart';

import '../../expandable.dart';

class TestCaseIssuesExpandable extends StatelessWidget {
  const TestCaseIssuesExpandable({super.key});

  @override
  Widget build(BuildContext context) {
    return const Expandable(title: Text('Reported Issues'), children: []);
  }
}
