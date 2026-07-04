import { useState } from 'react'
import AdminLogin from '../components/AdminLogin'
import Documents from '../components/Documents'
import TenantSelector from '../components/TenantSelector'
import type { Tenant } from '../types'

const ADMIN_TOKEN_KEY = 'knowledgeai_admin'

type SourceTab = 'files' | 'faq' | 'api'

export default function AdminPage() {
  const [authenticated, setAuthenticated] = useState(() => !!localStorage.getItem(ADMIN_TOKEN_KEY))
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [sourceTab, setSourceTab] = useState<SourceTab>('files')

  const logout = () => {
    localStorage.removeItem(ADMIN_TOKEN_KEY)
    setAuthenticated(false)
  }

  if (!authenticated) {
    return <AdminLogin onSuccess={() => {
      localStorage.setItem(ADMIN_TOKEN_KEY, '1')
      setAuthenticated(true)
    }} />
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-xl">🧠</span>
          <span className="font-bold text-gray-800 text-lg">KnowledgeAI</span>
          <span className="text-xs font-semibold bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">Admin</span>
        </div>
        <div className="flex items-center gap-4">
          <TenantSelector selected={tenant} onSelect={setTenant} />
          <button
            onClick={logout}
            className="text-xs text-gray-500 hover:text-red-600 font-medium transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      {tenant ? (
        <>
          {/* Share link banner */}
          <ShareLink tenant={tenant} />

          {/* Source type tabs */}
          <div className="bg-white border-b border-gray-200 px-6 flex gap-6">
            {[
              { id: 'files' as SourceTab, label: '📄 File Upload', available: true },
              { id: 'faq'   as SourceTab, label: '❓ FAQ Pages',    available: false },
              { id: 'api'   as SourceTab, label: '🔌 API / URL',    available: false },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => tab.available && setSourceTab(tab.id)}
                className={`py-3 text-sm font-medium border-b-2 transition-colors
                  ${!tab.available ? 'text-gray-300 border-transparent cursor-not-allowed' :
                    sourceTab === tab.id
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                {tab.label}
                {!tab.available && (
                  <span className="ml-1.5 text-[10px] bg-gray-100 text-gray-400 px-1.5 py-0.5 rounded-full font-normal">
                    coming soon
                  </span>
                )}
              </button>
            ))}
          </div>

          <main className="flex-1 overflow-hidden">
            {sourceTab === 'files' && <Documents tenant={tenant} />}
            {sourceTab === 'faq' && <ComingSoon type="FAQ Pages" description="Ingest FAQ pages by pasting a URL or uploading a CSV. Questions and answers are chunked and indexed automatically." />}
            {sourceTab === 'api' && <ComingSoon type="API / URL" description="Connect a REST API or website URL. The system will crawl, extract, and keep the content in sync." />}
          </main>
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
          <p className="text-5xl">🏢</p>
          <h1 className="text-xl font-bold text-gray-800">Select or create a tenant</h1>
          <p className="text-gray-500 text-sm max-w-sm">
            Each tenant has its own isolated knowledge base. Use the dropdown above to get started.
          </p>
        </div>
      )}
    </div>
  )
}

function ShareLink({ tenant }: { tenant: Tenant }) {
  const [copied, setCopied] = useState<'link' | 'token' | null>(null)

  const chatUrl = `${window.location.origin}/chat/${tenant.slug}?token=${tenant.access_token}`

  const copy = (type: 'link' | 'token') => {
    const text = type === 'link' ? chatUrl : tenant.access_token
    navigator.clipboard.writeText(text)
    setCopied(type)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="bg-indigo-50 border-b border-indigo-100 px-6 py-3 flex items-center gap-4 flex-wrap">
      <span className="text-xs font-semibold text-indigo-700 shrink-0">🔗 Client link</span>

      {/* URL */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <code className="text-xs bg-white border border-indigo-200 rounded-lg px-3 py-1.5 text-indigo-800 truncate flex-1">
          {chatUrl}
        </code>
        <button
          onClick={() => copy('link')}
          className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-3 py-1.5 shrink-0 transition-colors"
        >
          {copied === 'link' ? '✓ Copied' : 'Copy link'}
        </button>
      </div>

      {/* Token only */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xs text-indigo-500">Token:</span>
        <code className="text-xs bg-white border border-indigo-200 rounded-lg px-2 py-1.5 text-indigo-700 font-mono">
          {tenant.access_token}
        </code>
        <button
          onClick={() => copy('token')}
          className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
        >
          {copied === 'token' ? '✓' : 'Copy'}
        </button>
      </div>
    </div>
  )
}

function ComingSoon({ type, description }: { type: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8">
      <p className="text-5xl">🚧</p>
      <h2 className="text-lg font-bold text-gray-700">{type} — Coming Soon</h2>
      <p className="text-gray-400 text-sm max-w-md">{description}</p>
    </div>
  )
}
