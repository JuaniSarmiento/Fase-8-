"""
Email Value Object
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Email:
    """
    Email value object.
    
    Ensures email validity.
    """
    address: str
    
    # Simple email regex
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __post_init__(self):
        """Validate email address."""
        if not self.address:
            raise ValueError("Email address cannot be empty")
        
        if not self.EMAIL_PATTERN.match(self.address):
            raise ValueError(f"Invalid email address: {self.address}")
    
    @property
    def domain(self) -> str:
        """Get email domain."""
        return self.address.split('@')[1]
    
    @property
    def local_part(self) -> str:
        """Get local part of email."""
        return self.address.split('@')[0]
    
    def __str__(self) -> str:
        return self.address
