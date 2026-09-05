import { useQuery, useMutation } from '@tanstack/react-query'
import { apiClient } from '@/services/api'

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => apiClient.getProject(projectId),
    enabled: !!projectId,
  })
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.listProjects(),
  })
}

export function useProjectApprovals(projectId: string) {
  return useQuery({
    queryKey: ['project-approvals', projectId],
    queryFn: () => apiClient.getProjectApprovals(projectId),
    enabled: !!projectId,
  })
}

export function useApprovalGraph(projectId: string) {
  return useQuery({
    queryKey: ['approval-graph', projectId],
    queryFn: () => apiClient.getApprovalGraph(projectId),
    enabled: !!projectId,
  })
}

export function useOfficerOverview() {
  return useQuery({
    queryKey: ['officer-overview'],
    queryFn: () => apiClient.getOfficerOverview(),
  })
}

export function useCreateProject() {
  return useMutation({
    mutationFn: (projectData: any) => apiClient.createProject(projectData),
  })
}

export function useAnalyzeProject() {
  return useMutation({
    mutationFn: (projectId: string) => apiClient.analyzeProject(projectId),
  })
}

export function useUploadDocument() {
  return useMutation({
    mutationFn: ({ projectId, file }: { projectId: string; file: File }) =>
      apiClient.uploadDocument(projectId, file),
  })
}

export function useRegulatoryQuery() {
  return useMutation({
    mutationFn: ({ question, projectId }: { question: string; projectId?: string }) =>
      apiClient.queryRegulatoryCopilot(question, projectId),
  })
}

export function useMatchSchemes() {
  return useMutation({
    mutationFn: (industryData: any) => apiClient.matchSchemes(industryData),
  })
}

export function useComplianceDashboard(projectId: string) {
  return useQuery({
    queryKey: ['compliance', projectId],
    queryFn: () => apiClient.getComplianceDashboard(projectId),
    enabled: !!projectId,
  })
}

// ---- Explore Government Services ----------------------------------------
export function useServices(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['explore-services', params],
    queryFn: () => apiClient.listServices(params),
  })
}

export function useServiceCategories() {
  return useQuery({
    queryKey: ['explore-categories'],
    queryFn: () => apiClient.getServiceCategories(),
  })
}

export function useService(serviceId: string) {
  return useQuery({
    queryKey: ['explore-service', serviceId],
    queryFn: () => apiClient.getService(serviceId),
    enabled: !!serviceId,
  })
}

export function useServiceDocuments(serviceId: string, projectId?: string) {
  return useQuery({
    queryKey: ['explore-service-documents', serviceId, projectId],
    queryFn: () => apiClient.getServiceDocuments(serviceId, projectId),
    enabled: !!serviceId,
  })
}

export function useCheckApplicability() {
  return useMutation({
    mutationFn: ({ serviceId, projectId }: { serviceId: string; projectId: string }) =>
      apiClient.checkApplicability(serviceId, projectId),
  })
}

export function useAddToChecklist() {
  return useMutation({
    mutationFn: ({ serviceId, projectId }: { serviceId: string; projectId: string }) =>
      apiClient.addToChecklist(serviceId, projectId),
  })
}

export function useStartChecklistApplication() {
  return useMutation({
    mutationFn: (approvalId: string) => apiClient.startChecklistApplication(approvalId),
  })
}

export function useAttachChecklistDocument() {
  return useMutation({
    mutationFn: ({ approvalId, documentId }: { approvalId: string; documentId: string }) =>
      apiClient.attachChecklistDocument(approvalId, documentId),
  })
}

export function useDetachChecklistDocument() {
  return useMutation({
    mutationFn: ({ approvalId, documentId }: { approvalId: string; documentId: string }) =>
      apiClient.detachChecklistDocument(approvalId, documentId),
  })
}

// ---- Applications --------------------------------------------------------
export function useApplications() {
  return useQuery({
    queryKey: ['applications'],
    queryFn: () => apiClient.listApplications(),
  })
}

export function useApplication(applicationId: string) {
  return useQuery({
    queryKey: ['application', applicationId],
    queryFn: () => apiClient.getApplication(applicationId),
    enabled: !!applicationId,
  })
}

export function useApplicationTransitions(applicationId: string) {
  return useQuery({
    queryKey: ['application-transitions', applicationId],
    queryFn: () => apiClient.getApplicationTransitions(applicationId),
    enabled: !!applicationId,
  })
}

export function useSlaStatus(applicationId: string) {
  return useQuery({
    queryKey: ['application-sla', applicationId],
    queryFn: () => apiClient.getSlaStatus(applicationId),
    enabled: !!applicationId,
  })
}

export function useTransitionApplication() {
  return useMutation({
    mutationFn: ({ applicationId, toStatus }: { applicationId: string; toStatus: string }) =>
      apiClient.transitionApplication(applicationId, toStatus),
  })
}

// ---- Officer review -------------------------------------------------------
export function useOfficerApplications(params?: Record<string, any>) {
  return useQuery({
    queryKey: ['officer-applications', params],
    queryFn: () => apiClient.officerListApplications(params),
  })
}

export function useOfficerApplication(applicationId: string) {
  return useQuery({
    queryKey: ['officer-application', applicationId],
    queryFn: () => apiClient.officerGetApplication(applicationId),
    enabled: !!applicationId,
  })
}

export function useOfficerTransition() {
  return useMutation({
    mutationFn: ({ applicationId, toStatus }: { applicationId: string; toStatus: string }) =>
      apiClient.officerTransitionApplication(applicationId, toStatus),
  })
}

export function useOfficerSync() {
  return useMutation({
    mutationFn: (applicationId: string) => apiClient.officerSyncApplication(applicationId),
  })
}
