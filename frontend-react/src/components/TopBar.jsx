export default function TopBar({ agentName, onClearChat, onMenuOpen }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '14px 24px',
      borderBottom: '1px solid var(--border)',
      background: 'var(--white)',
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <button
          onClick={onMenuOpen}
          className="mobile-menu-btn"
          style={{
            border: 'none',
            background: 'none',
            padding: 4,
            color: 'var(--text-muted)',
            display: 'none',
          }}
        >
          <MenuIcon />
        </button>
        <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
          {agentName}
        </span>
      </div>

      <button
        onClick={onClearChat}
        style={{
          fontSize: 12,
          color: 'var(--text-muted)',
          border: '1px solid var(--border)',
          borderRadius: 6,
          padding: '4px 12px',
          background: 'none',
          cursor: 'pointer',
          transition: 'color 0.15s, border-color 0.15s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.color = 'var(--text-secondary)'
          e.currentTarget.style.borderColor = 'var(--text-muted)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.color = 'var(--text-muted)'
          e.currentTarget.style.borderColor = 'var(--border)'
        }}
      >
        Chat leeren
      </button>
    </div>
  )
}

function MenuIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  )
}
