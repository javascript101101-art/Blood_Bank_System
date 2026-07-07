from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

# *** ဒီမှာ လိုအပ်တဲ့ Model အားလုံးကို ထည့်လိုက်ပါ ***
from .user import User
from .donor import Donor
from .inventory import Inventory
from .blood_request import BloodRequest

class Hospital(BaseModel):
    __tablename__ = "hospitals"

    name = Column(String(255), nullable=False)
    location = Column(Text)
    contact_email = Column(String(255))
    is_active = Column(Boolean, default=True)

    # Relationships (အခု SQLAlchemy က User, Donor, Inventory, BloodRequest ကို ရှာတွေ့ပါပြီ)
    users = relationship("User", back_populates="hospital")
    donors = relationship("Donor", back_populates="hospital")
    inventories = relationship("Inventory", back_populates="hospital")
    requests = relationship("BloodRequest", back_populates="hospital")