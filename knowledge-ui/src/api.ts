import type { AskResponse, Document, HistoryMessage, Tenant } from './types'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  listTenants: () => request<Tenant[]>('/api/v1/tenants'),

  getTenant: (slug: string) => request<Tenant>(`/api/v1/tenants/${slug}`),

  verifyToken: (slug: string, token: string) =>
    request<{ valid: boolean }>(`/api/v1/tenants/${slug}/verify-token?token=${encodeURIComponent(token)}`),

  createTenant: (name: string, slug: string) =>
    request<Tenant>('/api/v1/tenants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, slug }),
    }),

  listDocuments: (slug: string) =>
    request<{ items: Document[]; total: number }>(
      `/api/v1/tenants/${slug}/documents?size=50`
    ),

  uploadDocument: (slug: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<{ document_id: string; status: string; message: string }>(
      `/api/v1/tenants/${slug}/documents`,
      { method: 'POST', body: form }
    )
  },

  ask: (slug: string, question: string, history: HistoryMessage[] = [], topK = 5, minScore = 0.5) =>
    request<AskResponse>(`/api/v1/tenants/${slug}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history, top_k: topK, min_score: minScore }),
    }),
}
