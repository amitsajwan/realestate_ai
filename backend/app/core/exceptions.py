class CRMException(Exception):
    """Base exception for CRM application"""
    def __init__(self, message: str, code: str = "GENERIC_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(CRMException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")

class ValidationError(CRMException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")

class NotFoundError(CRMException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", "NOT_FOUND")

class ConflictError(CRMException):
    def __init__(self, message: str = None, resource: str = None, field: str = None, value: str = None):
        if message:
            error_message = message
        elif resource and field and value:
            error_message = f"{resource} with {field} '{value}' already exists"
        else:
            error_message = "Resource conflict detected"
        super().__init__(error_message, "CONFLICT")

class FacebookError(CRMException):
    def __init__(self, message: str = "Facebook API error"):
        super().__init__(message, "FACEBOOK_ERROR")
