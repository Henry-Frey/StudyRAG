import AgentSelector from './AgentSelector.jsx'
import CollectionDropdown from './CollectionDropdown.jsx'
import UploadArea from './UploadArea.jsx'
import StatusBar from './StatusBar.jsx'

export default function Sidebar({
  selectedAgent, onAgentChange,
  selectedCollection, onCollectionChange,
  collections, health, onUploadComplete,
  isOpen, onClose,
}) {
  return (
    <>
      <aside style={{
        width: 260,
        flexShrink: 0,
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        zIndex: 20,
      }}>
        <div style={{ padding: '20px 16px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
            <div style={{
              width: 36, height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <BookIcon />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                StudyRAG
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.2, marginTop: 1 }}>
                KI-Lernassistent
              </div>
            </div>
          </div>

          <AgentSelector selected={selectedAgent} onChange={onAgentChange} />

          <div style={{ height: 20 }} />

          <CollectionDropdown
            collections={collections}
            selected={selectedCollection}
            onChange={onCollectionChange}
          />
        </div>

        <div style={{ flex: 1 }} />

        <div style={{ padding: '0 16px 16px' }}>
          <UploadArea
            collections={collections}
            onUploadComplete={onUploadComplete}
          />
          <StatusBar health={health} collections={collections} />
        </div>
      </aside>
    </>
  )
}

function BookIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  )
}
