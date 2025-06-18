import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'error_display.dart';

class ErrorDemoPage extends StatelessWidget {
  const ErrorDemoPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Error Handling Demo'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Error Handling Examples',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            
            // Structured error example
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Structured Backend Error',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text('Demonstrates how structured errors from the backend are displayed.'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => _showStructuredError(context),
                      child: const Text('Show Structured Error Dialog'),
                    ),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: () => _showStructuredErrorSnackbar(context),
                      child: const Text('Show Structured Error Snackbar'),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Network error example
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Network Error',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text('Demonstrates how network errors are handled.'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => _showNetworkError(context),
                      child: const Text('Show Network Error Dialog'),
                    ),
                    const SizedBox(height: 8),
                    ElevatedButton(
                      onPressed: () => _showNetworkErrorSnackbar(context),
                      child: const Text('Show Network Error Snackbar'),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Legacy error example
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Legacy Error Format',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    const Text('Demonstrates how legacy error formats are handled.'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => _showLegacyError(context),
                      child: const Text('Show Legacy Error Dialog'),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showStructuredError(BuildContext context) {
    // Simulate a structured error response from the new backend system
    final errorData = {
      'error': {
        'type': 'not_found',
        'message': 'Artefact not found',
        'code': 'E7B2A1C9',
        'details': {
          'resource': 'Artefact',
          'identifier': '999999',
          'timestamp': DateTime.now().toIso8601String(),
          'request_path': '/v1/artefacts/999999',
          'user_agent': 'Test Observer Frontend/1.0',
        }
      },
      'debug_info': {
        'exception_type': 'BusinessLogicError',
        'exception_message': 'Artefact with id 999999 not found',
        'request_id': 'req_${DateTime.now().millisecondsSinceEpoch}',
        'traceback': [
          'Traceback (most recent call last):',
          '  File "/app/test_observer/controllers/artefacts/artefact_retriever.py", line 36, in __call__',
          '    artefact = db.scalar(select(Artefact).where(Artefact.id == artefact_id))',
          '  File "/app/test_observer/controllers/artefacts/artefact_retriever.py", line 39, in __call__',
          '    raise not_found_error("Artefact", artefact_id)',
          '  File "/app/test_observer/error_utils.py", line 23, in not_found_error',
          '    return BusinessLogicError(',
          'test_observer.error_handling.BusinessLogicError: Artefact not found',
        ]
      }
    };

    showErrorDialog(
      context,
      errorData,
      title: 'Artefact Lookup Failed',
      onRetry: () => _simulateRetry(context),
    );
  }

  void _showStructuredErrorSnackbar(BuildContext context) {
    final errorData = {
      'error': {
        'type': 'validation_error',
        'message': 'Invalid stage for artefact family',
        'code': 'V4E8B2F1',
        'details': {
          'field': 'stage',
          'value': 'candidate',
          'artefact_family': 'deb',
          'available_stages': 'varies by family',
          'valid_stages_for_deb': 'proposed, updates, security'
        }
      },
      'debug_info': {
        'exception_type': 'ValidationError',
        'exception_message': 'Invalid stage for artefact family deb',
        'request_id': 'req_${DateTime.now().millisecondsSinceEpoch}',
        'traceback': [
          'Traceback (most recent call last):',
          '  File "/app/test_observer/controllers/artefacts/artefacts.py", line 154, in _validate_artefact_stage',
          '    DebStage(stage)',
          '  File "/app/test_observer/data_access/models.py", line 89, in __init__',
          '    raise ValueError(f"Invalid stage: {stage}")',
          'ValueError: Invalid stage: candidate',
        ]
      }
    };

    showErrorSnackbar(
      context,
      errorData,
      onRetry: () => _simulateRetry(context),
    );
  }

  void _showNetworkError(BuildContext context) {
    // Simulate a Dio network error
    final dioError = DioException(
      requestOptions: RequestOptions(path: '/v1/artefacts/123'),
      type: DioExceptionType.connectionTimeout,
      message: 'Connection timeout',
    );

    showErrorDialog(
      context,
      dioError,
      title: 'Connection Failed',
      onRetry: () => _simulateRetry(context),
    );
  }

  void _showNetworkErrorSnackbar(BuildContext context) {
    final dioError = DioException(
      requestOptions: RequestOptions(path: '/v1/test-executions'),
      type: DioExceptionType.connectionError,
      message: 'Failed to connect to server',
    );

    showErrorSnackbar(
      context,
      dioError,
      onRetry: () => _simulateRetry(context),
    );
  }

  void _showLegacyError(BuildContext context) {
    // Simulate a legacy error format (still used by some endpoints)
    final legacyError = DioException(
      requestOptions: RequestOptions(path: '/v1/legacy-endpoint'),
      type: DioExceptionType.badResponse,
      response: Response(
        requestOptions: RequestOptions(path: '/v1/legacy-endpoint'),
        statusCode: 404,
        data: {'detail': 'Resource not found in legacy system'},
      ),
    );

    showErrorDialog(
      context,
      legacyError,
      title: 'Legacy System Error',
      onRetry: () => _simulateRetry(context),
    );
  }

  void _simulateRetry(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Retry simulation triggered'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}