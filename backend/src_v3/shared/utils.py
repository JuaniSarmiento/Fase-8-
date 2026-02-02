"""
Utility functions
"""
import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def to_snake_case(text: str) -> str:
    """Convert string to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_camel_case(text: str) -> str:
    """Convert string to camelCase."""
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])
