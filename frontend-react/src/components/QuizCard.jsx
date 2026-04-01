import { useState } from 'react'

export default function QuizCard({ quizData }) {
  const questions = quizData?.questions ?? []
  if (!questions.length) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
        Quiz — {questions.length} Frage{questions.length !== 1 ? 'n' : ''}
      </div>
      {questions.map((q, i) => (
        <QuizQuestion key={i} question={q} index={i} />
      ))}
    </div>
  )
}

function QuizQuestion({ question, index }) {
  const [selected, setSelected] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const { question: text, options = [], correct = 0, explanation, source } = question
  const isCorrect = selected === correct

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 8,
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 14px',
        background: 'var(--bg-upload)',
        borderBottom: submitted ? '1px solid var(--border)' : 'none',
        fontSize: 13,
        fontWeight: 500,
        color: 'var(--text-primary)',
        lineHeight: 1.5,
      }}>
        <span style={{ color: 'var(--text-muted)', fontWeight: 400, marginRight: 6 }}>
          Frage {index + 1}
        </span>
        {text}
      </div>

      <div style={{ padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {options.map((opt, i) => {
          let bg = 'transparent'
          let border = '1px solid var(--border)'
          let color = 'var(--text-secondary)'

          if (submitted) {
            if (i === correct) {
              bg = '#F0FDF4'; border = '1px solid #86EFAC'; color = '#166534'
            } else if (i === selected && i !== correct) {
              bg = '#FEF2F2'; border = '1px solid #FECACA'; color = '#991B1B'
            }
          } else if (selected === i) {
            bg = 'var(--primary-light)'; border = '1px solid var(--primary)'; color = 'var(--primary)'
          }

          return (
            <button
              key={i}
              onClick={() => !submitted && setSelected(i)}
              disabled={submitted}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '8px 12px',
                borderRadius: 6,
                border,
                background: bg,
                color,
                fontSize: 13,
                cursor: submitted ? 'default' : 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <span style={{
                width: 20, height: 20, borderRadius: '50%',
                border: `2px solid ${selected === i && !submitted ? 'var(--primary)' : submitted && i === correct ? '#86EFAC' : 'currentColor'}`,
                flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 700,
              }}>
                {String.fromCharCode(65 + i)}
              </span>
              {opt}
            </button>
          )
        })}
      </div>

      {submitted && (
        <div style={{
          padding: '10px 14px',
          borderTop: '1px solid var(--border)',
          background: isCorrect ? '#F0FDF4' : '#FEF2F2',
        }}>
          <div style={{
            fontSize: 12, fontWeight: 600,
            color: isCorrect ? '#166534' : '#991B1B',
            marginBottom: explanation ? 4 : 0,
          }}>
            {isCorrect ? 'Richtig!' : `Falsch — Richtige Antwort: ${options[correct]}`}
          </div>
          {explanation && (
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              {explanation}
            </div>
          )}
          {source && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Quelle: {source}
            </div>
          )}
        </div>
      )}

      {!submitted && (
        <div style={{ padding: '0 14px 12px' }}>
          <button
            onClick={() => selected !== null && setSubmitted(true)}
            disabled={selected === null}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              border: 'none',
              background: selected !== null ? 'var(--primary)' : 'var(--border)',
              color: selected !== null ? 'white' : 'var(--text-muted)',
              fontSize: 12, fontWeight: 600,
              cursor: selected !== null ? 'pointer' : 'not-allowed',
              transition: 'background 0.15s ease',
            }}
          >
            Überprüfen
          </button>
        </div>
      )}
    </div>
  )
}
