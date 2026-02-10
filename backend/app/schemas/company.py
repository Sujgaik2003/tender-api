from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date

class CompanyProfileCreate(BaseModel):
    legal_name: str
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    company_address: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    capabilities: List[str] = []
    certifications: List[Dict[str, Any]] = [] # {name, issuer, expiry}
    insurance: List[Dict[str, Any]] = [] # {type, provider, amount}

class CompanyProfileResponse(CompanyProfileCreate):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PastPerformanceCreate(BaseModel):
    project_title: str
    client_name: Optional[str] = None
    project_value: Optional[float] = None
    currency: Optional[str] = "USD"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    challenges: Optional[str] = None
    solution: Optional[str] = None
    outcomes: Optional[str] = None
    keywords: List[str] = []
    reference_contact: Optional[Dict[str, str]] = None

class PastPerformanceResponse(PastPerformanceCreate):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TeamProfileCreate(BaseModel):
    full_name: str
    designation: Optional[str] = None
    years_experience: Optional[int] = None
    skills: List[str] = []
    qualifications: List[str] = []
    bio_summary: Optional[str] = None
    full_cv_text: Optional[str] = None
    linkedin_url: Optional[str] = None

class TeamProfileResponse(TeamProfileCreate):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# --- Enterprise Member Management ---

class MemberResponse(BaseModel):
    id: UUID
    full_name: Optional[str]
    role: str
    department: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class MemberUpdate(BaseModel):
    role: str
