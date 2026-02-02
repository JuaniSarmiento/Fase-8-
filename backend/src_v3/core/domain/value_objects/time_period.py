"""
Time Period Value Object
"""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TimePeriod:
    """
    Time Period value object.
    
    Represents a period of time with start and end dates.
    """
    start: datetime
    end: datetime
    
    def __post_init__(self):
        """Validate time period."""
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        delta = self.end - self.start
        return int(delta.total_seconds() / 60)
    
    @property
    def duration_hours(self) -> float:
        """Get duration in hours."""
        return self.duration_minutes / 60
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within period."""
        return self.start <= timestamp <= self.end
    
    def overlaps(self, other: "TimePeriod") -> bool:
        """Check if this period overlaps with another."""
        return (self.start <= other.end) and (other.start <= self.end)
    
    @classmethod
    def from_now(cls, minutes: int) -> "TimePeriod":
        """Create a period starting now with given duration."""
        start = datetime.utcnow()
        end = start + timedelta(minutes=minutes)
        return cls(start=start, end=end)
    
    def __str__(self) -> str:
        return f"{self.start.isoformat()} to {self.end.isoformat()}"
