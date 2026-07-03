import { useEffect, useState } from 'react'
import { api } from '../api'
import type { Tenant } from '../types'

interface Props {
  selected: Tenant | null
  onSelect: (t: Tenant) => void
}

export default function TenantSelector({ selected, onSelect }: Props) {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [error, setError] = useState('')

  const load = () => api.listTenants().then(setTenants).catch(() => {})

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    setError('')
    try {
      const t = await api.createTenant(name, slug)
      setTenants(prev => [t, ...prev])
      onSelect(t)
      setShowCreate(false)
      setName('')
      setSlug('')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create tenant')
    }
  }

  const autoSlug = (n: string) =>
    n.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

  return (
    <div className="relative flex items-center gap-3">
      <select
        className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        value={selected?.slug ?? ''}
        onChange={e => {
          const t = tenants.find(x => x.slug === e.target.value)
          if (t) onSelect(t)
        }}
      >
        <option value="" disabled>Select tenant…</option>
        {tenants.map(t => (
          <option key={t.id} value={t.slug}>{t.name}</option>
        ))}
      </select>

      <button
        onClick={() => setShowCreate(v => !v)}
        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
      >
        + New
      </button>

      {showCreate && (
        <div className="absolute top-9 right-0 z-20 bg-white border border-gray-200 rounded-xl shadow-lg p-4 w-72">
          <p className="text-sm font-semibold mb-3 text-gray-700">Create tenant</p>
          <input
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Name (e.g. Queen's University)"
            value={name}
            onChange={e => { setName(e.target.value); setSlug(autoSlug(e.target.value)) }}
          />
          <input
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Slug (e.g. queens-university)"
            value={slug}
            onChange={e => setSlug(e.target.value)}
          />
          {error && <p className="text-red-500 text-xs mb-2">{error}</p>}
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setShowCreate(false)}
              className="text-xs text-gray-500 hover:text-gray-700 px-3 py-1.5"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={!name || !slug}
              className="text-xs bg-indigo-600 text-white rounded-lg px-3 py-1.5 hover:bg-indigo-700 disabled:opacity-40"
            >
              Create
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
