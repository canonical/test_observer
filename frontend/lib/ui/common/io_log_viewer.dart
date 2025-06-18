import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class IOLogViewer extends StatefulWidget {
  final List<Map<String, dynamic>> ioLogs;
  final String environmentName;

  const IOLogViewer({
    super.key,
    required this.ioLogs,
    required this.environmentName,
  });

  @override
  State<IOLogViewer> createState() => _IOLogViewerState();
}

class _IOLogViewerState extends State<IOLogViewer> {
  int _selectedLogIndex = 0;

  @override
  Widget build(BuildContext context) {
    if (widget.ioLogs.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(16),
        child: Text(
          'No IO logs available for ${widget.environmentName}',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      );
    }

    final selectedLog = widget.ioLogs[_selectedLogIndex];
    
    return Container(
      constraints: const BoxConstraints(
        maxHeight: 600,
        minHeight: 300,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with log selection
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
              border: Border(
                bottom: BorderSide(
                  color: Theme.of(context).dividerColor,
                ),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'IO Log for ${widget.environmentName}',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    IconButton(
                      onPressed: () => _copyToClipboard(selectedLog['content']),
                      icon: const Icon(Icons.copy, size: 18),
                      tooltip: 'Copy log content',
                      style: IconButton.styleFrom(
                        minimumSize: const Size(32, 32),
                        padding: const EdgeInsets.all(4),
                      ),
                    ),
                  ],
                ),
                if (widget.ioLogs.length > 1) ...[
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Text(
                        'Log entry:',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: DropdownButton<int>(
                          value: _selectedLogIndex,
                          isExpanded: true,
                          items: widget.ioLogs.asMap().entries.map((entry) {
                            final index = entry.key;
                            final log = entry.value;
                            final status = log['status'] as String;
                            
                            return DropdownMenuItem<int>(
                              value: index,
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: status == 'FAILED' 
                                        ? Colors.red.shade100 
                                        : Colors.green.shade100,
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      status,
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: status == 'FAILED' 
                                          ? Colors.red.shade700 
                                          : Colors.green.shade700,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          'Test Execution ${log['test_execution_id']}',
                                          style: Theme.of(context).textTheme.bodySmall,
                                        ),
                                        if (log['environment_name'] != null) ...[
                                          Text(
                                            'Environment: ${log['environment_name']}',
                                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                              fontSize: 10,
                                              color: Theme.of(context).colorScheme.onSurfaceVariant,
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }).toList(),
                          onChanged: (value) {
                            if (value != null) {
                              setState(() {
                                _selectedLogIndex = value;
                              });
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          
          // Log content with optimized rendering
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: const BorderRadius.vertical(bottom: Radius.circular(8)),
                border: Border.all(
                  color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.2),
                ),
              ),
              child: _buildLogContent(selectedLog['content'] as String),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLogContent(String content) {
    // For very large logs, use a more efficient approach
    if (content.length > 100000) { // 100KB threshold
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.yellow.shade100,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: Colors.yellow.shade300),
            ),
            child: Row(
              children: [
                Icon(Icons.warning, size: 16, color: Colors.orange.shade600),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Large log content (${(content.length / 1024).round()}KB). Rendering optimized view.',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.orange.shade700,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: SingleChildScrollView(
              child: Text(
                content,
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onSurface,
                  height: 1.4,
                ),
              ),
            ),
          ),
        ],
      );
    }
    
    // For smaller logs, use SelectableText for better UX
    return SingleChildScrollView(
      child: SelectableText(
        content,
        style: TextStyle(
          fontFamily: 'monospace',
          fontSize: 12,
          color: Theme.of(context).colorScheme.onSurface,
          height: 1.4,
        ),
      ),
    );
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('IO log copied to clipboard'),
        duration: Duration(seconds: 2),
      ),
    );
  }
}

class IOLogDialog extends StatefulWidget {
  final List<Map<String, dynamic>> ioLogs;
  final String environmentName;

  const IOLogDialog({
    super.key,
    required this.ioLogs,
    required this.environmentName,
  });

  @override
  State<IOLogDialog> createState() => _IOLogDialogState();
}

class _IOLogDialogState extends State<IOLogDialog> {
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    // Simulate async loading to allow dialog to show before heavy rendering
    Future.delayed(const Duration(milliseconds: 100), () {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        width: MediaQuery.of(context).size.width * 0.9,
        height: MediaQuery.of(context).size.height * 0.8,
        constraints: const BoxConstraints(
          maxWidth: 1000,
          maxHeight: 800,
        ),
        child: Column(
          children: [
            // Dialog header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                border: Border(
                  bottom: BorderSide(
                    color: Theme.of(context).dividerColor,
                  ),
                ),
              ),
              child: Row(
                children: [
                  const Icon(Icons.terminal, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'IO Log - ${widget.environmentName}',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                    tooltip: 'Close',
                  ),
                ],
              ),
            ),
            
            // Log viewer
            Expanded(
              child: _isLoading 
                ? const Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        CircularProgressIndicator(),
                        SizedBox(height: 16),
                        Text('Loading IO logs...'),
                      ],
                    ),
                  )
                : Padding(
                    padding: const EdgeInsets.all(20),
                    child: IOLogViewer(
                      ioLogs: widget.ioLogs,
                      environmentName: widget.environmentName,
                    ),
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

// Helper function to show IO log dialog with loading state
void showIOLogDialog(
  BuildContext context,
  List<Map<String, dynamic>> ioLogs,
  String environmentName,
) {
  showDialog(
    context: context,
    barrierDismissible: false, // Prevent dismiss during loading
    builder: (context) => IOLogDialog(
      ioLogs: ioLogs,
      environmentName: environmentName,
    ),
  );
}