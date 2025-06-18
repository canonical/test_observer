import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:dio/dio.dart';

class ErrorDetail {
  final String type;
  final String message;
  final String code;
  final Map<String, dynamic>? details;

  ErrorDetail({
    required this.type,
    required this.message,
    required this.code,
    this.details,
  });

  factory ErrorDetail.fromJson(Map<String, dynamic> json) {
    return ErrorDetail(
      type: json['type'] ?? 'unknown_error',
      message: json['message'] ?? 'An error occurred',
      code: json['code'] ?? 'N/A',
      details: json['details'],
    );
  }
}

class ErrorResponse {
  final ErrorDetail error;
  final Map<String, dynamic>? debugInfo;

  ErrorResponse({
    required this.error,
    this.debugInfo,
  });

  factory ErrorResponse.fromJson(Map<String, dynamic> json) {
    return ErrorResponse(
      error: ErrorDetail.fromJson(json['error'] ?? {}),
      debugInfo: json['debug_info'],
    );
  }

  factory ErrorResponse.fromDioError(DioException dioError) {
    // Handle different types of Dio errors
    if (dioError.response?.data is Map<String, dynamic>) {
      final responseData = dioError.response!.data as Map<String, dynamic>;
      
      // Check if it's our new structured error format
      if (responseData.containsKey('error')) {
        return ErrorResponse.fromJson(responseData);
      }
      
      // Handle legacy error format
      if (responseData.containsKey('detail')) {
        return ErrorResponse(
          error: ErrorDetail(
            type: _getErrorTypeFromStatusCode(dioError.response?.statusCode),
            message: responseData['detail'].toString(),
            code: 'LEGACY',
          ),
        );
      }
    }
    
    // Handle network and other errors
    return ErrorResponse(
      error: ErrorDetail(
        type: _getDioErrorType(dioError),
        message: _getDioErrorMessage(dioError),
        code: 'CLIENT',
      ),
    );
  }

  static String _getErrorTypeFromStatusCode(int? statusCode) {
    switch (statusCode) {
      case 400:
        return 'bad_request';
      case 401:
        return 'unauthorized';
      case 403:
        return 'forbidden';
      case 404:
        return 'not_found';
      case 409:
        return 'conflict';
      case 422:
        return 'validation_error';
      case 500:
        return 'internal_error';
      default:
        return 'http_error';
    }
  }

  static String _getDioErrorType(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'timeout_error';
      case DioExceptionType.connectionError:
        return 'connection_error';
      case DioExceptionType.badResponse:
        return 'server_error';
      case DioExceptionType.cancel:
        return 'request_cancelled';
      default:
        return 'network_error';
    }
  }

  static String _getDioErrorMessage(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
        return 'Connection timeout. Please check your internet connection.';
      case DioExceptionType.sendTimeout:
        return 'Request timeout. Please try again.';
      case DioExceptionType.receiveTimeout:
        return 'Server response timeout. Please try again.';
      case DioExceptionType.connectionError:
        return 'Unable to connect to server. Please check your internet connection.';
      case DioExceptionType.badResponse:
        return 'Server returned an error (${error.response?.statusCode}).';
      case DioExceptionType.cancel:
        return 'Request was cancelled.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }
}

class ErrorDialog extends StatefulWidget {
  final ErrorResponse errorResponse;
  final String? title;
  final VoidCallback? onRetry;

  const ErrorDialog({
    super.key,
    required this.errorResponse,
    this.title,
    this.onRetry,
  });

  @override
  State<ErrorDialog> createState() => _ErrorDialogState();
}

class _ErrorDialogState extends State<ErrorDialog> {
  bool _showDetails = false;
  bool _showStackTrace = false;

  @override
  Widget build(BuildContext context) {
    final error = widget.errorResponse.error;
    
    return Dialog(
      child: Container(
        width: MediaQuery.of(context).size.width * 0.8,
        constraints: BoxConstraints(
          maxWidth: 600,
          maxHeight: MediaQuery.of(context).size.height * 0.8,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header with app-style design
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: _getErrorColor(error.type).withValues(alpha: 0.1),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                border: Border(
                  bottom: BorderSide(
                    color: _getErrorColor(error.type).withValues(alpha: 0.2),
                    width: 1,
                  ),
                ),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: _getErrorColor(error.type).withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      _getErrorIcon(error.type),
                      color: _getErrorColor(error.type),
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.title ?? _getErrorTitle(error.type),
                          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: _getErrorColor(error.type),
                          ),
                        ),
                        if (error.code != 'N/A') ...[
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  'Code: ${error.code}',
                                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                    fontFamily: 'monospace',
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              IconButton(
                                onPressed: () => _copyToClipboard(error.code),
                                icon: const Icon(Icons.copy, size: 16),
                                tooltip: 'Copy error code',
                                style: IconButton.styleFrom(
                                  minimumSize: const Size(24, 24),
                                  padding: const EdgeInsets.all(4),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            // Content
            Flexible(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Error message
                    Text(
                      error.message,
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    
                    const SizedBox(height: 24),
                    
                    // Details section
                    if (error.details != null || widget.errorResponse.debugInfo != null) ...[
                      _buildSectionHeader(
                        'Details',
                        _showDetails,
                        () => setState(() => _showDetails = !_showDetails),
                      ),
                      if (_showDetails) ...[
                        const SizedBox(height: 12),
                        _buildDetailsSection(),
                        const SizedBox(height: 16),
                      ],
                    ],
                    
                    // Stack trace section
                    if (_hasStackTrace()) ...[
                      _buildSectionHeader(
                        'Stack Trace',
                        _showStackTrace,
                        () => setState(() => _showStackTrace = !_showStackTrace),
                      ),
                      if (_showStackTrace) ...[
                        const SizedBox(height: 12),
                        _buildStackTraceSection(),
                      ],
                    ],
                  ],
                ),
              ),
            ),
            
            // Actions
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
                borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
                border: Border(
                  top: BorderSide(
                    color: Theme.of(context).dividerColor,
                    width: 1,
                  ),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Text('Close'),
                  ),
                  if (widget.onRetry != null) ...[
                    const SizedBox(width: 12),
                    ElevatedButton.icon(
                      onPressed: () {
                        Navigator.of(context).pop();
                        widget.onRetry!();
                      },
                      icon: const Icon(Icons.refresh, size: 18),
                      label: const Text('Retry'),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, bool isExpanded, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        child: Row(
          children: [
            Icon(
              isExpanded ? Icons.expand_less : Icons.expand_more,
              size: 20,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(width: 8),
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailsSection() {
    final error = widget.errorResponse.error;
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (error.details != null) ...[
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Error Details',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => _copyToClipboard(_formatDetailsForCopy(error.details!)),
                  icon: const Icon(Icons.copy, size: 18),
                  tooltip: 'Copy details',
                  style: IconButton.styleFrom(
                    minimumSize: const Size(32, 32),
                    padding: const EdgeInsets.all(4),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...error.details!.entries.map((entry) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 120,
                    child: Text(
                      '${entry.key}:',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.w500,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      entry.value.toString(),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontFamily: 'monospace',
                      ),
                    ),
                  ),
                ],
              ),
            )),
          ],
          if (widget.errorResponse.debugInfo != null) ...[
            if (error.details != null) ...[
              const SizedBox(height: 16),
              Divider(color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.2)),
              const SizedBox(height: 16),
            ],
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Debug Information',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () => _copyToClipboard(_formatDetailsForCopy(widget.errorResponse.debugInfo!)),
                  icon: const Icon(Icons.copy, size: 18),
                  tooltip: 'Copy debug info',
                  style: IconButton.styleFrom(
                    minimumSize: const Size(32, 32),
                    padding: const EdgeInsets.all(4),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...widget.errorResponse.debugInfo!.entries.where((entry) => entry.key != 'traceback').map((entry) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 120,
                    child: Text(
                      '${entry.key}:',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.w500,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(
                      entry.value.toString(),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontFamily: 'monospace',
                      ),
                    ),
                  ),
                ],
              ),
            )),
          ],
        ],
      ),
    );
  }

  Widget _buildStackTraceSection() {
    final stackTraceLines = _getStackTraceLines();
    if (stackTraceLines.isEmpty) return const SizedBox.shrink();
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'Stack Trace',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              IconButton(
                onPressed: () => _copyToClipboard(stackTraceLines.join('\n')),
                icon: const Icon(Icons.copy, size: 18),
                tooltip: 'Copy stack trace',
                style: IconButton.styleFrom(
                  minimumSize: const Size(32, 32),
                  padding: const EdgeInsets.all(4),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(
                color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: stackTraceLines.map((line) => Padding(
                padding: const EdgeInsets.only(bottom: 2),
                child: Text(
                  line,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              )).toList(),
            ),
          ),
        ],
      ),
    );
  }

  bool _hasStackTrace() {
    return _getStackTraceLines().isNotEmpty;
  }

  List<String> _getStackTraceLines() {
    final List<String> lines = [];
    
    // From debug info traceback
    if (widget.errorResponse.debugInfo != null) {
      final traceback = widget.errorResponse.debugInfo!['traceback'];
      if (traceback is List) {
        lines.addAll(traceback.map((line) => line.toString()));
      }
    }
    
    // Add any additional stack trace sources here
    // For example, from Dart stack traces
    
    return lines.where((line) => line.trim().isNotEmpty).toList();
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Copied to clipboard'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  String _formatDetailsForCopy(Map<String, dynamic> details) {
    return details.entries
        .map((entry) => '${entry.key}: ${entry.value}')
        .join('\n');
  }

  IconData _getErrorIcon(String errorType) {
    switch (errorType) {
      case 'not_found':
        return Icons.search_off;
      case 'unauthorized':
      case 'forbidden':
        return Icons.lock;
      case 'validation_error':
      case 'bad_request':
        return Icons.warning;
      case 'timeout_error':
        return Icons.timer_off;
      case 'connection_error':
      case 'network_error':
        return Icons.wifi_off;
      case 'server_error':
      case 'internal_error':
        return Icons.error;
      default:
        return Icons.error_outline;
    }
  }

  Color _getErrorColor(String errorType) {
    switch (errorType) {
      case 'not_found':
        return Colors.orange;
      case 'unauthorized':
      case 'forbidden':
        return Colors.red;
      case 'validation_error':
      case 'bad_request':
        return Colors.amber;
      case 'timeout_error':
      case 'connection_error':
      case 'network_error':
        return Colors.blue;
      case 'server_error':
      case 'internal_error':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _getErrorTitle(String errorType) {
    switch (errorType) {
      case 'not_found':
        return 'Not Found';
      case 'unauthorized':
        return 'Unauthorized';
      case 'forbidden':
        return 'Access Denied';
      case 'validation_error':
        return 'Validation Error';
      case 'bad_request':
        return 'Invalid Request';
      case 'timeout_error':
        return 'Request Timeout';
      case 'connection_error':
      case 'network_error':
        return 'Connection Error';
      case 'server_error':
      case 'internal_error':
        return 'Server Error';
      default:
        return 'Error';
    }
  }
}

class ErrorSnackbar {
  static void show(
    BuildContext context,
    ErrorResponse errorResponse, {
    VoidCallback? onRetry,
    Duration duration = const Duration(seconds: 4),
  }) {
    final error = errorResponse.error;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              _getErrorIcon(error.type),
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _getErrorTitle(error.type),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  Text(
                    error.message,
                    style: const TextStyle(color: Colors.white),
                  ),
                ],
              ),
            ),
          ],
        ),
        backgroundColor: _getErrorColor(error.type),
        duration: duration,
        action: onRetry != null
            ? SnackBarAction(
                label: 'Retry',
                textColor: Colors.white,
                onPressed: onRetry,
              )
            : SnackBarAction(
                label: 'Details',
                textColor: Colors.white,
                onPressed: () {
                  showDialog(
                    context: context,
                    builder: (context) => ErrorDialog(
                      errorResponse: errorResponse,
                      onRetry: onRetry,
                    ),
                  );
                },
              ),
      ),
    );
  }

  static IconData _getErrorIcon(String errorType) {
    switch (errorType) {
      case 'not_found':
        return Icons.search_off;
      case 'unauthorized':
      case 'forbidden':
        return Icons.lock;
      case 'validation_error':
      case 'bad_request':
        return Icons.warning;
      case 'timeout_error':
        return Icons.timer_off;
      case 'connection_error':
      case 'network_error':
        return Icons.wifi_off;
      case 'server_error':
      case 'internal_error':
        return Icons.error;
      default:
        return Icons.error_outline;
    }
  }

  static Color _getErrorColor(String errorType) {
    switch (errorType) {
      case 'not_found':
        return Colors.orange;
      case 'unauthorized':
      case 'forbidden':
        return Colors.red;
      case 'validation_error':
      case 'bad_request':
        return Colors.amber;
      case 'timeout_error':
      case 'connection_error':
      case 'network_error':
        return Colors.blue;
      case 'server_error':
      case 'internal_error':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  static String _getErrorTitle(String errorType) {
    switch (errorType) {
      case 'not_found':
        return 'Not Found';
      case 'unauthorized':
        return 'Unauthorized';
      case 'forbidden':
        return 'Access Denied';
      case 'validation_error':
        return 'Validation Error';
      case 'bad_request':
        return 'Invalid Request';
      case 'timeout_error':
        return 'Request Timeout';
      case 'connection_error':
      case 'network_error':
        return 'Connection Error';
      case 'server_error':
      case 'internal_error':
        return 'Server Error';
      default:
        return 'Error';
    }
  }
}

// Helper function to easily show errors
void showErrorDialog(
  BuildContext context,
  dynamic error, {
  String? title,
  VoidCallback? onRetry,
}) {
  ErrorResponse errorResponse;
  
  if (error is DioException) {
    errorResponse = ErrorResponse.fromDioError(error);
  } else if (error is Map<String, dynamic>) {
    errorResponse = ErrorResponse.fromJson(error);
  } else {
    errorResponse = ErrorResponse(
      error: ErrorDetail(
        type: 'unknown_error',
        message: error.toString(),
        code: 'CLIENT',
      ),
    );
  }
  
  showDialog(
    context: context,
    builder: (context) => ErrorDialog(
      errorResponse: errorResponse,
      title: title,
      onRetry: onRetry,
    ),
  );
}

void showErrorSnackbar(
  BuildContext context,
  dynamic error, {
  VoidCallback? onRetry,
  Duration duration = const Duration(seconds: 4),
}) {
  ErrorResponse errorResponse;
  
  if (error is DioException) {
    errorResponse = ErrorResponse.fromDioError(error);
  } else if (error is Map<String, dynamic>) {
    errorResponse = ErrorResponse.fromJson(error);
  } else {
    errorResponse = ErrorResponse(
      error: ErrorDetail(
        type: 'unknown_error',
        message: error.toString(),
        code: 'CLIENT',
      ),
    );
  }
  
  ErrorSnackbar.show(
    context,
    errorResponse,
    onRetry: onRetry,
    duration: duration,
  );
}