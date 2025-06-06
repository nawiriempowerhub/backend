from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    VOLUNTEER = "Volunteer"
    PARTNER = "Partner"
    USER = "User"

class ProgramCategory(str, enum.Enum):
    MENSTRUAL_HEALTH = "Menstrual Health"
    DIGITAL_LITERACY = "Digital Literacy"
    YOUTH_EMPOWERMENT = "Youth Empowerment"

class MediaType(str, enum.Enum):
    PHOTO = "Photo"
    VIDEO = "Video"
    REPORT = "Report"

class VolunteerStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VOLUNTEER)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    blog_posts = relationship("BlogPost", back_populates="author")

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(Enum(ProgramCategory))
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    media = relationship("Media", back_populates="program")

class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    type = Column(Enum(MediaType))
    url = Column(String)
    program_id = Column(Integer, ForeignKey("programs.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    program = relationship("Program", back_populates="media")

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    tags = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    author = relationship("User", back_populates="blog_posts")

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