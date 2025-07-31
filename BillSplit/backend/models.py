from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

# Base model for common fields like ID and creation timestamp
class PyBaseModel(BaseModel):
    id: str = Field(None, alias="doc_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    class Config:
        populate_by_name = True

# User Models (no change)
class UserBase(BaseModel):
    firebase_uid: str
    email: str
    username: str

class UserInDB(UserBase, PyBaseModel):
    pass

# Group Models
class GroupBase(BaseModel):
    # This will be used for GroupInDB (what's read/stored)
    name: str
    description: Optional[str] = None
    owner_id: str # Keep owner_id here for the stored/retrieved Group object

class GroupCreate(BaseModel): # <--- DO NOT INHERIT FROM GroupBase for creation
    name: str
    description: Optional[str] = None
    member_uids: List[str] = [] # List of Firebase UIDs of initial members (these are emails from frontend)

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class GroupInDB(GroupBase, PyBaseModel): # <--- GroupInDB still inherits GroupBase
    members: List[str] = []

# Expense Models
class ExpenseParticipantData(BaseModel):
    user_id: str # Firestore doc_id of the user
    share_amount: Optional[float] = None # For unequal splitting

class ExpenseBase(BaseModel):
    description: str
    amount: float
    payer_id: str # Firestore doc_id of the user who paid
    group_id: str # Firestore doc_id of the group
    participants: List[ExpenseParticipantData] # Users involved in this expense

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    payer_id: Optional[str] = None
    participants: Optional[List[ExpenseParticipantData]] = None

class ExpenseInDB(ExpenseBase, PyBaseModel):
    pass

# Settlement Models
class SettlementTransaction(BaseModel):
    payer_id: str # User who owes
    receiver_id: str # User who is owed
    amount: float
    payer_name: Optional[str] = None # For display
    receiver_name: Optional[str] = None # For display

class SettlementResult(BaseModel):
    balances: Dict[str, float] # user_id: balance
    transactions: List[SettlementTransaction]