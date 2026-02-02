"""
Risk Score Value Object
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RiskScore:
    """
    Risk Score value object.
    
    Encapsulates risk calculation logic and validation.
    """
    value: float
    
    def __post_init__(self):
        """Validate risk score."""
        if not isinstance(self.value, (int, float)):
            raise TypeError("Risk score must be numeric")
        
        if not (0 <= self.value <= 100):
            raise ValueError("Risk score must be between 0 and 100")
    
    @classmethod
    def calculate(
        cls,
        ai_dependency: float,
        avg_attempts: float,
        completion_rate: float,
        time_spent_minutes: int
    ) -> "RiskScore":
        """
        Calculate risk score from components.
        
        Formula:
        - AI dependency (40%): Higher AI usage = higher risk
        - Avg attempts (30%): More attempts = potential difficulty
        - Completion rate (20%): Lower completion = higher risk
        - Time spent (10%): Less time = lower engagement
        
        Args:
            ai_dependency: 0-1 float
            avg_attempts: Average attempts per exercise
            completion_rate: 0-1 float
            time_spent_minutes: Total time in minutes
        
        Returns:
            RiskScore instance
        """
        # AI dependency (40%)
        ai_risk = ai_dependency * 100 * 0.4
        
        # Average attempts (30%) - normalized to 1-5 range
        attempt_risk = min((avg_attempts - 1) / 4, 1.0) * 100 * 0.3
        
        # Completion rate (20%) - inverted
        completion_risk = (1 - completion_rate) * 100 * 0.2
        
        # Time spent (10%) - expecting minimum 60 minutes
        time_risk = max(0, (60 - time_spent_minutes) / 60) * 100 * 0.1
        
        total_risk = min(ai_risk + attempt_risk + completion_risk + time_risk, 100)
        
        return cls(value=round(total_risk, 2))
    
    def is_low(self) -> bool:
        """Check if risk is low (0-40)."""
        return self.value <= 40
    
    def is_medium(self) -> bool:
        """Check if risk is medium (41-60)."""
        return 40 < self.value <= 60
    
    def is_high(self) -> bool:
        """Check if risk is high (61-100)."""
        return self.value > 60
    
    def __str__(self) -> str:
        return f"{self.value:.2f}"
    
    def __float__(self) -> float:
        return self.value
