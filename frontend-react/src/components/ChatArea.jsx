import { useRef, useEffect } from 'react'
import TopBar from './TopBar.jsx'
import EmptyState from './EmptyState.jsx'
import ChatMessage from './ChatMessage.jsx'
import InputBar from './InputBar.jsx'
import { chat } from '../api.js'
import { AGENTS } from '../App.jsx'

export default function ChatArea({
  messages, setMessages,
  selectedAgent, selectedCollection,
  onClearChat, onMenuOpen,
}) {
  const scrollRef = useRef(null)
  const isLoading = messages.length > 0 && messages[messages.length - 1]?.role === 'loading'

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  async function handleSend(text) {
    const agentInfo = AGENTS[selectedAgent] ?? AGENTS['Erklärer']

    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'loading', content: '' },
    ])

    try {
      const response = await chat(text, agentInfo.type, selectedCollection)
      setMessages(prev => [
        ...prev.slice(0, -1),
        {
          role: 'assistant',
          content: response.answer ?? '',
          agent_name: response.agent_name,
          agent_type: response.agent_type,
          sources: response.sources ?? [],
          quiz_data: response.quiz_data ?? null,
          processing_time_ms: response.processing_time_ms,
        },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', content: `Fehler: ${err.message}`, sources: [] },
      ])
    }
  }

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden',
      background: 'var(--bg-main)',
    }}>
      <TopBar
        agentName={selectedAgent}
        onClearChat={onClearChat}
        onMenuOpen={onMenuOpen}
      />

      {/* Messages or empty state */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: messages.length ? '24px' : 0,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {messages.length === 0 ? (
          <EmptyState agent={selectedAgent} onSuggestion={handleSend} />
        ) : (
          messages.map((msg, i) => (
            msg.role === 'loading'
              ? <LoadingBubble key={i} />
              : <ChatMessage key={i} msg={msg} />
          ))
        )}
      </div>

      <InputBar onSend={handleSend} disabled={isLoading} />

      <style>{fadeIn}</style>
    </div>
  )
}

function LoadingBubble() {
  return (
    <div style={{ display: 'flex', justifyContent: 'flex-start', animation: 'fadeSlideIn 0.2s ease' }}>
      <div style={{
        padding: '14px 18px',
        borderRadius: '12px 12px 12px 0',
        background: 'var(--white)',
        border: '1px solid var(--border)',
        display: 'flex', gap: 5, alignItems: 'center',
        boxShadow: 'var(--shadow-sm)',
      }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            width: 7, height: 7, borderRadius: '50%',
            background: 'var(--primary)',
            opacity: 0.6,
            animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }} />
        ))}
      </div>
      <style>{dotBounce}</style>
    </div>
  )
}

const fadeIn = `
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0);   }
}
`

const dotBounce = `
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}
`
