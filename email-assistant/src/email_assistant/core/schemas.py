from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal, Any


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
