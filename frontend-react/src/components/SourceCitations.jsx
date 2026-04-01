import { useState } from 'react'

export default function SourceCitations({ sources }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null

  return (
    <div style={{ marginTop: 10 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 5,
          fontSize: 11, fontWeight: 500,
          color: 'var(--primary)',
          background: 'var(--primary-light)',
          border: 'none',
          borderRadius: 4,
          padding: '3px 8px',
          cursor: 'pointer',
          transition: 'opacity 0.15s',
        }}
      >
        <BookOpenIcon />
        {sources.length} Quelle{sources.length !== 1 ? 'n' : ''}
        <ChevronIcon open={open} />
      </button>

      {open && (
        <div style={{
          marginTop: 8,
          display: 'flex', flexDirection: 'column', gap: 6,
        }}>
          {sources.map((src, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '7px 10px',
              background: 'var(--bg-main)',
              border: '1px solid var(--border)',
              borderRadius: 6,
            }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {src.lecture_title || src.file_name || 'Unbekannt'}
                </div>
                {src.file_name && src.lecture_title && (
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{src.file_name}</div>
                )}
              </div>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexShrink: 0, marginLeft: 12 }}>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  S. {src.page_number ?? '?'}
                </span>
                <span style={{
                  fontSize: 11, fontWeight: 500,
                  color: 'var(--text-secondary)',
                  fontVariantNumeric: 'tabular-nums',
                }}>
                  {typeof src.relevance_score === 'number' ? src.relevance_score.toFixed(3) : '—'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function BookOpenIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  )
}

function ChevronIcon({ open }) {
  return (
    <svg
      width="10" height="10"
      viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  )
}
