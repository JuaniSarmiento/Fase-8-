"""
Domain Exceptions - Business Rule Violations
"""


class DomainException(Exception):
    """Base exception for domain layer"""
    pass


class EntityNotFoundException(DomainException):
    """Entity not found in repository"""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id '{entity_id}' not found")


class ValidationException(DomainException):
    """Domain validation failed"""
    pass


class BusinessRuleViolationException(DomainException):
    """Business rule was violated"""
    pass
