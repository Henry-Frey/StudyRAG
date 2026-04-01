import { AGENTS } from '../App.jsx'

const AGENT_ICONS = {
  Erklärer:   <BrainIcon />,
  Quizmaster: <HelpCircleIcon />,
  Vernetzer:  <LinkIcon />,
}

export default function AgentSelector({ selected, onChange }) {
  return (
    <div>
      <div style={labelStyle}>AGENT</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {Object.entries(AGENTS).map(([name, info]) => {
          const active = selected === name
          return (
            <button
              key={name}
              onClick={() => onChange(name)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '9px 11px',
                borderRadius: 8,
                border: 'none',
                background: active ? 'var(--primary-light)' : 'transparent',
                color: active ? 'var(--primary)' : 'var(--text-secondary)',
                fontWeight: active ? 600 : 400,
                cursor: 'pointer',
                textAlign: 'left',
                width: '100%',
                transition: 'background 0.15s ease, color 0.15s ease',
              }}
            >
              <span style={{ flexShrink: 0, opacity: active ? 1 : 0.7 }}>
                {AGENT_ICONS[name]}
              </span>
              <div>
                <div style={{ fontSize: 13, lineHeight: 1.3 }}>{name}</div>
                <div style={{
                  fontSize: 11,
                  color: active ? 'var(--primary)' : 'var(--text-muted)',
                  fontWeight: 400,
                  lineHeight: 1.3,
                  opacity: active ? 0.8 : 1,
                }}>
                  {info.description}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

const labelStyle = {
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: '0.8px',
  color: 'var(--text-muted)',
  textTransform: 'uppercase',
  marginBottom: 6,
}

function BrainIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.07-4.57A3 3 0 0 1 4.5 9a2.99 2.99 0 0 1 .86-2.1A2.5 2.5 0 0 1 9.5 2Z" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.07-4.57A3 3 0 0 0 19.5 9a2.99 2.99 0 0 0-.86-2.1A2.5 2.5 0 0 0 14.5 2Z" />
    </svg>
  )
}

function HelpCircleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
}

function LinkIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  )
}
