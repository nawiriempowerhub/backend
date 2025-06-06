from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from .models import UserRole, ProgramCategory, MediaType, VolunteerStatus

# ==============================================================================
# 🔐 User Schemas
# ==============================================================================

class UserBase(BaseModel):
    """Base schema for user, contains common fields."""
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    """Schema for creating a new user. Includes password."""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.ADMIN

class User(UserBase):
    """Schema for returning user data in responses. Excludes password."""
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        orm_mode = True

# ==============================================================================
# 📚 Program Schemas
# ==============================================================================

class ProgramBase(BaseModel):
    """Base schema for program details."""
    title: str
    description: str
    category: ProgramCategory
    image_url: Optional[str] = None

class ProgramCreate(ProgramBase):
    """Schema for creating a new program."""
    pass

class Program(ProgramBase):
    """Schema for returning program data in responses."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ==============================================================================
# 📝 Blog Schemas
# ==============================================================================

class BlogBase(BaseModel):
    """Base schema for blog posts."""
    title: str
    content: str
    tags: Optional[str] = None

class BlogCreate(BlogBase):
    """Schema for creating a new blog post."""
    pass

class Blog(BlogBase):
    """Schema for returning blog post data, includes author info."""
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# ==============================================================================
# 🖼️ Media Schemas
# ==============================================================================

class MediaBase(BaseModel):
    """Base schema for media items."""
    title: str
    type: MediaType
    url: str
    program_id: Optional[int] = None

class MediaCreate(MediaBase):
    """Schema for creating a new media item record."""
    pass

class Media(MediaBase):
    """Schema for returning media item data in responses."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ==============================================================================
# 📩 Contact Submission Schemas
# ==============================================================================

class ContactSubmissionBase(BaseModel):
    """Base schema for contact form submissions."""
    name: str
    email: EmailStr
    message: str

class ContactSubmissionCreate(ContactSubmissionBase):
    """Schema for creating a new contact submission."""
    pass

class ContactSubmission(ContactSubmissionBase):
    """Schema for returning contact submission data in responses."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ==============================================================================
# 🧾 Volunteer Schemas
# ==============================================================================

class VolunteerBase(BaseModel):
    """Base schema for volunteer applications."""
    name: str
    email: EmailStr
    phone: str
    motivation: str

class VolunteerCreate(VolunteerBase):
    """Schema for creating a new volunteer application."""
    pass

class Volunteer(VolunteerBase):
    """Schema for returning volunteer application data in responses."""
    id: int
    status: VolunteerStatus
    created_at: datetime

    class Config:
        orm_mode = True

class VolunteerStatusUpdate(BaseModel):
    """Schema specifically for updating a volunteer's status."""
    status: VolunteerStatus

# ==============================================================================
# 📆 Event Schemas
# ==============================================================================

class EventBase(BaseModel):
    """Base schema for events."""
    title: str
    date: datetime
    location: str
    description: str

class EventCreate(EventBase):
    """Schema for creating a new event."""
    pass

class Event(EventBase):
    """Schema for returning event data in responses."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ==============================================================================
# 🔑 Authentication Token Schemas
# ==============================================================================

class Token(BaseModel):
    """Schema for the access token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for the data encoded within the JWT."""
    email: Optional[str] = None