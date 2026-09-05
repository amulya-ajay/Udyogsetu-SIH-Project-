from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum as SQLEnum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    ENTREPRENEUR = "ENTREPRENEUR"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"

class ApprovalStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    QUERY_RAISED = "QUERY_RAISED"
    INSPECTION = "INSPECTION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"

class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    VERIFIED = "VERIFIED"
    WARNING = "WARNING"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    MISSING = "MISSING"

class ComplianceStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    OVERDUE = "OVERDUE"

class ServiceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

approval_documents = Table(
    "approval_documents",
    Base.metadata,
    Column(
        "approval_id",
        UUID(as_uuid=True),
        ForeignKey("approvals.id"),
        primary_key=True,
    ),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        primary_key=True,
    ),
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.ENTREPRENEUR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("Project", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    business_type = Column(String(100))
    industry = Column(String(100))
    sector = Column(String(100))
    project_stage = Column(String(100))
    investment_amount = Column(Float)
    
    location_state = Column(String(100))
    location_district = Column(String(100))
    location_city = Column(String(100))
    location_industrial_area = Column(String(255))
    location_midc_estate = Column(String(255))
    land_type = Column(String(100))
    
    employees = Column(Integer)
    production_type = Column(String(100))
    hazardous_materials = Column(Boolean, default=False)
    has_boiler = Column(Boolean, default=False)
    electricity_load = Column(Float)
    water_consumption = Column(Float)
    pollution_potential = Column(String(50))
    building_type = Column(String(100))
    
    is_new = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="projects")
    approvals = relationship("Approval", back_populates="project")
    documents = relationship("Document", back_populates="project")
    compliance_items = relationship("ComplianceItem", back_populates="project")

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    sector = Column(String(100))
    is_mandatory = Column(Boolean, default=False)
    risk_level = Column(String(50), default="MEDIUM")
    estimated_processing_days = Column(Integer)
    renewal_period_days = Column(Integer)
    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.NOT_STARTED)
    application_id = Column(String(100))
    submitted_at = Column(DateTime)
    approved_at = Column(DateTime)
    source = Column(String(255))
    source_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="approvals")
    documents = relationship("Document", secondary="approval_documents")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    category = Column(String(50), default="general")
    severity = Column(String(20), default="info")
    is_read = Column(Boolean, default=False)
    project_id = Column(UUID(as_uuid=True), nullable=True)
    reference_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "title": self.title,
            "message": self.message,
            "category": self.category,
            "severity": self.severity,
            "is_read": self.is_read,
            "project_id": str(self.project_id) if self.project_id else None,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)
    extracted_text = Column(Text)
    extracted_fields = Column(JSONB, default={})
    custom_metadata = Column(JSONB, default={})
    validation_errors = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="documents")

class ComplianceItem(Base):
    __tablename__ = "compliance_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    requirement = Column(String(255), nullable=False)
    frequency = Column(String(50))
    due_date = Column(DateTime)
    status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.ON_TRACK)
    last_completed = Column(DateTime)
    next_due = Column(DateTime)
    document_required = Column(Boolean, default=False)
    source = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="compliance_items")

class ApprovalRule(Base):
    __tablename__ = "approval_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    department = Column(String(100), nullable=False)
    sector = Column(String(100))
    location = Column(String(100))
    conditions = Column(JSONB, nullable=False)
    is_mandatory = Column(Boolean, default=False)
    required_documents = Column(JSON, default=[])
    dependencies = Column(JSON, default=[])
    estimated_processing_days = Column(Integer)
    renewal_period_days = Column(Integer)
    risk_level = Column(String(50), default="MEDIUM")
    source = Column(String(255))
    source_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    department = Column(String(100))
    document_type = Column(String(100))
    date = Column(DateTime)
    effective_date = Column(DateTime)
    effective_to = Column(DateTime)
    supersedes_document_id = Column(UUID(as_uuid=True), nullable=True)
    source_url = Column(String(500))
    version = Column(String(50))
    jurisdiction = Column(String(100))
    sector = Column(String(100))
    text = Column(Text, nullable=False)
    is_latest = Column(Boolean, default=True)
    superseded_by_document_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id"))
    chunk_index = Column(Integer)
    text = Column(Text, nullable=False)
    embedding = Column(JSONB)
    custom_metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB, default={})
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")

class GovernmentApplication(Base):
    """Tracks a submitted application's live state as reported by the
    government integration layer (spec §19)."""
    __tablename__ = "government_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_id = Column(UUID(as_uuid=True), ForeignKey("approvals.id"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    system = Column(String(100), nullable=False)
    government_application_id = Column(String(100), nullable=False)
    last_synced_status = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    raw_response = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    sector = Column(String(100))
    location = Column(String(100))
    min_investment = Column(Float)
    max_investment = Column(Float)
    eligible_entity = Column(String(100))
    employee_requirement = Column(Integer)
    benefits = Column(JSON, default=[])
    application_period = Column(String(255))
    required_documents = Column(JSON, default=[])
    source = Column(String(255))
    source_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GovernmentService(Base):
    """Explore catalog entry for a government service.

    A service links to an ``ApprovalRule`` so the existing engine evaluates
    project applicability deterministically, and to a gateway ``system`` for
    tracked (DEMO) or guided submission flows.

    ``application_mode`` values:
      INTEGRATED - application can be created and submitted via UdyogSetu
      GUIDED     - checklist/docs prepared in UdyogSetu, submission at the authority
      REDIRECT   - "Apply" opens the official external portal
      DEMO       - mock end-to-end demonstration (is_demo should be True)
    """

    __tablename__ = "government_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    authority = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    service_type = Column(String(50), default="APPROVAL")
    application_mode = Column(String(20), default="GUIDED")
    status = Column(SQLEnum(ServiceStatus), default=ServiceStatus.ACTIVE)
    official_reference = Column(String(255))
    external_portal_url = Column(String(500))
    applicable_documents = Column(JSON, default=[])
    fees = Column(String(255))
    eligibility_summary = Column(Text)
    risk_level = Column(String(50), default="MEDIUM")
    sla_days = Column(Integer)
    renewal_period_days = Column(Integer)
    approval_rule_id = Column(UUID(as_uuid=True), ForeignKey("approval_rules.id"), nullable=True, index=True)
    gateway_system = Column(String(50), nullable=True)
    is_demo = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    approval_rule = relationship("ApprovalRule")


class AIEventLog(Base):
    """Non-sensitive observability record for AI/LLM interactions (spec §34).

    Deliberately excludes API keys, passwords and document bodies. Only metadata
    needed for cost/performance monitoring is stored.
    """

    __tablename__ = "ai_event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    request_type = Column(String(50), nullable=False)      # generation/classification/embed/tool
    model = Column(String(100), nullable=True)             # provider/model label
    latency_ms = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_kind = Column(String(100), nullable=True)
    event_metadata = Column("metadata", JSONB, default={})  # extra, non-sensitive detail
    created_at = Column(DateTime, default=datetime.utcnow)
