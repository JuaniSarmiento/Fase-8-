"""
User SQLAlchemy Model - Persistence Layer Only

Simplified user model focusing on authentication.
Academic context moved to UserProfileModel.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class UserModel(Base):
    """
    User persistence model (ORM).
    
    Maps to 'users' table.
    No business logic - only persistence structure.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(String(36), primary_key=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=True)
    
    # Authorization
    roles = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_users_roles_gin', 'roles', postgresql_using='gin'),
        Index('idx_users_deleted', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<UserModel(id={self.id}, email={self.email}, username={self.username})>"

