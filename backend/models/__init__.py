"""
Database models for STRATUS Bug Advisor
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class QueryLog:
    """Query log model"""
    id: Optional[int] = None
    product: str = ""
    query_text: str = ""
    query_length: int = 0
    response_time_ms: int = 0
    success: bool = False
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    query_hash: Optional[str] = None

@dataclass
class Feedback:
    """Feedback model"""
    id: Optional[int] = None
    query_id: Optional[int] = None
    query_hash: Optional[str] = None
    helpful: bool = False
    feedback_text: Optional[str] = None
    timestamp: Optional[datetime] = None
    ip_address: Optional[str] = None

@dataclass
class ApiConfig:
    """API configuration model"""
    id: Optional[int] = None
    config_key: str = ""
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_encrypted: bool = False
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

@dataclass
class UsageStats:
    """Usage statistics model"""
    date: str = ""
    total_queries: int = 0
    successful_queries: int = 0
    avg_response_time: float = 0.0
    success_rate: float = 0.0
    top_products: Optional[str] = None  # JSON string
    unique_users: int = 0
    total_errors: int = 0

@dataclass
class AdminUser:
    """Admin user model"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    email: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None

@dataclass
class ResponseCache:
    """Response cache model"""
    id: Optional[int] = None
    query_hash: str = ""
    product: str = ""
    response_text: str = ""
    confidence: float = 0.0
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    hit_count: int = 0

@dataclass
class SystemLog:
    """System log model"""
    id: Optional[int] = None
    level: str = ""
    message: str = ""
    module: Optional[str] = None
    function_name: Optional[str] = None
    line_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    additional_data: Optional[str] = None  # JSON string
