import ReactMarkdown from 'react-markdown'
import QuizCard from './QuizCard.jsx'
import SourceCitations from './SourceCitations.jsx'

export default function ChatMessage({ msg }) {
  const isUser = msg.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        animation: 'fadeSlideIn 0.2s ease',
      }}
    >
      <div style={{
        maxWidth: isUser ? '70%' : '80%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
      }}>
        <div style={{
          padding: '12px 16px',
          borderRadius: isUser ? '12px 12px 0 12px' : '12px 12px 12px 0',
          background: isUser ? 'var(--primary)' : 'var(--white)',
          border: isUser ? 'none' : '1px solid var(--border)',
          color: isUser ? 'white' : 'var(--text-primary)',
          fontSize: 14,
          lineHeight: 1.6,
          boxShadow: 'var(--shadow-sm)',
        }}>
          {isUser ? (
            <span>{msg.content}</span>
          ) : (
            <>
              {msg.agent_name && (
                <div style={{
                  fontSize: 11, fontWeight: 600,
                  color: 'var(--primary)',
                  marginBottom: 8,
                  textTransform: 'uppercase',
                  letterSpacing: '0.6px',
                }}>
                  {msg.agent_name}
                </div>
              )}
              {msg.quiz_data ? (
                <QuizCard quizData={msg.quiz_data} />
              ) : (
                <div className="message-body">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              )}
            </>
          )}
        </div>

        {!isUser && (
          <div style={{ paddingLeft: 2 }}>
            <SourceCitations sources={msg.sources} />
            {msg.processing_time_ms != null && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>
                {msg.processing_time_ms.toFixed(0)} ms
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
