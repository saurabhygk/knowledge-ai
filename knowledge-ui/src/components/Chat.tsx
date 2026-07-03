import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import type { Message, Tenant } from '../types'

interface Props { tenant: Tenant }


function BotMessage({ msg }: { msg: Message }) {
  return (
    <div className="flex flex-col gap-1 max-w-[80%]">
      <div className={`px-4 py-3 rounded-2xl rounded-tl-sm text-sm leading-relaxed shadow-sm
        ${msg.error ? 'bg-red-50 text-red-700' : 'bg-white border border-gray-200 text-gray-800'}`}>
        {msg.text}
      </div>
    </div>
  )
}

export default function Chat({ tenant }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'bot', text: `Hi! I'm ready to answer questions about ${tenant.name}'s documents. Ask me anything.` }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Reset chat when tenant changes
  useEffect(() => {
    setMessages([{ role: 'bot', text: `Hi! I'm ready to answer questions about ${tenant.name}'s documents. Ask me anything.` }])
  }, [tenant.slug])

  const send = async () => {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await api.ask(tenant.slug, q)
      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.answer,
        sources: res.sources,
        llm_provider: res.llm_provider,
      }])
    } catch (e: unknown) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: e instanceof Error ? e.message : 'Something went wrong.',
        error: true,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
        {messages.map((msg, i) => (
          msg.role === 'user'
            ? (
              <div key={i} className="flex justify-end">
                <div className="bg-indigo-600 text-white px-4 py-3 rounded-2xl rounded-tr-sm text-sm max-w-[75%] shadow-sm leading-relaxed">
                  {msg.text}
                </div>
              </div>
            )
            : (
              <div key={i} className="flex justify-start">
                <BotMessage msg={msg} />
              </div>
            )
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex gap-1.5 items-center">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-4 py-3 flex gap-3 items-end">
        <textarea
          rows={1}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="Ask a question about your documents…"
          className="flex-1 resize-none border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 max-h-32 leading-relaxed"
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl px-4 py-2.5 text-sm font-medium transition-colors shrink-0"
        >
          Send
        </button>
      </div>
    </div>
  )
}
