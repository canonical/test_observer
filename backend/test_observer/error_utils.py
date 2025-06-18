# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Utility functions for consistent error handling across controllers"""

from typing import Any, Dict, Optional

from fastapi import status

from test_observer.error_handling import BusinessLogicError, ValidationError, DatabaseError


def not_found_error(resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None) -> BusinessLogicError:
    """Create a standardized not found error"""
    message = f"{resource} not found"
    error_details = {"resource": resource, "identifier": str(identifier)}
    if details:
        error_details.update(details)
    
    return BusinessLogicError(
        message=message,
        error_type="not_found",
        details=error_details,
        status_code=status.HTTP_404_NOT_FOUND
    )


def already_exists_error(resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None) -> BusinessLogicError:
    """Create a standardized already exists error"""
    message = f"{resource} already exists"
    error_details = {"resource": resource, "identifier": str(identifier)}
    if details:
        error_details.update(details)
    
    return BusinessLogicError(
        message=message,
        error_type="already_exists",
        details=error_details,
        status_code=status.HTTP_409_CONFLICT
    )


def invalid_operation_error(operation: str, reason: str, details: Optional[Dict[str, Any]] = None) -> BusinessLogicError:
    """Create a standardized invalid operation error"""
    message = f"Cannot {operation}: {reason}"
    error_details = {"operation": operation, "reason": reason}
    if details:
        error_details.update(details)
    
    return BusinessLogicError(
        message=message,
        error_type="invalid_operation",
        details=error_details,
        status_code=status.HTTP_400_BAD_REQUEST
    )


def permission_denied_error(resource: str, action: str, details: Optional[Dict[str, Any]] = None) -> BusinessLogicError:
    """Create a standardized permission denied error"""
    message = f"Permission denied to {action} {resource}"
    error_details = {"resource": resource, "action": action}
    if details:
        error_details.update(details)
    
    return BusinessLogicError(
        message=message,
        error_type="permission_denied",
        details=error_details,
        status_code=status.HTTP_403_FORBIDDEN
    )


def invalid_input_error(field: str, value: Any, reason: str, details: Optional[Dict[str, Any]] = None) -> ValidationError:
    """Create a standardized invalid input error"""
    message = f"Invalid {field}: {reason}"
    error_details = {"field": field, "value": str(value), "reason": reason}
    if details:
        error_details.update(details)
    
    return ValidationError(
        message=message,
        field=field,
        value=value,
        details=error_details
    )


def missing_required_field_error(field: str, context: str = "", details: Optional[Dict[str, Any]] = None) -> ValidationError:
    """Create a standardized missing required field error"""
    message = f"Required field '{field}' is missing"
    if context:
        message += f" for {context}"
    
    error_details = {"field": field}
    if context:
        error_details["context"] = context
    if details:
        error_details.update(details)
    
    return ValidationError(
        message=message,
        field=field,
        details=error_details
    )


def database_operation_error(operation: str, reason: str, details: Optional[Dict[str, Any]] = None) -> DatabaseError:
    """Create a standardized database operation error"""
    message = f"Database {operation} failed: {reason}"
    error_details = {"operation": operation, "reason": reason}
    if details:
        error_details.update(details)
    
    return DatabaseError(
        message=message,
        operation=operation,
        details=error_details
    )


def artefact_status_error(current_status: str, requested_status: str, reason: str) -> BusinessLogicError:
    """Create a standardized artefact status transition error"""
    message = f"Cannot change artefact status from {current_status} to {requested_status}: {reason}"
    
    return BusinessLogicError(
        message=message,
        error_type="invalid_status_transition",
        details={
            "current_status": current_status,
            "requested_status": requested_status,
            "reason": reason
        },
        status_code=status.HTTP_400_BAD_REQUEST
    )


def environment_review_error(action: str, reason: str, details: Optional[Dict[str, Any]] = None) -> BusinessLogicError:
    """Create a standardized environment review error"""
    message = f"Cannot {action} environment review: {reason}"
    error_details = {"action": action, "reason": reason}
    if details:
        error_details.update(details)
    
    return BusinessLogicError(
        message=message,
        error_type="environment_review_error",
        details=error_details,
        status_code=status.HTTP_400_BAD_REQUEST
    )


def test_execution_error(action: str, reason: str, details: Optional[Dict[str, Any]] = None) -> BusinessLogicError:
    """Create a standardized test execution error"""
    message = f"Cannot {action} test execution: {reason}"
    error_details = {"action": action, "reason": reason}
    if details:
        error_details.update(details)
    
    return BusinessLogicError(
        message=message,
        error_type="test_execution_error",
        details=error_details,
        status_code=status.HTTP_400_BAD_REQUEST
    )