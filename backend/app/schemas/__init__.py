from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRole(str, Enum):
    ENTREPRENEUR = "ENTREPRENEUR"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"


class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=10, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.ENTREPRENEUR

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    phone: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ProjectCreate(BaseModel):
    name: str
    company_name: str
    business_type: str
    industry: str
    sector: str


class ProjectOnboarding(BaseModel):
    company_name: str = Field(min_length=2)
    business_type: str = Field(min_length=2)
    industry: str = Field(min_length=2)
    sector: str = Field(min_length=2)

    project_name: str = Field(min_length=2)
    is_new: bool = True
    project_stage: str = Field(min_length=2)
    investment_amount: float = Field(ge=0)

    location_state: str = Field(min_length=2)
    location_district: str = Field(min_length=2)
    location_city: str = Field(min_length=2)
    location_industrial_area: str | None = None
    location_midc_estate: str | None = None
    land_type: str = Field(min_length=2)

    employees: int = Field(ge=0)
    production_type: str = Field(default="", min_length=0)
    hazardous_materials: bool = False
    has_boiler: bool = False
    electricity_load: float = Field(default=0, ge=0)
    water_consumption: float = Field(default=0, ge=0)
    pollution_potential: str = "low"
    building_type: str = Field(default="", min_length=0)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    company_name: str
    industry: str
    sector: str
    investment_amount: float | None
    location_state: str | None
    location_district: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    id: UUID
    name: str
    department: str
    status: str
    is_mandatory: bool
    estimated_processing_days: int | None
    risk_level: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    status: str
    extracted_fields: dict
    validation_errors: list
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceItemResponse(BaseModel):
    id: UUID
    category: str
    requirement: str
    status: str
    due_date: datetime | None
    next_due: datetime | None

    class Config:
        from_attributes = True


class SchemeMatcher(BaseModel):
    industry: str
    location: str
    investment: float
    employees: int
    business_type: str


class SchemeResponse(BaseModel):
    id: UUID
    name: str
    department: str
    sector: str | None
    min_investment: float | None
    max_investment: float | None
    benefits: list
    match_score: float | None = None
    match_reason: str | None = None

    class Config:
        from_attributes = True


class GovernmentServiceResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None = None
    category: str
    authority: str
    department: str
    service_type: str
    application_mode: str
    status: str
    official_reference: str | None = None
    external_portal_url: str | None = None
    applicable_documents: list = Field(default_factory=list)
    fees: str | None = None
    eligibility_summary: str | None = None
    risk_level: str = "MEDIUM"
    sla_days: int | None = None
    renewal_period_days: int | None = None
    gateway_system: str | None = None
    is_demo: bool = False
    is_active: bool = True

    class Config:
        from_attributes = True


class ExploreCheckRequest(BaseModel):
    project_id: UUID


class ExploreChecklistRequest(BaseModel):
    project_id: UUID


class ExploreDocumentAttachRequest(BaseModel):
    document_id: UUID


class GovernmentServiceCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category: str = Field(min_length=2, max_length=100)
    authority: str = Field(min_length=2, max_length=255)
    department: str = Field(min_length=2, max_length=100)
    service_type: str = "APPROVAL"
    application_mode: str = "GUIDED"
    official_reference: str | None = None
    external_portal_url: str | None = None
    applicable_documents: list = Field(default_factory=list)
    fees: str | None = None
    eligibility_summary: str | None = None
    risk_level: str = "MEDIUM"
    sla_days: int | None = None
    renewal_period_days: int | None = None
    approval_rule_id: UUID | None = None
    gateway_system: str | None = None
    is_demo: bool = False
    is_active: bool = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatQuery(BaseModel):
    question: str = Field(min_length=1)
    project_id: UUID | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float
    relevant_regulations: list[str]