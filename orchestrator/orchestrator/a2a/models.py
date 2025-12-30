from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum

class IntentType(str, Enum):
    """Types of user intents"""
    # Email intents
    WRITE_EMAIL = "write_email"
    CLASSIFY_EMAILS = "classify_emails"
    
    # Booking intents
    CREATE_BOOKING = "create_booking"
    LIST_BOOKINGS = "list_bookings"
    CANCEL_BOOKING = "cancel_booking"
    UPDATE_BOOKING = "update_booking"
    CHECK_AVAILABILITY = "check_availability"
    
    # Unknown
    UNKNOWN = "unknown"


class ParsedIntent(BaseModel):
    """Parsed user intent with extracted parameters"""
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    missing_parameters: List[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_message: Optional[str] = None


class WriteEmailParams(BaseModel):
    """Parameters for write_email skill"""
    to: Optional[str] = None
    subject: Optional[str] = None
    text: Optional[str] = None
    tone: str = "professional"
    should_generate: bool = True


class ClassifyEmailsParams(BaseModel):
    """Parameters for classify_emails skill"""
    days_back: int = 7
    categories: Optional[List[str]] = None


class CreateBookingParams(BaseModel):
    """Parameters for create_booking skill"""
    service: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[int] = None  # in minutes
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None


class ListBookingsParams(BaseModel):
    """Parameters for list_bookings skill"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None  # confirmed, pending, cancelled
    customer_email: Optional[str] = None


class CancelBookingParams(BaseModel):
    """Parameters for cancel_booking skill"""
    booking_id: Optional[str] = None
    reason: Optional[str] = None


class UpdateBookingParams(BaseModel):
    """Parameters for update_booking skill"""
    booking_id: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    notes: Optional[str] = None


class CheckAvailabilityParams(BaseModel):
    """Parameters for check_availability skill"""
    service: Optional[str] = None
    date: Optional[str] = None
    duration: Optional[int] = None


class OrchestrationResult(BaseModel):
    """Result of orchestration"""
    success: bool
    message: str
    intent: IntentType
    agent_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConversationState(BaseModel):
    """State of the conversation"""
    user_message: str
    parsed_intent: Optional[ParsedIntent] = None
    awaiting_clarification: bool = False
    clarification_attempts: int = 0
    max_clarification_attempts: int = 3
    result: Optional[OrchestrationResult] = None