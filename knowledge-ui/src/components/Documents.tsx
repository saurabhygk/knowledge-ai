import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Document, Tenant } from '../types'

const STATUS_STYLE: Record<Document['status'], string> = {
  UPLOADED:   'bg-blue-100 text-blue-700',
  PROCESSING: 'bg-yellow-100 text-yellow-700',
  INDEXED:    'bg-green-100 text-green-700',
  FAILED:     'bg-red-100 text-red-700',
}

interface Props { tenant: Tenant }

export default function Documents({ tenant }: Props) {
  const [docs, setDocs] = useState<Document[]>([])
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const load = useCallback(() => {
    api.listDocuments(tenant.slug).then(r => setDocs(r.items)).catch(() => {})
  }, [tenant.slug])

  useEffect(() => {
    load()
    // poll while any doc is processing
    const id = setInterval(() => {
      setDocs(prev => {
        if (prev.some(d => d.status === 'UPLOADED' || d.status === 'PROCESSING')) load()
        return prev
      })
    }, 4000)
    return () => clearInterval(id)
  }, [load])

  const upload = async (file: File) => {
    setUploading(true)
    try {
      await api.uploadDocument(tenant.slug, file)
      load()
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) upload(file)
  }

  return (
    <div className="flex flex-col h-full gap-6 p-6">
      {/* Upload zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${dragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'}`}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = '' }}
        />
        {uploading
          ? <p className="text-indigo-600 font-medium animate-pulse">Uploading…</p>
          : <>
              <p className="text-3xl mb-2">📄</p>
              <p className="text-sm font-medium text-gray-600">Drop a file here or click to browse</p>
              <p className="text-xs text-gray-400 mt-1">PDF, DOCX, TXT and more</p>
            </>
        }
      </div>

      {/* Document list */}
      {docs.length === 0
        ? <p className="text-center text-gray-400 text-sm">No documents yet. Upload one above.</p>
        : (
          <div className="overflow-auto rounded-xl border border-gray-200 bg-white shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Filename</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Uploaded</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Indexed</th>
                </tr>
              </thead>
              <tbody>
                {docs.map(doc => (
                  <tr key={doc.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-800 max-w-xs truncate">{doc.filename}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ${STATUS_STYLE[doc.status]}`}>
                        {doc.status}
                      </span>
                      {doc.status === 'PROCESSING' && (
                        <span className="ml-2 inline-block w-3 h-3 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{new Date(doc.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-500">
                      {doc.indexed_at ? new Date(doc.indexed_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    </div>
  )
}
