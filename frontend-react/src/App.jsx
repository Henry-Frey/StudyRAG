import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatArea from './components/ChatArea.jsx'
import { fetchHealth, fetchCollections } from './api.js'

export const AGENTS = {
  Erklärer:   { type: 'explainer', description: 'Konzepte erklären' },
  Quizmaster: { type: 'quiz',      description: 'Wissen testen'      },
  Vernetzer:  { type: 'connector', description: 'Themen verbinden'   },
}

export default function App() {
  const [messages, setMessages]               = useState([])
  const [selectedAgent, setSelectedAgent]     = useState('Erklärer')
  const [selectedCollection, setSelectedCollection] = useState(null)
  const [collections, setCollections]         = useState([])
  const [health, setHealth]                   = useState(null)
  const [sidebarOpen, setSidebarOpen]         = useState(false)

  const loadCollections = useCallback(async () => {
    try {
      const data = await fetchCollections()
      setCollections(data)
    } catch {
      setCollections([])
    }
  }, [])

  const loadHealth = useCallback(async () => {
    try {
      const data = await fetchHealth()
      setHealth(data)
    } catch {
      setHealth(null)
    }
  }, [])

  useEffect(() => {
    loadCollections()
    loadHealth()
    const interval = setInterval(() => {
      loadCollections()
      loadHealth()
    }, 15000)
    return () => clearInterval(interval)
  }, [loadCollections, loadHealth])

  function clearChat() {
    setMessages([])
  }

  function handleAgentChange(agent) {
    setSelectedAgent(agent)
  }

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      overflow: 'hidden',
      background: 'var(--bg-main)',
    }}>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          style={{
            position: 'fixed', inset: 0,
            background: 'rgba(0,0,0,0.3)',
            zIndex: 10,
            display: 'none',
          }}
          className="mobile-overlay"
        />
      )}

      <Sidebar
        selectedAgent={selectedAgent}
        onAgentChange={handleAgentChange}
        selectedCollection={selectedCollection}
        onCollectionChange={setSelectedCollection}
        collections={collections}
        health={health}
        onUploadComplete={loadCollections}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <ChatArea
        messages={messages}
        setMessages={setMessages}
        selectedAgent={selectedAgent}
        selectedCollection={selectedCollection}
        onClearChat={clearChat}
        onMenuOpen={() => setSidebarOpen(true)}
      />
    </div>
  )
}
