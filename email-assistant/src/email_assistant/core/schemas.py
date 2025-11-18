from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime


class EmailRequest(BaseModel):
    """Request model for email writing"""
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, description="Email subject")
    text: str = Field(..., min_length=1, description="Email body or instructions")
    tone: Literal["professional", "casual", "formal", "friendly"] = Field(
        default="professional",
        description="Tone of the email"
    )
    should_generate: bool = Field(
        default=False,
        description="Whether to generate draft from instructions or use text as-is"
    )
    cc: Optional[str] = Field(None, description="Carbon copy recipients")
    bcc: Optional[str] = Field(None, description="Blind carbon copy recipients")

class EmailResponse(BaseModel):
    """Response model for email operations"""
    status: Literal["sent_successfully", "draft_generated", "sent_directly", "error"]
    message: str
    generated_body: Optional[str] = None
    error: Optional[str] = None

class EmailState(BaseModel):
    """State for email writing graph"""
    to: str
    subject: str
    text: str
    tone: str
    should_generate: bool
    generated_body: Optional[str] = None
    status: str = "initialized"
    error: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None

    # MCP client resource
    mcp: Optional[Any] = None

    class Config:
        arbitrary_types_allowed = True

class EmailClassificationState(BaseModel):
    """
    State schema for email classification workflow.
    Supports both single email and batch classification.
    """
    # Mode selection
    mode: Literal["single", "batch"] = Field(
        description="Classification mode: 'single' for one email, 'batch' for multiple"
    )
    
    # Single email mode fields
    email_id: Optional[str] = Field(
        None,
        description="Email ID for single email classification"
    )

    email_ids: Optional[List[str]] = Field(
        None,
        description="List of Email IDs for batch classification"
    )
    
    # Batch mode fields
    after_date: Optional[datetime] = Field(
        None,
        description="Start date for batch classification (inclusive)"
    )
    before_date: Optional[datetime] = Field(
        None,
        description="End date for batch classification (inclusive)"
    )
    max_results: Optional[int] = Field(
        100,
        description="Maximum number of emails to fetch in batch mode"
    )
    
    # Classification configuration
    categories: List[str] = Field(
        description="List of predefined categories for classification"
    )
    parallelize: bool = Field(
        True,
        description="Whether to parallelize batch classification"
    )
    apply_labels: bool = Field(
        False,
        description="Whether to apply classification labels to emails in Gmail"
    )
    
    # MCP client
    mcp: Any = Field(
        description="MCP client for Gmail operations"
    )
    
    # Workflow state fields
    emails: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Fetched emails to classify"
    )
    classification_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Classification results with email_id and category"
    )
    status: Optional[str] = Field(
        None,
        description="Current workflow status"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if workflow fails"
    )
    total_emails: Optional[int] = Field(
        None,
        description="Total number of emails fetched"
    )
    total_classified: Optional[int] = Field(
        None,
        description="Total number of emails successfully classified"
    )
    labeled_count: Optional[int] = Field(
        None,
        description="Number of emails labeled (if apply_labels=True)"
    )
    label_errors: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Errors encountered while applying labels"
    )

    class Config:
        arbitrary_types_allowed = True


class ClassificationRequest(BaseModel):
    """Request model for email classification."""
    # Batch mode fields
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_results: Optional[int] = 100

class ClassificationResponse(BaseModel):
    """Response model for email classification."""
    status: str
    message: str
    total_emails: Optional[int] = None
    total_classified: Optional[int] = None
    classification_results: Optional[List[Dict[str, Any]]] = None
    labeled_count: Optional[int] = None
    error: Optional[str] = None