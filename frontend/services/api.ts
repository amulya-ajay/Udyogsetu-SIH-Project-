import axios, { AxiosInstance, AxiosError } from 'axios'
import { clearSession, getToken, setSession } from '@/lib/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: { 'Content-Type': 'application/json' },
      timeout: 30000,
    })

    this.client.interceptors.request.use((config) => {
      const token = getToken()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
          clearSession()
          if (!window.location.pathname.startsWith('/login')) {
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      },
    )
  }

  private extractErrorMessage(error: any): string {
    return error.response?.data?.detail || error.message || 'Request failed'
  }

  getToken(): string | null {
    return getToken()
  }

  getCurrentUser(): any | null {
    if (typeof window === 'undefined') return null
    try {
      const raw = localStorage.getItem('udyogsetu_user')
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  setSession(token: string, user?: any) {
    setSession(token, user)
  }

  clearSession() {
    clearSession()
  }

  async register(email: string, name: string, phone: string, password: string, role: string) {
    const response = await this.client.post('/auth/register', { email, name, phone, password, role })
    return response.data
  }

  async login(email: string, password: string) {
    const response = await this.client.post('/auth/login', { email, password })
    return response.data
  }

  async createProject(projectData: any) {
    const response = await this.client.post('/projects', projectData)
    return response.data
  }

  async listProjects() {
    const response = await this.client.get('/projects')
    return response.data
  }

  async getProject(projectId: string) {
    const response = await this.client.get(`/projects/${projectId}`)
    return response.data
  }

  async analyzeProject(projectId: string) {
    const response = await this.client.post(`/projects/${projectId}/analyze`)
    return response.data
  }

  async getProjectApprovals(projectId: string) {
    const response = await this.client.get(`/projects/${projectId}/approvals`)
    return response.data
  }

  async getApprovalGraph(projectId: string) {
    const response = await this.client.get(`/projects/${projectId}/approval-graph`)
    return response.data
  }

  async submitApplication(applicationId: string) {
    const response = await this.client.post(`/applications/${applicationId}/submit`)
    return response.data
  }

  async getOfficerOverview() {
    const response = await this.client.get('/officer/full')
    return response.data
  }

  async uploadDocument(projectId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post(`/documents/upload?project_id=${projectId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async queryRegulatoryCopilot(question: string, projectId?: string) {
    const response = await this.client.post('/chat/query', { question, project_id: projectId })
    return response.data
  }

  async matchSchemes(industryData: any) {
    const response = await this.client.post('/schemes/match', industryData)
    return response.data
  }

  async getComplianceDashboard(projectId: string) {
    const response = await this.client.get(`/compliance/${projectId}`)
    return response.data
  }

  // ---- Explore Government Services -------------------------------------
  async listServices(params?: Record<string, any>) {
    const response = await this.client.get('/explore/services', { params })
    return response.data
  }

  async getServiceCategories() {
    const response = await this.client.get('/explore/services/categories')
    return response.data
  }

  async getService(serviceId: string) {
    const response = await this.client.get(`/explore/services/${serviceId}`)
    return response.data
  }

  async getServiceDocuments(serviceId: string, projectId?: string) {
    const response = await this.client.get(`/explore/services/${serviceId}/documents`, {
      params: projectId ? { project_id: projectId } : undefined,
    })
    return response.data
  }

  async checkApplicability(serviceId: string, projectId: string) {
    const response = await this.client.post(`/explore/services/${serviceId}/check-applicability`, {
      project_id: projectId,
    })
    return response.data
  }

  async addToChecklist(serviceId: string, projectId: string) {
    const response = await this.client.post(`/explore/services/${serviceId}/checklist`, {
      project_id: projectId,
    })
    return response.data
  }

  async getChecklistApproval(approvalId: string) {
    const response = await this.client.get(`/explore/checklist/${approvalId}`)
    return response.data
  }

  async startChecklistApplication(approvalId: string) {
    const response = await this.client.post(`/explore/checklist/${approvalId}/start`)
    return response.data
  }

  async attachChecklistDocument(approvalId: string, documentId: string) {
    const response = await this.client.post(`/explore/checklist/${approvalId}/attach-document`, {
      document_id: documentId,
    })
    return response.data
  }

  async detachChecklistDocument(approvalId: string, documentId: string) {
    const response = await this.client.post(`/explore/checklist/${approvalId}/detach-document`, {
      document_id: documentId,
    })
    return response.data
  }

  // ---- Applications (owner-scoped tracking) ----------------------------
  async listApplications() {
    const response = await this.client.get('/applications')
    return response.data
  }

  async getApplication(applicationId: string) {
    const response = await this.client.get(`/applications/${applicationId}`)
    return response.data
  }

  async getApplicationTransitions(applicationId: string) {
    const response = await this.client.get(`/applications/${applicationId}/transitions`)
    return response.data
  }

  async getSlaStatus(applicationId: string) {
    const response = await this.client.get(`/applications/${applicationId}/sla`)
    return response.data
  }

  async transitionApplication(applicationId: string, toStatus: string) {
    const response = await this.client.post(`/applications/${applicationId}/transition`, {
      to_status: toStatus,
    })
    return response.data
  }

  // ---- Officer review ----------------------------------------------------
  async officerListApplications(params?: Record<string, any>) {
    const response = await this.client.get('/officer/applications', { params })
    return response.data
  }

  async officerGetApplication(applicationId: string) {
    const response = await this.client.get(`/officer/applications/${applicationId}`)
    return response.data
  }

  async officerTransitionApplication(applicationId: string, toStatus: string) {
    const response = await this.client.post(`/officer/applications/${applicationId}/transition`, {
      to_status: toStatus,
    })
    return response.data
  }

  async officerSyncApplication(applicationId: string) {
    const response = await this.client.post(`/officer/applications/${applicationId}/sync`)
    return response.data
  }
}

export const apiClient = new ApiClient()
export { API_URL }