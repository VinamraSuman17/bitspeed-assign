from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from datetime import datetime, timezone
from app.database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=True)
    phone_number = Column(String, index=True, nullable=True)
    linked_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    link_precedence = Column(Enum("primary", "secondary", name="link_precedence"), default="primary")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)
