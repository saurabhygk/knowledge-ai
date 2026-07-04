export interface Tenant {
  id: string
  name: string
  slug: string
  access_token: string
  created_at: string
}

export interface Document {
  id: string
  tenant_id: string
  filename: string
  content_type: string | null
  status: 'UPLOADED' | 'PROCESSING' | 'INDEXED' | 'FAILED'
  metadata: Record<string, unknown>
  error_message: string | null
  created_at: string
  indexed_at: string | null
}

export interface SearchResult {
  chunk_text: string
  score: number
  document_id: string
  filename: string
  chunk_index: number
  metadata: Record<string, unknown>
}

export interface AskResponse {
  question: string
  answer: string
  sources: SearchResult[]
  llm_provider: string
}

export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface Message {
  role: 'user' | 'bot'
  text: string
  sources?: SearchResult[]
  llm_provider?: string
  error?: boolean
  escalate?: boolean  // renders escalation card instead of a text bubble
}
