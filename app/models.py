from datetime import datetime
import json
from sqlalchemy import Boolean, Column, Date, Float, Integer, String, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
import enum
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.types import TypeDecorator, TEXT

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    # VOLUNTEER = "VOLUNTEER"
    # PARTNER = "PARTNER"
    # USER = "USER"  # Add this only if your DB also has 'USER'

# models/about.py
from sqlalchemy import Column, Integer, String, Text, Date
from app.database import Base

class About(Base):
    __tablename__ = "about"

    id = Column(Integer, primary_key=True, index=True)
    story = Column(Text)
    mission = Column(Text)
    vision = Column(Text)
    core_values = Column(Text)
    impact_summary = Column(Text, nullable=True)
    timeline = Column(Text, nullable=True)

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    role = Column(String)
    bio = Column(Text)
    photo_filename = Column(String, nullable=False)  # ✅ must be provided

class ImpactEvent(Base):
    __tablename__ = "impact_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    date = Column(Date)
    image_filename = Column(String, nullable=True)  # ✅ Add image filename

class ProgramCategory(str, enum.Enum):
    MENSTRUAL_HEALTH = "Menstrual Health"
    DIGITAL_LITERACY = "Digital Literacy"
    YOUTH_EMPOWERMENT = "Youth Empowerment"

class MediaType(str, enum.Enum):
    PHOTO = "PHOTO"
    VIDEO = "VIDEO"
    # INFOGRAPHIC = "INFOGRAPHIC"
    TESTIMONIAL = "TESTIMONIAL"
    # REPORT_LINK = "REPORT_LINK"
    # NEWSLETTER = "NEWSLETTER"
    # MEDIA_COVERAGE = "MEDIA_COVERAGE"
    YOUTUBE_EMBED = "YOUTUBE_EMBED"


class VolunteerStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ADMIN)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class JSONList(TypeDecorator):
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value
class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, index=True)
    description = Column(Text)
    objectives = Column(MutableList.as_mutable(JSONList), default=[])
    target_group = Column(MutableList.as_mutable(JSONList), default=[])
    # ...
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    status = Column(String, default="Ongoing")  # You can use Enum if status is fixed set
    category = Column(Enum(ProgramCategory), nullable=True)
    featured_image_url = Column(String)  # Rename from image_url for clarity
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    media = relationship("Media", back_populates="program")

class Media(Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(MediaType), nullable=False)

    file_url = Column(String, nullable=True)  # For uploaded file path (photo/video)
    external_link = Column(String, nullable=True)  # For YouTube or cloud-hosted videos

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_featured = Column(Boolean, default=False)

    program_id = Column(Integer, ForeignKey('programs.id'))
    program = relationship("Program", back_populates="media")

class ContactSubmission(Base):
    __tablename__ = "contact_submissions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    message = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Volunteer(Base):
    __tablename__ = "volunteers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    motivation = Column(Text)
    status = Column(Enum(VolunteerStatus), default=VolunteerStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(DateTime(timezone=True))
    location = Column(String)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
  
class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"))

    event = relationship("Event", back_populates="registrations")

# In your Event model, add:
Event.registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete")
  
# class PaymentMethod(str, enum.Enum):
#     mpesa = "M-Pesa"


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    # payment_method = Column(Enum(PaymentMethod), default="M-Pesa")
    donor_phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())