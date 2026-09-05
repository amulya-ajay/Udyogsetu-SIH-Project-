export type UserRole = 'ENTREPRENEUR' | 'OFFICER' | 'ADMIN'

export interface User {
  id: string
  email: string
  name: string
  phone: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface Project {
  id: string
  name: string
  company_name: string
  industry: string
  sector: string
  investment_amount?: number
  location_state?: string
  location_district?: string
  created_at: string
}

export interface Approval {
  id: string
  name: string
  department: string
  status: string
  is_mandatory: boolean
  estimated_processing_days?: number
  risk_level: string
}

export interface Document {
  id: string
  file_name: string
  file_type: string
  status: string
  extracted_fields: Record<string, any>
  validation_errors: string[]
  created_at: string
}

export interface Scheme {
  id: string
  name: string
  department: string
  sector?: string
  benefits: string[]
  match_score?: number
  match_reason?: string
}

export interface ComplianceItem {
  id: string
  category: string
  requirement: string
  status: string
  due_date?: string
  next_due?: string
}

export interface GovernmentService {
  id: string
  slug: string
  name: string
  description?: string
  category: string
  authority?: string
  department: string
  service_type: string
  application_mode: 'INTEGRATED' | 'GUIDED' | 'REDIRECT' | 'DEMO'
  official_reference?: string
  external_portal_url?: string
  applicable_documents?: { document_type: string; description?: string; required?: boolean }[]
  fees?: string
  eligibility_summary?: string
  risk_level: string
  sla_days?: number
  renewal_period_days?: number
  approval_rule_id?: string
  gateway_system?: string
  is_demo: boolean
  is_active: boolean
}

export interface ApplicabilityResult {
  service_id: string
  service_slug: string
  status: 'APPLICABLE' | 'NOT_APPLICABLE' | 'NOT_DETERMINED'
  reason: string
  matched_conditions: string[]
  failed_conditions: string[]
  required_documents: string[]
  rule_id?: string
}

export interface ServiceDocumentEntry {
  document_type: string
  description: string
  required: boolean
}

export interface ServiceDocumentsResponse {
  service_id: string
  service_slug: string
  required_documents: ServiceDocumentEntry[]
  project_id?: string
  project_documents: {
    id: string
    file_name: string
    status: string
    document_type?: string
    matches_requirement: number[]
  }[]
}

export interface ChecklistApplication {
  approval_id: string
  application_id: string
  name: string
  department: string
  status: string
  service_slug?: string
  required_documents: ServiceDocumentEntry[]
  attached_documents: {
    id: string
    file_name: string
    status: string
    document_type?: string
  }[]
  available_transitions: { to: string; label: string; side_effect: string }[]
}

export interface ApplicationItem {
  application_id: string
  approval_id?: string
  approval_name: string
  department: string
  project_name?: string
  status: string
  submitted_at?: string
  approved_at?: string
  estimated_processing_days?: number
  risk_level?: string
}

export interface ApplicationDetail extends ApplicationItem {
  documents?: { id: string; file_name: string; status: string; document_type?: string }[]
  government?: {
    system?: string
    government_application_id?: string
    last_synced_status?: string
  }
  owner_email?: string
  owner_name?: string
  company_name?: string
  source?: string
  available_transitions?: { to: string; label: string; side_effect: string }[]
}

export interface SlaStatus {
  application_id?: string
  approval_name?: string
  status: 'ON_TRACK' | 'AT_RISK' | 'BREACHED' | 'COMPLETED' | 'NOT_STARTED'
  sla_days: number
  days_elapsed: number
  days_remaining: number
  reason: string
  breach_probability: number
  deadline?: string
}
