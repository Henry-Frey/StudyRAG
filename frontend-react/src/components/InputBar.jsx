import { useState, useRef, useEffect } from 'react'

export default function InputBar({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [value])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const canSend = value.trim().length > 0 && !disabled

  return (
    <div style={{
      padding: '12px 24px 16px',
      borderTop: '1px solid var(--border)',
      background: 'var(--white)',
      flexShrink: 0,
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: 8,
        background: 'var(--white)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        padding: '6px 6px 6px 16px',
        boxShadow: 'var(--shadow-sm)',
        transition: 'border-color 0.15s ease',
      }}
        onFocusCapture={e => e.currentTarget.style.borderColor = 'var(--primary)'}
        onBlurCapture={e => e.currentTarget.style.borderColor = 'var(--border)'}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Stelle eine Frage zu deinen Vorlesungsmaterialien…"
          rows={1}
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            resize: 'none',
            fontSize: 13,
            color: 'var(--text-primary)',
            background: 'transparent',
            lineHeight: 1.5,
            padding: '4px 0',
            maxHeight: 120,
            overflowY: 'auto',
          }}
        />
        <button
          onClick={submit}
          disabled={!canSend}
          style={{
            width: 36, height: 36,
            borderRadius: 8,
            border: 'none',
            background: canSend ? 'var(--primary)' : 'var(--border)',
            color: 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: canSend ? 'pointer' : 'not-allowed',
            opacity: canSend ? 1 : 0.5,
            flexShrink: 0,
            transition: 'background 0.15s ease, opacity 0.15s ease, transform 0.1s ease',
          }}
          onMouseDown={e => canSend && (e.currentTarget.style.transform = 'scale(0.93)')}
          onMouseUp={e => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <SendIcon />
        </button>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
        Enter zum Senden · Shift+Enter für neue Zeile
      </div>
    </div>
  )
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}
