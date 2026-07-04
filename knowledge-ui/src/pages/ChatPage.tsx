import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import Chat from '../components/Chat'
import type { Tenant } from '../types'

type State = 'loading' | 'missing-token' | 'invalid-token' | 'not-found' | 'ready'

export default function ChatPage() {
  const { slug } = useParams<{ slug: string }>()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [state, setState] = useState<State>('loading')

  useEffect(() => {
    if (!slug) { setState('not-found'); return }
    if (!token) { setState('missing-token'); return }

    const validate = async () => {
      try {
        // Verify token first — if invalid, don't even reveal the tenant exists
        await api.verifyToken(slug, token)
        // Token valid — now load tenant details
        const t = await api.getTenant(slug)
        setTenant(t)
        setState('ready')
      } catch (e: unknown) {
        const status = (e as { status?: number }).status
        if (status === 401) setState('invalid-token')
        else setState('not-found')
      }
    }

    validate()
  }, [slug, token])

  if (state === 'loading') {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (state === 'missing-token') {
    return <AccessDenied title="Access token required" message="Please use the full link provided by your administrator." />
  }

  if (state === 'invalid-token') {
    return <AccessDenied title="Invalid access token" message="This link is invalid or has expired. Please contact your administrator for a new link." />
  }

  if (state === 'not-found') {
    return <AccessDenied title="Not found" message="This knowledge base does not exist." />
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3 shadow-sm">
        <span className="text-xl">🧠</span>
        <div>
          <span className="font-bold text-gray-800 text-lg">{tenant!.name}</span>
          <span className="ml-2 text-xs text-gray-400">Knowledge Assistant</span>
        </div>
      </header>
      <main className="flex-1 overflow-hidden">
        <Chat tenant={tenant!} />
      </main>
    </div>
  )
}

function AccessDenied({ title, message }: { title: string; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4 text-center bg-gray-50 px-6">
      <p className="text-5xl">🔒</p>
      <h1 className="text-xl font-bold text-gray-700">{title}</h1>
      <p className="text-gray-400 text-sm max-w-sm">{message}</p>
    </div>
  )
}
