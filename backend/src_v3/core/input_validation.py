"""Input Validation and Sanitization Utilities.

Prevents:
- SQL Injection
- XSS attacks
- Path traversal
- Command injection
"""
from __future__ import annotations

import re
import html
from typing import Any, Optional
from pathlib import Path


class InputValidator:
    """Validate and sanitize user inputs."""
    
    # Allowed characters for different input types
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    UUID_PATTERN = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
    ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")
    
    # Dangerous patterns
    PATH_TRAVERSAL_PATTERN = re.compile(r"\.\.|/\.\./|\\\.\.\\")
    COMMAND_INJECTION_PATTERN = re.compile(r"[;&|`$(){}[\]<>]")
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input (remove HTML, limit length)."""
        if not isinstance(text, str):
            return ""
        
        # Truncate
        text = text[:max_length]
        
        # Escape HTML
        text = html.escape(text)
        
        # Remove null bytes
        text = text.replace("\x00", "")
        
        return text.strip()
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format."""
        return bool(InputValidator.USERNAME_PATTERN.match(username))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format."""
        return bool(InputValidator.UUID_PATTERN.match(uuid_str.lower()))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename (no path traversal)."""
        if not filename or len(filename) > 255:
            return False
        
        # Check for path traversal
        if InputValidator.PATH_TRAVERSAL_PATTERN.search(filename):
            return False
        
        # Check for dangerous characters
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\x00"]
        if any(char in filename for char in dangerous_chars):
            return False
        
        return True
    
    @staticmethod
    def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> bool:
        """Validate integer value."""
        try:
            int_value = int(value)
            
            if min_value is not None and int_value < min_value:
                return False
            
            if max_value is not None and int_value > max_value:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_filepath(filepath: str, allowed_dir: str) -> Optional[Path]:
        """Sanitize filepath and ensure it's within allowed directory."""
        try:
            # Resolve absolute path
            allowed_path = Path(allowed_dir).resolve()
            requested_path = (allowed_path / filepath).resolve()
            
            # Check if path is within allowed directory
            if not str(requested_path).startswith(str(allowed_path)):
                return None
            
            return requested_path
        except Exception:
            return None
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validate password strength.
        
        Returns:
            (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password is too long (max 128 characters)"
        
        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for at least one lowercase letter
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for at least one digit
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        
        # Special character requirement removed for better user experience
        # Users can now register with passwords that only have:
        # - At least 8 characters
        # - One uppercase letter
        # - One lowercase letter
        # - One digit
        
        return True, ""
    
    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """Sanitize SQL identifier (table/column name)."""
        # Only allow alphanumeric and underscore
        return "".join(c for c in identifier if c.isalnum() or c == "_")
    
    @staticmethod
    def validate_json_size(json_str: str, max_size_kb: int = 100) -> bool:
        """Validate JSON size to prevent DoS."""
        max_bytes = max_size_kb * 1024
        return len(json_str.encode("utf-8")) <= max_bytes


class CodeSanitizer:
    """Sanitize code submissions for security."""
    
    # Dangerous Python patterns
    DANGEROUS_PATTERNS = [
        r"__import__",
        r"exec\s*\(",
        r"eval\s*\(",
        r"compile\s*\(",
        r"open\s*\(",
        r"file\s*\(",
        r"input\s*\(",
        r"raw_input\s*\(",
        r"os\.",
        r"sys\.",
        r"subprocess\.",
        r"socket\.",
        r"urllib\.",
        r"requests\.",
        r"pickle\.",
        r"shelve\.",
        r"globals\s*\(",
        r"locals\s*\(",
        r"vars\s*\(",
        r"dir\s*\(",
        r"__builtins__",
    ]
    
    def __init__(self):
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
    
    def has_dangerous_code(self, code: str) -> tuple[bool, Optional[str]]:
        """Check if code contains dangerous patterns.
        
        Returns:
            (has_dangerous, pattern_name)
        """
        for pattern in self.patterns:
            match = pattern.search(code)
            if match:
                return True, match.group(0)
        
        return False, None
    
    def sanitize_code_output(self, output: str, max_length: int = 10000) -> str:
        """Sanitize code execution output."""
        # Truncate
        if len(output) > max_length:
            output = output[:max_length] + "\n... (output truncated)"
        
        # Escape HTML
        output = html.escape(output)
        
        return output
