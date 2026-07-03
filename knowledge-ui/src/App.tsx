import { useState } from 'react'
import Chat from './components/Chat'
import Documents from './components/Documents'
import TenantSelector from './components/TenantSelector'
import type { Tenant } from './types'

type Tab = 'chat' | 'documents'

export default function App() {
  const [tenant, setTenant] = useState<Tenant | null>(null)
  const [tab, setTab] = useState<Tab>('chat')

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <span className="text-xl">🧠</span>
          <span className="font-bold text-gray-800 text-lg">KnowledgeAI</span>
        </div>
        <TenantSelector selected={tenant} onSelect={setTenant} />
      </header>

      {tenant ? (
        <>
          {/* Tabs */}
          <div className="bg-white border-b border-gray-200 px-6 flex gap-6">
            {(['chat', 'documents'] as Tab[]).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`py-3 text-sm font-medium border-b-2 transition-colors capitalize
                  ${tab === t
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'}`}
              >
                {t === 'chat' ? '💬 Chat' : '📄 Documents'}
              </button>
            ))}
          </div>

          {/* Content */}
          <main className="flex-1 overflow-hidden">
            {tab === 'chat'
              ? <Chat tenant={tenant} />
              : <Documents tenant={tenant} />
            }
          </main>
        </>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center">
          <p className="text-5xl">🧠</p>
          <h1 className="text-2xl font-bold text-gray-800">Welcome to KnowledgeAI</h1>
          <p className="text-gray-500 max-w-md">
            Select a tenant from the top right to start chatting with your documents,
            or create a new one.
          </p>
        </div>
      )}
    </div>
  )
}
