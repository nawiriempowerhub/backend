from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

from datetime import date
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
        
class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ==============================================================================
# 📚 Program Schemas
# ==============================================================================

class ProgramBase(BaseModel):
    """Base schema for program details."""
    title: str
    description: str
    category: ProgramCategory
   

class ProgramCreate(ProgramBase):
    """Schema for creating a new program."""
    pass

class ProgramUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class Program(ProgramBase):
    """Schema for returning program data in responses."""
    id: int
    image_url: str
    created_at: datetime

    class Config:
        orm_mode = True

# ==============================================================================
# 🖼️ Media Schemas
# ==============================================================================

class MediaBase(BaseModel):
    """Base schema for media items."""
    title: str
    type: MediaType
    file_url: Optional[HttpUrl] = None
    program_id: Optional[int] = None
    description: Optional[str] = None

class MediaCreate(MediaBase):
    """Schema for creating a new media item record."""
    pass

class Media(MediaBase):
    """Schema for returning media item data in responses."""
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class MediaProgramUpdate(BaseModel):
    program_id: Optional[int]
    
from typing import Optional
from pydantic import BaseModel
import enum

   

class MediaUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    type: Optional[MediaType]
    file_url: Optional[str]
    external_link: Optional[str]
    is_featured: Optional[bool]
    tags: Optional[str]
    program_id: Optional[int]  # Optional: still allow updating program too

    
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

class VolunteerForm(BaseModel):
    """Base schema for volunteer applications."""
    name: str
    email: EmailStr
    phone: str
    motivation: str

class VolunteerCreate(VolunteerForm):
    """Schema for creating a new volunteer application."""
    pass

class Volunteer(VolunteerForm):
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


class EventRegistrationBase(BaseModel):
    name: str
    email: EmailStr

class EventRegistrationCreate(EventRegistrationBase):
    event_id: int

class EventRegistrationResponse(EventRegistrationBase):
    id: int
    event_id: int

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
    
# ============================
# 👥 Team Member Schemas
# ============================

class TeamMemberBase(BaseModel):
    id: int
    name: str
    role: str
    bio: str
    photo_filename: Optional[str]  # Change from HttpUrl to Optional[str]


    class Config:
        orm_mode = True
        
class TeamMemberCreate(TeamMemberBase): pass

class TeamMember(TeamMemberBase):
    id: int
    class Config:
        orm_mode = True

# ============================
# 📄 About Schemas
# ============================

class AboutBase(BaseModel):
    story: str
    mission: str
    vision: str
    core_values: str
    impact_summary: Optional[str] = None
    timeline: Optional[str] = None

class AboutCreate(AboutBase): pass
class AboutUpdate(AboutBase): pass

class About(AboutBase):
    id: int
    class Config:
        orm_mode = True

class AboutResponse(BaseModel):
    about: AboutBase
    team: List[TeamMemberBase]

class ImpactEventBase(BaseModel):
    id: int
    title: str
    description: str
    date: date
    image_filename: Optional[HttpUrl] = None  # ✅ Full image URL

class ImpactEventCreate(ImpactEventBase):
    pass  # image is handled separately via UploadFile

class ImpactEvent(ImpactEventBase):
    id: int
    image_filename: Optional[HttpUrl] = None  # ✅ Full image URL

    class Config:
        orm_mode = True
        
class PaymentMethod(str, enum.Enum):
    mpesa = "M-Pesa"
    card = "Card"
    bank = "Bank"
    cash = "Cash"
    other = "Other"

class DonationBase(BaseModel):
    donor_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    amount: float
    payment_method: Optional[PaymentMethod] = PaymentMethod.mpesa

class DonationCreate(DonationBase):
    pass

class Donation(DonationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        



class DonationForm(BaseModel):
    donor_name: str
    email: EmailStr
    amount: float
    phone: Optional[str]
    payment_method: str

class EventRegistrationForm(BaseModel):
    name: str
    email: EmailStr
    event_id: int