var capturedClient: any

jest.mock('axios', () => {
  const makeClient = () => ({
    post: jest.fn().mockResolvedValue({ data: {} }),
    get: jest.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    defaults: { headers: {} },
  })
  const create = jest.fn(() => {
    capturedClient = makeClient()
    return capturedClient
  })
  return { create }
})

jest.mock('@/lib/auth', () => ({
  getToken: jest.fn(() => null),
  clearSession: jest.fn(),
  setSession: jest.fn(),
}))

import { apiClient } from '@/services/api'

describe('API contract: project analyze', () => {
  beforeEach(() => {
    capturedClient.post.mockReset()
    capturedClient.post.mockResolvedValue({
      data: { project_id: 'p1', applicable_approvals: [], total_count: 0 },
    })
  })

  it('POSTs to the analyze endpoint and returns the response', async () => {
    const data = await apiClient.analyzeProject('p1')
    expect(capturedClient.post).toHaveBeenCalledWith('/projects/p1/analyze')
    expect(data.total_count).toBe(0)
  })
})

describe('API contract: application submit', () => {
  beforeEach(() => {
    capturedClient.post.mockReset()
    capturedClient.post.mockResolvedValue({ data: { application_id: 'a1', status: 'SUBMITTED' } })
  })

  it('POSTs to the submit endpoint without a request body (matches backend)', async () => {
    const data = await apiClient.submitApplication('a1')
    expect(capturedClient.post).toHaveBeenCalledWith('/applications/a1/submit')
    expect(data.status).toBe('SUBMITTED')
  })
})

describe('API contract: chat query', () => {
  beforeEach(() => {
    capturedClient.post.mockReset()
    capturedClient.post.mockResolvedValue({ data: { intent: 'general', answer: 'ok' } })
  })

  it('POSTs the copilot query with a `question` field (not `query`)', async () => {
    const data = await apiClient.queryRegulatoryCopilot('What do I need?', 'p1')
    expect(capturedClient.post).toHaveBeenCalledWith('/chat/query', {
      question: 'What do I need?',
      project_id: 'p1',
    })
    expect(data.answer).toBe('ok')
  })
})
