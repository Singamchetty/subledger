class DomainError(Exception):
    """Base class for business-rule failures. Mapped to HTTP responses at the edge."""

    status_code = 400
    code = "domain_error"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class BusinessRuleError(DomainError):
    status_code = 422
    code = "business_rule_violation"
