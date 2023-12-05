import 'package:flutter/material.dart';
import 'package:popover/popover.dart';

import '../../models/test_execution.dart';

class TestExecutionReviewButton extends StatelessWidget {
  const TestExecutionReviewButton({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(4),
      child: ElevatedButton(
        onPressed: () {
          showPopover(
            context: context,
            bodyBuilder: (context) => _PopOver(
              testExecution: testExecution,
            ),
            direction: PopoverDirection.bottom,
            width: 500,
            height: 300,
            arrowHeight: 15,
            arrowWidth: 30,
          );
        },
        child: const Text('Review'),
      ),
    );
  }
}

class _PopOver extends StatelessWidget {
  const _PopOver({required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          Text(
            'Select new review status',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          Text(
            'Insert review comments:',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const TextField(
            decoration: InputDecoration(
              border: OutlineInputBorder(),
              hintText: 'Insert review comments',
            ),
          ),
          const ElevatedButton(
            onPressed: null,
            child: Text('Submit Review'),
          ),
        ],
      ),
    );
  }
}
