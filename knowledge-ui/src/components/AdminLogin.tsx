import { useState } from 'react'

const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD ?? 'admin'

interface Props {
  onSuccess: () => void
}

export default function AdminLogin({ onSuccess }: Props) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (password === ADMIN_PASSWORD) {
      onSuccess()
    } else {
      setError('Incorrect password')
      setPassword('')
    }
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <form
        onSubmit={submit}
        className="bg-white border border-gray-200 rounded-2xl shadow-sm p-8 w-full max-w-sm flex flex-col gap-5"
      >
        <div className="flex flex-col items-center gap-2 mb-2">
          <span className="text-4xl">🧠</span>
          <h1 className="text-xl font-bold text-gray-800">Admin Login</h1>
          <p className="text-xs text-gray-400">KnowledgeAI Administration</p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-gray-600">Password</label>
          <input
            type="password"
            value={password}
            onChange={e => { setPassword(e.target.value); setError('') }}
            placeholder="Enter admin password"
            autoFocus
            className="border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          {error && <p className="text-red-500 text-xs">{error}</p>}
        </div>

        <button
          type="submit"
          disabled={!password}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl py-2.5 text-sm font-medium transition-colors"
        >
          Sign in
        </button>

        <p className="text-center text-xs text-gray-400">
          Set <code className="bg-gray-100 px-1 rounded">VITE_ADMIN_PASSWORD</code> in{' '}
          <code className="bg-gray-100 px-1 rounded">knowledge-ui/.env</code>
        </p>
      </form>
    </div>
  )
}
