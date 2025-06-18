# Enhanced Error Handling System

This document describes the enhanced error handling system implemented for Test Observer.

## Overview

The new error handling system provides a consistent, user-friendly way to present errors from both backend and frontend operations, with support for detailed debugging information and stack traces.

## Features

### Backend Error Handling

- **Structured Error Responses**: Consistent JSON format with error codes, types, and details
- **Debug Information**: Optional stack traces and debug data for development
- **Error Tracking**: Unique error codes for incident tracking
- **Custom Exception Types**: Business logic, validation, and database error types

### Frontend Error Presentation

- **Rich Error Dialogs**: App-styled dialogs with collapsible sections
- **Stack Trace Display**: Formatted stack traces with copy functionality
- **Copy to Clipboard**: Easy copying of error details, stack traces, and error codes
- **Error Snackbars**: Less intrusive notifications for minor errors
- **Legacy Support**: Handles both new structured and old error formats

## Error Dialog Structure

The enhanced error dialog includes:

1. **Header Section**:
   - Error type icon with appropriate color coding
   - Error title styled like app headings
   - Error code with copy button
   - Professional layout matching app design

2. **Content Sections**:
   - Error message in clear, readable format
   - Collapsible "Details" section with structured error information
   - Collapsible "Stack Trace" section with formatted traceback
   - Copy buttons for each section

3. **Actions**:
   - Close button
   - Optional Retry button for retryable operations

## Usage Examples

### Show Enhanced Error Dialog

```dart
showErrorDialog(
  context,
  error, // Can be DioException, Map, or any error object
  title: 'Custom Error Title',
  onRetry: () => performRetryAction(),
);
```

### Show Error Snackbar

```dart
showErrorSnackbar(
  context,
  error,
  onRetry: () => performRetryAction(),
  duration: Duration(seconds: 5),
);
```

### In Widget Error Handling

```dart
// In AsyncValue.when() error handler
error: (error, stack) => Center(
  child: Column(
    mainAxisAlignment: MainAxisAlignment.center,
    children: [
      const Icon(Icons.error_outline, size: 48, color: Colors.red),
      const SizedBox(height: 16),
      const Text('Failed to load data'),
      const SizedBox(height: 8),
      ElevatedButton.icon(
        onPressed: () => showErrorDialog(
          context,
          error,
          title: 'Data Loading Error',
          onRetry: () => ref.invalidate(dataProvider),
        ),
        icon: const Icon(Icons.info),
        label: const Text('View Details'),
      ),
    ],
  ),
),
```

## Error Types and Visual Indicators

Different error types are automatically styled with appropriate colors and icons:

- **Not Found** (404): Orange warning icon
- **Unauthorized/Forbidden** (401/403): Red lock icon
- **Validation Error** (422): Amber warning icon
- **Network Errors**: Blue connectivity icon
- **Server Errors** (500): Red error icon
- **General Errors**: Grey outline icon

## Backend Integration

The system automatically detects and handles:

1. **New Structured Errors**: From the enhanced backend error handling system
2. **Legacy Errors**: Old `{"detail": "message"}` format
3. **Network Errors**: Dio connection, timeout, and HTTP errors

## Demo Page

A demo page (`error_demo_page.dart`) is available to showcase different error types and their presentation. This includes examples of:

- Structured backend errors with stack traces
- Network connection errors
- Legacy error format handling
- Different error severity levels

## Development Benefits

- **Consistent UX**: All errors follow the same visual patterns
- **Better Debugging**: Stack traces and error codes for troubleshooting
- **User-Friendly**: Non-technical users see clear messages, developers can access details
- **Copy Functionality**: Easy sharing of error information for support
- **Professional Appearance**: Error dialogs match app design standards

The enhanced error handling system significantly improves both user experience and developer debugging capabilities while maintaining a professional, consistent appearance throughout the application.