const EMPTY_STATE = {
  Erklärer: {
    title: 'Konzepte verstehen',
    description: 'Stellen Sie Fragen zu Ihren Vorlesungsmaterialien. Der Erklärer findet relevante Abschnitte und erklärt Konzepte mit Quellenangaben.',
    suggestions: ['Was ist RAG?', 'Erkläre Backpropagation', 'Transformer Architektur'],
    icon: <BrainIcon />,
  },
  Quizmaster: {
    title: 'Wissen testen',
    description: 'Generiert Multiple-Choice-Fragen aus Ihren Unterlagen zur gezielten Prüfungsvorbereitung.',
    suggestions: ['Quiz zu Kapitel 3', '10 Fragen zu ML', 'Karteikarten erstellen'],
    icon: <HelpCircleIcon />,
  },
  Vernetzer: {
    title: 'Themen verbinden',
    description: 'Findet Querverbindungen und Zusammenhänge zwischen Konzepten aus verschiedenen Vorlesungen.',
    suggestions: ['Wie hängen X und Y zusammen?', 'Vergleiche A mit B', 'Mindmap erstellen'],
    icon: <LinkIcon />,
  },
}

export default function EmptyState({ agent, onSuggestion }) {
  const state = EMPTY_STATE[agent] ?? EMPTY_STATE['Erklärer']

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      flex: 1,
      padding: 24,
      textAlign: 'center',
    }}>
      <div style={{
        width: 56, height: 56,
        borderRadius: 16,
        background: 'var(--primary-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 16,
        color: 'var(--primary)',
      }}>
        {state.icon}
      </div>

      <h2 style={{
        fontSize: 18,
        fontWeight: 700,
        color: 'var(--text-primary)',
        marginBottom: 8,
      }}>
        {state.title}
      </h2>

      <p style={{
        fontSize: 13,
        color: 'var(--text-muted)',
        maxWidth: 360,
        lineHeight: 1.6,
        marginBottom: 24,
      }}>
        {state.description}
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
        {state.suggestions.map(s => (
          <SuggestionChip key={s} text={s} onClick={() => onSuggestion(s)} />
        ))}
      </div>
    </div>
  )
}

function SuggestionChip({ text, onClick }) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        padding: '8px 14px',
        borderRadius: 20,
        border: `1px solid ${hovered ? 'var(--primary)' : 'var(--border)'}`,
        fontSize: 12,
        color: hovered ? 'var(--primary)' : 'var(--text-secondary)',
        background: hovered ? 'var(--primary-light)' : 'var(--white)',
        cursor: 'pointer',
        transition: 'all 0.15s ease',
      }}
    >
      {text}
    </button>
  )
}

import { useState } from 'react'

function BrainIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.07-4.57A3 3 0 0 1 4.5 9a2.99 2.99 0 0 1 .86-2.1A2.5 2.5 0 0 1 9.5 2Z" />
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.07-4.57A3 3 0 0 0 19.5 9a2.99 2.99 0 0 0-.86-2.1A2.5 2.5 0 0 0 14.5 2Z" />
    </svg>
  )
}
function HelpCircleIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
}
function LinkIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  )
}
